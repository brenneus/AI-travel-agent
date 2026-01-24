import asyncio
from typing import List, Optional
from langchain_core.tools import tool
from playwright.async_api import async_playwright
from src.config import Config
from src.state import FlightOption

@tool
async def search_flights(origin: str, destination: str, date: str) -> List[FlightOption]:
    """
    Search for flights using a browser automation agent.
    
    IMPORTANT: Arguments 'origin' and 'destination' MUST be the 3-letter IATA airport code.
    If the user provides a city name (e.g., "New York"), YOU (the agent) must convert it 
    to the appropriate code (e.g., "JFK", "LGA", or "NYC" for all airports) before calling this tool.
    
    Args:
        origin (str): 3-letter IATA airport code (e.g., "JFK", "LHR", "NRT")
        destination (str): 3-letter IATA airport code
        date (str): Date of travel in YYYY-MM-DD format
    """
    print(f"✈️  Searching flights: {origin} -> {destination} on {date}...")
    
    flights = []
    
    async with async_playwright() as p:
        # 1. Launch Browser with "Human" settings
        # We disable the "AutomationControlled" flag so Google doesn't see us as a bot immediately.
        browser = await p.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # 2. Create a "Context" (Like a fresh incognito window)
        # We inject the User Agent here to look like a real Mac user.
        context = await browser.new_context(
            user_agent=Config.USER_AGENT,
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        
        try:
            # 3. Navigate to Google Flights
            # Strategy: We construct the URL directly. This is much faster and less prone to breaking
            # than trying to find the "From" and "To" text boxes and typing in them.
            url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{date}"
            
            print(f"   Navigating to: {url}")
            await page.goto(url, timeout=Config.TIMEOUT)
            
            # 4. Wait for the "Results" to appear
            # We don't use 'time.sleep()'. We wait for the specific 'div[role="main"]' element 
            # to appear, which tells us the flight list has actually loaded.
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=10000)
            
            # --- SCRAPING LOGIC (Placeholder) ---
            print("   (Page loaded. Returning mock data for connection test...)")
            
            # MOCK DATA:
            # We create a valid FlightOption object.
            # This proves that our Pydantic model in state.py accepts the data correctly.
            mock_flight = FlightOption(
                airline="Demo Air",
                flight_number="DA101",
                departure_city=origin,
                arrival_city=destination,
                departure_time="10:00 AM",
                arrival_time="2:00 PM",
                price=350.00,
                booking_link=page.url
            )
            flights.append(mock_flight)
            
        except Exception as e:
            print(f"❌ Error scraping flights: {e}")
            # SNAPSHOT: If it crashes, we take a picture.
            # This is saved to the 'logs/' folder so you can see exactly what the bot saw.
            await page.screenshot(path="logs/flight_error.png")
            
        finally:
            # Always close the browser to free up memory
            await browser.close()
            
    return flights