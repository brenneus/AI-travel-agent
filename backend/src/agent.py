import operator
import asyncio
from typing import Annotated, List, Literal, Union

# 1. Load Environment Variables
from dotenv import load_dotenv
load_dotenv() 

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 2. Import Custom Components
from src.state import AgentState
from src.tools.flight_search import search_outbound_flights, search_return_flights, generate_booking_link
from src.config import Config

# ------------------------------------------------------------------
# 3. SETUP THE BRAIN
# ------------------------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model=Config.MODEL_NAME, 
    temperature=0, 
    max_retries=2,
)

tools = [search_outbound_flights, search_return_flights, generate_booking_link]
llm_with_tools = llm.bind_tools(tools)

# ------------------------------------------------------------------
# 4. DEFINE THE "ARCHITECT" SYSTEM PROMPT
# ------------------------------------------------------------------

SYSTEM_PROMPT = """You are an intelligent Flight Planning Agent.
Your goal is to plan a complete round-trip itinerary for the user.
Remember the current year is 2026. 

**PHASE 1: CLARIFICATION (The "Pre-Flight Check")**
Before searching, you must ensure you have precise data.
Analyze the user's request for these keys. If any are missing or vague, ASK.

1.  **Dates**: Exact Depart and Return dates (e.g., "2026-02-12" and "2026-02-16").
2.  **Airports:** * Convert cities to Airport Codes (e.g., "New York" -> JFK, LGA, or EWR).
    * *CRITICAL:* If a city has multiple airports (NY, London, DC, Tokyo, etc.), ASK the user if they have a preference or if "Any" is okay. 
3.  **Stops:** (Non-stop vs. Any)
4.  **Airline:** (Specific vs. No preference)
5.  **Timing:** (Morning/Afternoon/Night vs. Anytime)
6.  **Budget:** (Max price, "Cheapest Option", or "No limit")

**PHASE 2: AUTONOMOUS EXECUTION (Strict Tool usage)**
Once you have the data, execute the workflow without stopping.

**Step 1: Search Outbound**
* Call `search_outbound_flights`.
* **FORMATTING RULES:**
    * `origin`: Use the IATA code (e.g., "JFK").
    * `destination`: Use the IATA code (e.g., "LHR").
    * `depart_date`: Convert "next friday" etc. to `YYYY-MM-DD` format.
    * `return_date`: Convert "following monday" etc. to `YYYY-MM-DD` format.

**Step 2: Autonomous Selection**
* Review the results from Step 1.
* **Apply Budget Logic:**
    * If "Max Price" is set: DISCARD any flight over the limit. If no flights remain, let the user know and ask to adjust their budget.
    * If "Cheapest Option": Non-stop > Price, but the cheapest non-stop flight wins. If no non-stop flights, pick the cheapest overall. 
    * If "No limit": Prioritize Non-stop > Airline Preference > Price
* Pick the **single best flight** matching the User's Phase 1 preferences.
* Make sure to note the `booking_link` from this flight for Step 3.

**Step 3: Search Return (The Handshake)**
* Call `search_return_flights`.
* **CRITICAL:** You must pass the EXACT values from the flight selected in Step 2:
    * `search_url`: Must be the `booking_link` from the chosen outbound flight.
    * `outbound_airline`: Exact airline name.
    * `outbound_departure_time`: Exact string (e.g. "12:59 PM").
    * `outbound_arrival_time`: Exact string.
    * `outbound_price`: Exact float (e.g., 813.0).
    * `outbound_stops`: Exact string (e.g., "Nonstop").

**Step 4: Autonomous Return Selection**
* Review the results from Step 3.
* **Apply Budget Logic:**
    * If "Max Price" is set: DISCARD any flight over the limit. If no flights remain, let the user know and ask to adjust their budget.
    * If "Cheapest Option": Non-stop > Price, but the cheapest non-stop flight wins. If no non-stop flights, pick the cheapest overall. 
    * If "No limit": Prioritize Non-stop > Airline Preference > Price
* Pick the **single best return flight** matching the User's Phase 1 preferences.
* Make sure to note the `booking_link` from this flight for Step 5.

**Step 5: Generate Booking Link (The Final Lock)**
* Review the results from Step 3 and select the best return flight.
* Call `generate_booking_link`.
* **CRITICAL:** Pass the EXACT values from the chosen return flight:
    * `search_url`: The `booking_link` returned in Step 3.
    * `return_airline`: Exact airline name.
    * `return_departure_time`: Exact string.
    * `return_arrival_time`: Exact string.
    * `return_price`: Exact float.
    * `return_stops`: Exact string.

**Step 6: Final Output**
* Present the final itinerary to the user.
* **You MUST include the 'Deep Link' returned by Step 5.**
* Example: "I have booked your trip! Outbound: Delta ($200). Return: Delta ($200). [Click Here to Book](<Deep_Link_URL>)"
"""

# ------------------------------------------------------------------
# 5. DEFINE THE NODES (FIXED: NOW ASYNC)
# ------------------------------------------------------------------

async def chatbot_node(state: AgentState):
    """
    The central node. It looks at the conversation history and decides what to do next.
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    result = await llm_with_tools.ainvoke(messages)
    
    return {"messages": [result]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"

# ------------------------------------------------------------------
# 6. BUILD THE GRAPH
# ------------------------------------------------------------------

def create_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", chatbot_node)
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()

compiled_graph = create_agent()

# ------------------------------------------------------------------
# 7. RUNNER (CLI MODE)
# ------------------------------------------------------------------

async def main():
    print(f"🤖 Flight Architect Initialized. Type 'q' to quit.")
    
    chat_history = []
    
    while True:
        user_input = input("\n👤 User: ")
        if user_input.lower() in ["q", "quit"]: break
        
        chat_history.append(HumanMessage(content=user_input))
        
        initial_state = {
            "messages": chat_history,
        }
        
        print("   (Thinking...)")
        
        try:
            async for event in compiled_graph.astream(initial_state, stream_mode="values"):
                
                if "messages" in event:
                    last_msg = event["messages"][-1]
                    
                    # LOGGING
                    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                        print(f"   ⚙️  Action: {last_msg.tool_calls[0]['name']}")
                        print(f"       Args: {last_msg.tool_calls[0]['args']}")
                    
                    elif last_msg.type == "tool":
                        print(f"   ✅ Tool Data Received.")
                    
                    elif isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
                        content = last_msg.content
                        final_text = ""
                        
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and "text" in block:
                                    final_text += block["text"]
                        else:
                            final_text = str(content)
                            
                        print(f"🤖 Agent: {final_text}")
                        chat_history = event["messages"]
                        
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())