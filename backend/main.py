import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from src.agent import compiled_graph

app = FastAPI(title="Flight Architect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_session"

@app.get("/health")
def health_check():
    return {"status": "online", "agent": "ready"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    
    # We define an async generator function inside the endpoint
    async def event_generator():
        try:
            user_msg = HumanMessage(content=request.message)
            initial_state = {"messages": [user_msg]}
            config = {"configurable": {"thread_id": request.thread_id}}
            
            # This is the exact same loop from your CLI!
            async for event in compiled_graph.astream(initial_state, config, stream_mode="values"):
                if "messages" in event:
                    last_msg = event["messages"][-1]
                    
                    # 1. Catch Tool Calls (The "Thinking" phase)
                    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                        tool_name = last_msg.tool_calls[0]["name"]
                        
                        # Format the data as a JSON string prefixed with "data: "
                        payload = json.dumps({"type": "tool", "content": f"Running {tool_name}..."})
                        yield f"data: {payload}\n\n"
                    
                    # 2. Catch the Final Agent Response
                    elif isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
                        content = last_msg.content
                        final_text = ""
                        
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and "text" in block:
                                    final_text += block["text"]
                        else:
                            final_text = str(content)
                        
                        if final_text: # Only send if it's not empty
                            payload = json.dumps({"type": "message", "content": final_text})
                            yield f"data: {payload}\n\n"
                            
        except Exception as e:
            error_payload = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {error_payload}\n\n"

    # Return the generator as a StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")