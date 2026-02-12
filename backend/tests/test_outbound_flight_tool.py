import asyncio
import sys
import os

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.flight_search import search_outbound_flights
from src.config import Config

# Force browser to show up so you can watch it
Config.HEADLESS = False

async def run_test():
    print("🧪 Starting OUTBOUND Flight Search Test (Fast Scrape)...")
    
    # Run Tool 1 with BOTH dates
    results = await search_outbound_flights.ainvoke({
        "origin": "JFK", 
        "destination": "SRQ", 
        "depart_date": "2026-02-12",
        "return_date": "2026-02-16"
    })
    
    print(f"\n✅ Test Complete! Scraper returned {len(results)} outbound options.")
    
    output_filename = "tests/outbound_search_test.txt"
    
    if results:
        print(f"   📝 Writing detailed report to {output_filename}...")
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("--- OUTBOUND SEARCH RESULTS: JFK -> SRQ ---\n")
            f.write(f"Query: 2026-02-12 returning 2026-02-16\n")
            f.write(f"Total Options Found: {len(results)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, flight in enumerate(results, 1):
                f.write(f"OPTION #{i}\n")
                f.write(f"   ✈️  Airline:     {flight.airline}\n")
                f.write(f"   💰 Est. Price:  ${flight.price}\n")
                f.write(f"   ⏰ Depart:      {flight.departure_time}\n")
                f.write(f"   🛬 Arrive:      {flight.arrival_time}\n")
                f.write(f"   ⏱️  Duration:    {flight.duration}\n")
                f.write(f"   🛑 Stops:       {flight.stops}\n")
                f.write(f"   🔗 Search URL:  {flight.booking_link}\n") 
                f.write("-" * 60 + "\n")
                
        print(f"   ✅ Done! Open '{output_filename}' to verify the data.")
    else:
        print("   ⚠️  No flights found. Check the browser window for errors.")

if __name__ == "__main__":
    asyncio.run(run_test())