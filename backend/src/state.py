import operator
from typing import Annotated, List, TypedDict, Optional, Union
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel

# ------------------------------------------------------------------
# 1. ATOMIC DATA MODELS
# ------------------------------------------------------------------
class FlightOption(BaseModel):
    """
    Represents a single flight option.
    Used for both search results and saving the user's selection.
    """
    airline: str
    flight_number: str
    departure_city: str
    arrival_city: str
    departure_time: str
    arrival_time: str
    price: float
    duration: str   
    stops: str      
    booking_link: Optional[str] = None

# ------------------------------------------------------------------
# 2. THE AGENT STATE
# ------------------------------------------------------------------
class AgentState(TypedDict):
    """
    The 'Memory' of the agent.
    """
    # The Chat History (The stream of conversation)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # The "Pinned" Memories (Explicitly saving choices)
    # We use Optional because at the start of the chat, these are None.
    selected_outbound_flight: Optional[FlightOption]
    selected_return_flight: Optional[FlightOption]
    
    # Optional: Track if we are done
    is_booked: Optional[bool]