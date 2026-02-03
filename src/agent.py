import operator
from typing import Annotated, List, Literal, Union

# 1. Load Environment Variables (API Key)
from dotenv import load_dotenv
load_dotenv() 

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 2. Import Custom Components
from src.state import AgentState
from src.tools.flight_search import search_outbound_flights, search_return_flights
from src.config import Config

# ------------------------------------------------------------------
# 3. SETUP THE BRAIN
# ------------------------------------------------------------------

# We use the model name defined in your Config file (gemini-3-flash-preview)
# Ensure GOOGLE_API_KEY is in your .env file
llm = ChatGoogleGenerativeAI(
    model=Config.MODEL_NAME, 
    temperature=0,       # 0 is strictly required for accurate tool inputs
    max_retries=2,
)

# Bind our "Surgical Tools" to the LLM
tools = [search_outbound_flights, search_return_flights]
llm_with_tools = llm.bind_tools(tools)

# ------------------------------------------------------------------
# 4. DEFINE THE SYSTEM PROMPT
# ------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert Flight Booking Agent. 
Your goal is to help the user plan a round-trip flight.

Follow this STRICT workflow:
1.  **Search Outbound:** Use `search_outbound_flights` first.
2.  **Present Options:** List the airlines, times, and prices found. ASK the user to pick one.
3.  **Wait for Selection:** Do NOT guess. Wait for the user to say "I want Option 2" or "The JetBlue one".
4.  **Search Return:** Once the user picks an outbound flight, use `search_return_flights`. 
    * You MUST extract the `search_url`, `airline`, `departure_time`, `arrival_time`, and `price` from the selected option to call this tool correctly.
5.  **Finalize:** Present the matching return flights.

**CRITICAL RULES:**
* Never make up flights. Only use data from the tools.
* If you cannot find the return flight (tool returns empty), ask the user to pick a different outbound flight.
"""

# ------------------------------------------------------------------
# 5. DEFINE THE NODES
# ------------------------------------------------------------------

def chatbot_node(state: AgentState):
    """
    The central node. It looks at the conversation history and decides what to do next.
    """
    # We prepend the System Prompt to the history every time so the agent never forgets its role
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    result = llm_with_tools.invoke(messages)
    return {"messages": [result]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Decides the next step based on the LLM's last message.
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM wants to use a tool, route there
    if last_message.tool_calls:
        return "tools"
    
    # Otherwise, stop and wait for the user
    return "__end__"

# ------------------------------------------------------------------
# 6. BUILD THE GRAPH
# ------------------------------------------------------------------

def create_agent():
    workflow = StateGraph(AgentState)

    # A. Add Nodes
    workflow.add_node("agent", chatbot_node)
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)

    # B. Define Edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    return workflow.compile()

# ------------------------------------------------------------------
# 7. RUNNER (Test Loop)
# ------------------------------------------------------------------

if __name__ == "__main__":
    print(f"🤖 Flight Agent Initialized ({Config.MODEL_NAME}). Type 'q' to quit.")
    
    agent = create_agent()
    chat_history = []
    
    while True:
        user_input = input("\n👤 User: ")
        if user_input.lower() in ["q", "quit"]: break
        
        # Add user message to history
        chat_history.append(HumanMessage(content=user_input))
        
        initial_state = {
            "messages": chat_history,
            "origin": "JFK", 
            "destination": "LHR"
        }
        
        print("   (Thinking...)")
        
        # Stream events
        try:
            events = agent.stream(initial_state, stream_mode="values")
            
            for event in events:
                if "messages" in event:
                    last_msg = event["messages"][-1]
                    
                    # Visual Logging
                    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                        print(f"   ⚙️  AI Calling Tool: {last_msg.tool_calls[0]['name']}")
                    elif last_msg.type == "tool":
                        print(f"   ✅ Tool Result Received")
                    elif isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
                        print(f"🤖 Agent: {last_msg.content}")
                        # Update history so the agent remembers the conversation
                        chat_history = event["messages"]
                        
        except Exception as e:
            print(f"❌ Error: {e}")
            print("   (Check your .env file or API Quota)")