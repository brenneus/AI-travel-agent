import asyncio
import re
from typing import List, Set
from langchain_core.tools import tool
from playwright.async_api import async_playwright, Page, Locator
from src.config import Config
from src.state import FlightOption

COMMON_AIRLINES = [
    "Delta", "United", "American", "JetBlue", "Southwest", 
    "Spirit", "Frontier", "Alaska", "British Airways", "Virgin Atlantic", 
    "Air France", "Lufthansa", "Emirates", "Qatar", "Singapore Airlines"
]

async def _extract_card_data(card: Locator) -> dict:
    """
    Shared Helper: Extracts text, price, airline, and times from a flight card.
    """
    try:
        text = await card.text_content(timeout=500)
    except:
        return None

    if not text or "$" not in text: return None
    
    # 1. Airline
    airline = "Unknown"
    for name in COMMON_AIRLINES:
        if name in text:
            airline = name
            break
    if airline == "Unknown":
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines: airline = lines[0]
    
    # 2. Price
    price = 0.0
    price_match = re.search(r'\$([\d,]+)', text)
    if price_match:
        try:
            price = float(price_match.group(1).replace(',', ''))
        except: pass
        
    # 3. Times
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
# TOOL 1: FAST OUTBOUND SEARCH (No Clicking)
# ------------------------------------------------------------------
@tool
async def search_outbound_flights(origin: str, destination: str, depart_date: str, return_date: str) -> List[FlightOption]:
    """
    Step 1: Search for OUTBOUND flights. 
    Returns ALL unique flight options found on the first page.
    """
    print(f"✈️  Tool 1: Fast Scrape {origin} -> {destination} ({depart_date} to {return_date})")
    
    search_query = f"Flights from {origin} to {destination} on {depart_date} returning {return_date}"
    url = f"https://www.google.com/travel/flights?q={search_query.replace(' ', '+')}"

    results = []
    seen_ids: Set[str] = set() # <--- DEDUPLICATION TRACKER
    
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
            
            cards = await page.locator('div[role="main"] li').all()
            
            for card in cards:
                data = await _extract_card_data(card)
                if not data: continue
                
                # Create a unique fingerprint for this flight
                # Key: Airline + Departure Time + Price
                unique_key = f"{data['airline']}-{data['dep_time']}-{data['price']}"
                
                if unique_key in seen_ids:
                    continue # Skip duplicate
                
                seen_ids.add(unique_key)
                
                flight = FlightOption(
                    airline=data['airline'],
                    flight_number="N/A",
                    departure_city=origin,
                    arrival_city=destination,
                    departure_time=data['dep_time'],
                    arrival_time=data['arr_time'],
                    price=data['price'],
                    booking_link=page.url 
                )
                results.append(flight)
                
        except Exception as e:
            print(f"❌ Error in Outbound Search: {e}")
        finally:
            await browser.close()
            
    print(f"✅ Found {len(results)} unique outbound options.")
    return results

# ------------------------------------------------------------------
# TOOL 2: SMART RETURN SEARCH (Locate & Click)
# ------------------------------------------------------------------
@tool
async def search_return_flights(search_url: str, outbound_airline: str, outbound_time: str) -> List[FlightOption]:
    """
    Step 2: Search for RETURN flights.
    """
    print(f"✈️  Tool 2: Re-locating flight '{outbound_airline}' at {outbound_time}...")
    
    results = []
    seen_ids: Set[str] = set() # <--- DEDUPLICATION TRACKER
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            # 1. Load the General Search URL
            await page.goto(search_url, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            # 2. FIND the previously selected flight
            cards = await page.locator('div[role="main"] li').all()
            
            target_card = None
            for card in cards:
                text = await card.text_content()
                if not text: continue
                
                if outbound_airline in text and outbound_time in text:
                    target_card = card
                    break
            
            if not target_card:
                print(f"❌ Could not find the selected flight ({outbound_airline} @ {outbound_time}) on the page.")
                return []
            
            # 3. CLICK IT
            print("   ✅ Found matching outbound flight. Clicking...")
            await target_card.click()
            await page.wait_for_timeout(3000)
            
            # 4. Scrape Returns
            return_cards = await page.locator('div[role="main"] li').all()
            
            for card in return_cards:
                data = await _extract_card_data(card)
                if not data: continue
                
                # Unique Key for Return Flight
                unique_key = f"{data['airline']}-{data['dep_time']}-{data['price']}"
                
                if unique_key in seen_ids:
                    continue
                seen_ids.add(unique_key)
                
                flight = FlightOption(
                    airline=data['airline'],
                    flight_number="N/A",
                    departure_city="Dest", 
                    arrival_city="Origin",
                    departure_time=data['dep_time'],
                    arrival_time=data['arr_time'],
                    price=data['price'], 
                    booking_link=page.url 
                )
                results.append(flight)
                
        except Exception as e:
            print(f"❌ Error in Return Search: {e}")
        finally:
            await browser.close()
            
    print(f"✅ Found {len(results)} unique return options.")
    return results