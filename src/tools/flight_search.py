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
    """
    Aggressively normalizes text for comparison.
    Removes standard spaces, non-breaking spaces (\u00a0), and narrow spaces (\u202f).
    """
    if not text: return ""
    return text.lower().replace(" ", "").replace("\u00a0", "").replace("\u202f", "").strip()

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
# TOOL 2: SMART RETURN SEARCH (Robust Match)
# ------------------------------------------------------------------
@tool
async def search_return_flights(search_url: str, outbound_airline: str, outbound_departure_time: str, outbound_arrival_time: str, outbound_price: float) -> List[FlightOption]:
    """
    Step 2: Search for RETURN flights.
    Requires strict matching of the selected outbound flight to ensure accuracy.
    """
    print(f"✈️  Tool 2: Re-locating {outbound_airline} ({outbound_departure_time} - {outbound_arrival_time}) for ${outbound_price}...")
    
    results = []
    seen_ids: Set[str] = set()
    
    # Normalize inputs for robust comparison
    target_airline = normalize_text(outbound_airline)
    target_dep = normalize_text(outbound_departure_time)
    target_arr = normalize_text(outbound_arrival_time)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=Config.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(user_agent=Config.USER_AGENT)
        page = await context.new_page()
        
        try:
            await page.goto(search_url, timeout=Config.TIMEOUT)
            await page.wait_for_selector('div[role="main"]', state="visible", timeout=15000)
            
            cards = await page.locator('div[role="main"] li').all()
            print(f"   (Scanning {len(cards)} visible cards for match...)")
            
            target_card = None
            
            for i, card in enumerate(cards):
                data = await _extract_card_data(card)
                if not data: continue
                
                # --- ROBUST MATCHING ---
                card_airline = normalize_text(data['airline'])
                card_dep = normalize_text(data['dep_time'])
                card_arr = normalize_text(data['arr_time'])
                
                # Check 1: Airline (Check if target is substring of card, e.g. "jetblue" in "jetblueairways")
                airline_match = (target_airline in card_airline) or (card_airline in target_airline)
                
                # Check 2: Times
                time_match = (target_dep == card_dep) and (target_arr == card_arr)
                
                # Check 3: Price (Allow $1.0 tolerance for float rounding)
                price_match = abs(data['price'] - outbound_price) < 2.0
                
                # Debug Print for first 5 cards to see what we are comparing
                if i < 5: 
                    print(f"   🔎 Checking Card #{i+1}: {data['airline']} {data['dep_time']} ${data['price']} | Match? A:{airline_match} T:{time_match} P:{price_match}")

                if airline_match and time_match and price_match:
                    target_card = card
                    print(f"   🎯 MATCH FOUND on Card #{i+1}!")
                    break
            
            if not target_card:
                print(f"❌ Critical: Could not re-locate the flight. Check the debug logs above.")
                return []
            
            # 3. CLICK IT
            await target_card.click()
            await page.wait_for_timeout(3000)
            
            # 4. Scrape Returns
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