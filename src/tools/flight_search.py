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

async def _extract_flight_info(card: Locator) -> dict:
    """
    Helper to extract raw text, airline, and times from a card.
    """
    text = await card.text_content()
    if not text: return None
    
    # 1. Airline
    airline = "Unknown Airline"
    for name in COMMON_AIRLINES:
        if name in text:
            airline = name
            break
    if airline == "Unknown Airline":
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines: airline = lines[0]

    # 2. Times (Find all occurrences of "10:00 AM")
    time_matches = re.findall(r'(\d{1,2}:\d{2}\s?[AP]M)', text)
    dep_time = "Unknown"
    arr_time = "Unknown"
    
    if len(time_matches) >= 2:
        dep_time = time_matches[0]
        arr_time = time_matches[-1] 
        
    return {
        "text": text,
        "airline": airline,
        "dep_time": dep_time,
        "arr_time": arr_time
    }

async def _scrape_google_flights(page: Page, origin: str, destination: str, depart_date: str, return_date: str) -> List[FlightOption]:
    print(f"   🔎 Deep Search: Checking combinations for {origin} <-> {destination}...")
    
    search_query = f"Flights from {origin} to {destination} on {depart_date} returning {return_date}"
    url = f"https://www.google.com/travel/flights?q={search_query.replace(' ', '+')}"
    
    results = []
    
    # --- DEDUPLICATION SET ---
    # We will store strings like "Delta-$700-10:00AM-5:00PM" here
    seen_flights: Set[str] = set()

    MAX_OUTBOUND_CHECKS = 3
    
    for i in range(MAX_OUTBOUND_CHECKS):
        print(f"      ⟳ Iteration {i+1}/{MAX_OUTBOUND_CHECKS}: Processing Outbound Option #{i+1}...")
        
        try:
            # 1. LOAD PAGE
            await page.goto(url, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            # 2. FIND OUTBOUND CARDS
            outbound_cards = await page.locator('div[role="main"] li').all()
            
            valid_cards = []
            for card in outbound_cards:
                if "$" in await card.text_content():
                    valid_cards.append(card)
            
            if i >= len(valid_cards): break
                
            outbound_card = valid_cards[i]
            out_info = await _extract_flight_info(outbound_card)
            if not out_info: continue

            # 3. CLICK
            await outbound_card.click()
            await page.wait_for_timeout(3000)
            
            # 4. FIND RETURN CARDS
            return_cards = await page.locator('div[role="main"] li').all()
            
            # We take the top 1 return flight for this outbound
            for ret_card in return_cards:
                ret_info = await _extract_flight_info(ret_card)
                if not ret_info or "$" not in ret_info['text']: continue
                
                # Extract Price
                price = 0.0
                price_match = re.search(r'\$([\d,]+)', ret_info['text'])
                if price_match:
                    try:
                        price = float(price_match.group(1).replace(',', ''))
                    except: pass
                
                # Create the unique ID for deduplication
                # We check Price + Schedule to determine uniqueness
                unique_id = f"{price}-{out_info['dep_time']}-{ret_info['dep_time']}"
                
                if unique_id in seen_flights:
                    print(f"      Duplicate found (skipping): {unique_id}")
                    continue
                
                # Add to set so we don't add it again
                seen_flights.add(unique_id)
                
                # 5. BUILD ITINERARY
                flight = FlightOption(
                    airline=f"{out_info['airline']} (Out) / {ret_info['airline']} (Ret)",
                    flight_number="N/A", 
                    departure_city=origin,
                    arrival_city=destination,
                    departure_time=f"OUT: {out_info['dep_time']} - {out_info['arr_time']}",
                    arrival_time=f"RET: {ret_info['dep_time']} - {ret_info['arr_time']}",
                    price=price,
                    booking_link=page.url 
                )
                results.append(flight)
                break # Move to next outbound iteration after finding the best return
                
        except Exception as e:
            print(f"      ⚠️ Error in iteration {i}: {e}")
            continue
            
    return results

@tool
async def search_flights(origin: str, destination: str, depart_date: str, return_date: str) -> List[FlightOption]:
    """
    Search for ROUND TRIP flights.
    """
    print(f"✈️  Manager: Starting Deep Search {origin} <-> {destination}")
    
    all_flights = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            scrapers = [_scrape_google_flights]
            for scraper_func in scrapers:
                flights = await scraper_func(page, origin, destination, depart_date, return_date)
                all_flights.extend(flights)
                
        except Exception as e:
            print(f"❌ Critical Error in Search Tool: {e}")
            await page.screenshot(path="logs/error_screenshot.png")
            
        finally:
            await browser.close()
            
    print(f"✅ Found {len(all_flights)} unique itineraries.")
    return all_flights