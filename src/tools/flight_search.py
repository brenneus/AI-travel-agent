import asyncio
import re
from typing import List
from langchain_core.tools import tool
from playwright.async_api import async_playwright, Page, Locator
from src.config import Config
from src.state import FlightOption

# Common airlines for entity extraction
COMMON_AIRLINES = [
    "Delta", "United", "American", "JetBlue", "Southwest", 
    "Spirit", "Frontier", "Alaska", "British Airways", "Virgin Atlantic", 
    "Air France", "Lufthansa", "Emirates", "Qatar", "Singapore Airlines"
]

async def _extract_card_data(card: Locator) -> dict:
    """
    Shared Helper: Extracts text, price, airline, and times from a flight card.
    Returns a dictionary of raw values used to build the FlightOption object.
    """
    text = await card.text_content()
    if not text or "$" not in text: return None
    
    # 1. Airline Extraction
    airline = "Unknown"
    for name in COMMON_AIRLINES:
        if name in text:
            airline = name
            break
    if airline == "Unknown":
        # Fallback: take the first non-empty line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines: airline = lines[0]
    
    # 2. Price Extraction
    price = 0.0
    price_match = re.search(r'\$([\d,]+)', text)
    if price_match:
        try:
            price = float(price_match.group(1).replace(',', ''))
        except: pass
        
    # 3. Time Extraction (Looks for patterns like 10:00 AM)
    time_matches = re.findall(r'(\d{1,2}:\d{2}\s?[AP]M)', text)
    dep_time = time_matches[0] if time_matches else "Unknown"
    arr_time = time_matches[-1] if len(time_matches) > 1 else "Unknown"
    
    return {
        "airline": airline,
        "price": price,
        "dep_time": dep_time,
        "arr_time": arr_time
    }

# ------------------------------------------------------------------
# TOOL 1: OUTBOUND SEARCH 
# ------------------------------------------------------------------
@tool
async def search_outbound_flights(origin: str, destination: str, depart_date: str) -> List[FlightOption]:
    """
    Step 1: Search for OUTBOUND flights.
    Returns a list of FlightOption objects.
    
    IMPORTANT: The 'booking_link' field of these objects contains the SESSION URL.
    The Agent MUST save this link to find the matching return flight later.
    """
    print(f"✈️  Tool 1: Searching Outbound {origin} -> {destination} on {depart_date}")
    
    # Construct URL: We use "roundtrip" so Google prepares the session for a return flight
    # We leave the return date open so the user can pick it in step 2
    query = f"Flights from {origin} to {destination} on {depart_date} roundtrip"
    url = f"https://www.google.com/travel/flights?q=Flights%20to%20{query.replace(' ', '%20')}"

    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            # We process the top 3 options to generate valid Session URLs
            for i in range(3): 
                # Re-query DOM elements on every loop to avoid stale handles
                cards = await page.locator('div[role="main"] li').all()
                valid_cards = [c for c in cards if "$" in await c.text_content()]
                
                if i >= len(valid_cards): break
                card = valid_cards[i]
                
                # 1. Extract Data
                data = await _extract_card_data(card)
                if not data: continue
                
                # 2. CLICK flight to generate Session URL
                await card.click()
                
                # Wait for URL update (This locks in the outbound flight)
                await page.wait_for_timeout(2000)
                session_url = page.url 
                
                # 3. Create FlightOption Object
                flight = FlightOption(
                    airline=data['airline'],
                    flight_number="N/A", # Hard to scrape without clicking details
                    departure_city=origin,
                    arrival_city=destination,
                    departure_time=data['dep_time'],
                    arrival_time=data['arr_time'],
                    price=data['price'],
                    booking_link=session_url # <--- CRITICAL: Storing the Session State here
                )
                results.append(flight)
                
                # 4. Reset: Go back to list to process the next option
                await page.go_back()
                await page.wait_for_selector('div[role="main"]', state="visible")
                
        except Exception as e:
            print(f"❌ Error in Outbound Search: {e}")
            await page.screenshot(path="logs/outbound_error.png")
        finally:
            await browser.close()
            
    print(f"✅ Found {len(results)} outbound options.")
    return results

# ------------------------------------------------------------------
# TOOL 2: RETURN SEARCH (Consumer)
# ------------------------------------------------------------------
@tool
async def search_return_flights(outbound_booking_link: str) -> List[FlightOption]:
    """
    Step 2: Search for RETURN flights.
    
    Args:
        outbound_booking_link: The 'booking_link' string from the FlightOption 
                               selected in Step 1.
    """
    print(f"✈️  Tool 2: Searching Return Flights via Link...")
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            # 1. Restore Session
            # This loads the page exactly where the user left off (Outbound locked in)
            await page.goto(outbound_booking_link, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            # 2. Scrape Return Options
            cards = await page.locator('div[role="main"] li').all()
            
            count = 0
            for card in cards:
                if count >= 5: break
                
                data = await _extract_card_data(card)
                if not data: continue
                
                # Create FlightOption for the Return Leg
                flight = FlightOption(
                    airline=data['airline'],
                    flight_number="N/A",
                    departure_city="Dest", # We could infer this from context, but keeping generic for now
                    arrival_city="Origin",
                    departure_time=data['dep_time'],
                    arrival_time=data['arr_time'],
                    price=data['price'], # This is usually the TOTAL trip price (bundle)
                    booking_link=outbound_booking_link # This link is valid for booking the pair
                )
                results.append(flight)
                count += 1
                
        except Exception as e:
            print(f"❌ Error in Return Search: {e}")
            await page.screenshot(path="logs/return_error.png")
        finally:
            await browser.close()
            
    print(f"✅ Found {len(results)} return options.")
    return results