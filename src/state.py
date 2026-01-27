import operator
from typing import Annotated, List, Optional, TypedDict
from pydantic import BaseModel, Field

# ATOMIC DATA MODELS (The "Things" we are looking for)

# For this agent, we have three types of items: Flights, Hotels, and Excursions.
# Each is defined as a Pydantic model for easy validation and serialization.

class FlightOption(BaseModel):
    airline: str
    flight_number: str
    departure_city: str
    arrival_city: str
    departure_time: str
    arrival_time: str
    price: float
    currency: str = "USD"
    booking_link: Optional[str] = None  

class HotelOption(BaseModel):
    hotel_name: str
    location: str
    check_in: str
    check_out: str
    price_per_night: float
    total_price: float
    rating: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    booking_link: Optional[str] = None

class ExcursionOption(BaseModel):
    activity_name: str
    location: str
    date: str
    price: float
    description: Optional[str] = None
    booking_link: Optional[str] = None

# THE AGENT STATE (The "data" passed between nodes)
# This TypedDict defines exactly what the Agent is allowed to remember.

class AgentState(TypedDict):
    # SECTION A: User Inputs - These are set at the start and generally don't change.
    origin: str
    destination: str
    start_date: str
    end_date: str
    budget_total: float
    preferences: str  

    # SECTION B: Research Results - These are populated as the agent gathers information.
    flight_options: Annotated[List[FlightOption], operator.add]
    hotel_options: Annotated[List[HotelOption], operator.add]
    excursion_options: Annotated[List[ExcursionOption], operator.add]

    # SECTION C: The Final Selection - The specific items the user has agreed to book.
    selected_outbound_flight: Optional[FlightOption]
    selected_return_flight: Optional[FlightOption]
    
    selected_hotel: Optional[HotelOption]
    
    selected_excursions: List[ExcursionOption]
    
    # SECTION D: System Status - Tracks the conversation and booking progress.
    messages: Annotated[List[str], operator.add] # Chat history
    is_booked: bool