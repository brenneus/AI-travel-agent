import asyncio
import sys
import os

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.flight_search import search_return_flights
from src.config import Config

# Force browser to show up so you can watch the "Click" happen
Config.HEADLESS = False

async def run_return_test():
    print("🧪 Starting RETURN Flight Search Test (Strict Match)...")
    print("   Goal: Find and Click the exact 'JetBlue' flight using 4 data points.")

    # --- MOCK INPUTS (Matching your Option #2) ---
    mock_search_url = " https://www.google.com/travel/flights?q=Flights+from+JFK+to+SRQ+on+2026-02-12+returning+2026-02-16"
    # These must match Option #2 EXACTLY
    mock_airline = "JetBlue"
    mock_dep_time = "4:52 PM" 
    mock_arr_time = "8:07 PM"
    mock_price = 653.0

    print(f"   🎯 Target Fingerprint:")
    print(f"      - Airline: {mock_airline}")
    print(f"      - Depart:  {mock_dep_time}")
    print(f"      - Arrive:  {mock_arr_time}")
    print(f"      - Price:   ${mock_price}")
    
    # Run Tool 2
    results = await search_return_flights.ainvoke({
        "search_url": mock_search_url,
        "outbound_airline": mock_airline,
        "outbound_departure_time": mock_dep_time,
        "outbound_arrival_time": mock_arr_time,
        "outbound_price": mock_price
    })
    
    print(f"\n✅ Test Complete! Scraper returned {len(results)} return options.")
    
    output_filename = "tests/return_search_test.txt"
    
    if results:
        print(f"   📝 Writing detailed report to {output_filename}...")
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(f"--- RETURN SEARCH RESULTS ---\n")
            f.write(f"Based on Outbound: {mock_airline} ({mock_dep_time} - {mock_arr_time})\n")
            f.write(f"Total Options Found: {len(results)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, flight in enumerate(results, 1):
                f.write(f"RETURN OPTION #{i}\n")
                f.write(f"   ✈️  Airline:     {flight.airline}\n")
                f.write(f"   💰 Total Price: ${flight.price}\n")
                f.write(f"   ⏰ Depart:      {flight.departure_time}\n")
                f.write(f"   🛬 Arrive:      {flight.arrival_time}\n")
                f.write(f"   🔗 Booking URL: {flight.booking_link}\n")
                f.write("-" * 60 + "\n")
                
        print(f"   ✅ Done! Open '{output_filename}' to verify the return options.")
    else:
        print("   ⚠️  No return flights found. The strict matching likely failed to find the card.")

if __name__ == "__main__":
    asyncio.run(run_return_test())