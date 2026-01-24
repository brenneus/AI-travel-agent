import asyncio
import sys
import os

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.flight_search import search_flights
from src.config import Config

# Force browser to show up
Config.HEADLESS = False

async def run_test():
    print("🧪 Starting Connection Test...")
    
    # --- THE FIX IS HERE ---
    # 1. Use .ainvoke() instead of calling it like a function
    # 2. Pass arguments as a Dictionary (JSON style)
    results = await search_flights.ainvoke({
        "origin": "JFK", 
        "destination": "LHR", 
        "date": "2025-10-15"
    })
    
    print(f"\n✅ Test Complete! Scraper returned {len(results)} flight(s).")
    print(f"   Sample Data: {results[0]}")

if __name__ == "__main__":
    asyncio.run(run_test())