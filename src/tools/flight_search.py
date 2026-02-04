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

def normalize_text(text: str) -> str:
    if not text: return ""
    return text.lower().replace(" ", "").replace("\u00a0", "").replace("\u202f", "").strip()

async def _extract_card_data(card: Locator) -> dict:
    """
    Extracts text, price, airline, times, duration, and stops from a flight card.
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

    # 4. Duration
    duration = "Unknown"
    duration_match = re.search(r'(\d+\s*hr\s*\d*\s*min|\d+\s*hr)', text)
    if duration_match:
        duration = duration_match.group(0)
    
    # 5. Stops
    stops = "Unknown"
    if "nonstop" in text.lower():
        stops = "Nonstop"
    else:
        stops_match = re.search(r'(\d+)\s*stop', text.lower())
        if stops_match:
            stops = f"{stops_match.group(1)} Stop(s)"
        else:
            stops = "Unknown" 
    
    return {
        "airline": airline,
        "price": price,
        "dep_time": dep_time,
        "arr_time": arr_time,
        "duration": duration,
        "stops": stops
    }

# ------------------------------------------------------------------
# TOOL 1: FAST OUTBOUND SEARCH
# ------------------------------------------------------------------
@tool
async def search_outbound_flights(origin: str, destination: str, depart_date: str, return_date: str) -> List[FlightOption]:
    """
    Step 1: Search for OUTBOUND flights. Returns ALL unique flight options.
    """
    print(f"✈️  Tool 1: Fast Scrape {origin} -> {destination}")
    
    search_query = f"Flights from {origin} to {destination} on {depart_date} returning {return_date}"
    url = f"https://www.google.com/travel/flights?q={search_query.replace(' ', '+')}"

    results = []
    seen_ids: Set[str] = set() 
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=Config.HEADLESS, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            cards = await page.locator('div[role="main"] li').all()
            
            for card in cards:
                data = await _extract_card_data(card)
                if not data: continue
                
                unique_key = f"{data['airline']}-{data['dep_time']}-{data['price']}"
                if unique_key in seen_ids: continue
                seen_ids.add(unique_key)
                
                flight = FlightOption(
                    airline=data['airline'],
                    flight_number="N/A",
                    departure_city=origin,
                    arrival_city=destination,
                    departure_time=data['dep_time'],
                    arrival_time=data['arr_time'],
                    duration=data['duration'],
                    stops=data['stops'],
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
# TOOL 2: SMART RETURN SEARCH (Reverted to < $2.0 tolerance)
# ------------------------------------------------------------------
@tool
async def search_return_flights(
    search_url: str, 
    outbound_airline: str, 
    outbound_departure_time: str, 
    outbound_arrival_time: str, 
    outbound_price: float,
    outbound_stops: str
) -> List[FlightOption]:
    """
    Step 2: Search for RETURN flights. Requires strict matching of the outbound flight.
    """
    print(f"✈️  Tool 2: Re-locating Outbound Flight (Strict Match)...")
    
    results = []
    seen_ids: Set[str] = set()
    
    target_airline = normalize_text(outbound_airline)
    target_dep = normalize_text(outbound_departure_time)
    target_arr = normalize_text(outbound_arrival_time)
    target_stops = normalize_text(outbound_stops)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=Config.HEADLESS, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            await page.goto(search_url, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            # --- RE-SELECT OUTBOUND ---
            cards = await page.locator('div[role="main"] li').all()
            target_card = None
            
            for card in cards:
                data = await _extract_card_data(card)
                if not data: continue
                
                card_airline = normalize_text(data['airline'])
                card_dep = normalize_text(data['dep_time'])
                card_arr = normalize_text(data['arr_time'])
                card_stops = normalize_text(data['stops'])
                
                airline_match = (target_airline in card_airline) or (card_airline in target_airline)
                time_match = (target_dep == card_dep) and (target_arr == card_arr)
                stops_match = (target_stops == card_stops)
                # REVERTED: Strict tolerance
                price_match = abs(data['price'] - outbound_price) < 2.0 

                if airline_match and time_match and stops_match and price_match:
                    target_card = card
                    break
            
            if not target_card:
                print(f"❌ Critical: Could not re-locate outbound flight.")
                return []
            
            await target_card.click()
            await page.wait_for_timeout(3000)
            
            # --- SCRAPE RETURNS ---
            return_cards = await page.locator('div[role="main"] li').all()
            
            for card in return_cards:
                data = await _extract_card_data(card)
                if not data: continue
                
                unique_key = f"{data['airline']}-{data['dep_time']}-{data['price']}"
                if unique_key in seen_ids: continue
                seen_ids.add(unique_key)
                
                flight = FlightOption(
                    airline=data['airline'],
                    flight_number="N/A",
                    departure_city="Dest", 
                    arrival_city="Origin",
                    departure_time=data['dep_time'],
                    arrival_time=data['arr_time'],
                    duration=data['duration'], 
                    stops=data['stops'],     
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

# ------------------------------------------------------------------
# TOOL 3: FINAL BOOKING LINK (Reverted to < $2.0 tolerance)
# ------------------------------------------------------------------
@tool
async def generate_booking_link(
    search_url: str, 
    return_airline: str, 
    return_departure_time: str, 
    return_arrival_time: str, 
    return_price: float,
    return_stops: str
) -> str:
    """
    Step 3: FINAL STEP. Selects the return flight using STRICT MATCHING and extracts the final booking URL.
    """
    print(f"✈️  Tool 3: Generating Final Booking Link (Strict Match)...")
    
    target_airline = normalize_text(return_airline)
    target_dep = normalize_text(return_departure_time)
    target_arr = normalize_text(return_arrival_time)
    target_stops = normalize_text(return_stops)
    
    final_url = "Error: Could not generate link"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=Config.HEADLESS, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            # 1. Go to the page where Outbound is already selected
            await page.goto(search_url, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            # 2. Find the Return Flight
            cards = await page.locator('div[role="main"] li').all()
            target_card = None
            
            for card in cards:
                data = await _extract_card_data(card)
                if not data: continue
                
                # Card Fingerprint
                card_airline = normalize_text(data['airline'])
                card_dep = normalize_text(data['dep_time'])
                card_arr = normalize_text(data['arr_time'])
                card_stops = normalize_text(data['stops'])
                
                # Matching Logic
                airline_match = (target_airline in card_airline) or (card_airline in target_airline)
                time_match = (target_dep == card_dep) and (target_arr == card_arr)
                stops_match = (target_stops == card_stops)
                price_match = abs(data['price'] - return_price) < 2.0
                
                if airline_match and time_match and stops_match and price_match:
                    target_card = card
                    print(f"   🎯 RETURN MATCH FOUND: {data['airline']} {data['dep_time']}")
                    break
            
            if target_card:
                await target_card.click()
                await page.wait_for_timeout(5000) 
                final_url = page.url
                print(f"✅ SUCCESS! Final Deep Link Generated.")
            else:
                print("❌ Could not find the selected return flight to click.")
                
        except Exception as e:
            print(f"❌ Error generating link: {e}")
        finally:
            await browser.close()

    return final_url