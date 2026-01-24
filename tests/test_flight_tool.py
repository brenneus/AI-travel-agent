import asyncio
import sys
import os

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.flight_search import search_flights
from src.config import Config

# Force browser to show up so you can watch it
Config.HEADLESS = False

async def run_test():
    print("🧪 Starting Round-Trip Flight Search Test (Deep Search)...")
    print("   Please wait, this will take ~20 seconds as it clicks through options.")
    
    # Run the tool (simulating the Agent's call)
    results = await search_flights.ainvoke({
        "origin": "JFK", 
        "destination": "SRQ", 
        "depart_date": "2026-02-12",
        "return_date": "2026-02-16"
    })
    
    print(f"\n✅ Test Complete! Scraper returned {len(results)} complete itineraries.")
    
    # Save to 'tests/' folder to keep root clean
    output_filename = "tests/flight_search_test.txt"
    
    if results:
        print(f"   📝 Writing detailed report to {output_filename}...")
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("--- DEEP SEARCH RESULTS: JFK -> SRQ ---\n")
            f.write(f"Query Dates: 2026-02-12 to 2026-02-16\n")
            f.write(f"Total Itineraries Found: {len(results)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, flight in enumerate(results, 1):
                f.write(f"ITINERARY #{i}\n")
                f.write(f"   ✈️  Airlines:    {flight.airline}\n")
                f.write(f"   💰 Total Price: ${flight.price}\n")
                f.write(f"   📅 Schedule:\n")
                f.write(f"       • {flight.departure_time}\n") # Will print "OUT: 10:00 AM - 1:00 PM"
                f.write(f"       • {flight.arrival_time}\n")   # Will print "RET: 5:00 PM - 8:00 PM"
                f.write(f"   🔗 Deep Link:   {flight.booking_link}\n")
                f.write("-" * 60 + "\n")
                
        print(f"   ✅ Done! Open '{output_filename}' to verify the Outbound/Return pairs.")
    else:
        print("   ⚠️  No flights found. Check browser window for errors.")

if __name__ == "__main__":
    asyncio.run(run_test())