import requests
import json
import sys

def test_streaming_chat():
    url = "http://localhost:8000/chat"
    
    # The payload matching your Pydantic ChatRequest model
    payload = {
        "message": "Find me a flight from JFK to Sarasota from March 10 to March 16 on a direct flight. I don't have a preference for airline, timing, or budget.",
        "thread_id": "test_cli_001"
    }

    print(f"📡 Sending request to {url}...\n")

    try:
        # The stream=True argument is the magic key for SSE
        with requests.post(url, json=payload, stream=True) as response:
            # Check if the server rejected the request (e.g., 404 or 500 error)
            response.raise_for_status()

            # Iterate over the stream chunk by chunk as it arrives
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    
                    # SSE formats data lines starting with "data: "
                    if decoded_line.startswith("data: "):
                        # Strip off "data: " to get the raw JSON string
                        json_str = decoded_line[6:] 
                        
                        try:
                            data = json.loads(json_str)
                            
                            # Route the output based on the type we defined in main.py
                            if data.get("type") == "tool":
                                print(f"⚙️  [THINKING]: {data.get('content')}")
                            elif data.get("type") == "message":
                                print(f"🤖 [AGENT]: {data.get('content')}")
                            elif data.get("type") == "error":
                                print(f"❌ [ERROR]: {data.get('content')}")
                                
                        except json.JSONDecodeError:
                            print(f"⚠️ [RAW]: {json_str}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect. Is your Uvicorn server running?")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    test_streaming_chat()