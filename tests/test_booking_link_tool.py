import asyncio
import sys
import os

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.flight_search import generate_booking_link
from src.config import Config

# Force browser to show up so you can watch the final click
Config.HEADLESS = False

async def run_booking_link_test():
    print("🧪 Starting FINAL BOOKING LINK Test (Strict Match)...")
    print("   Goal: Go to the 'Return Selection' page, click the specific return flight, and grab the deep link.")

    # --- MOCK INPUTS (From your RETURN OPTION #1 data) ---
    mock_search_url = "https://www.google.com/travel/flights/search?tfs=CBwQAho_EgoyMDI2LTAyLTEyIh8KA0pGSxIKMjAyNi0wMi0xMhoDU1JRKgJCNjIDNDYzagcIARIDSkZLcgcIARIDU1JRGh4SCjIwMjYtMDItMTZqBwgBEgNTUlFyBwgBEgNKRktAAUgBcAGCAQsI____________AZgBAQ&tfu=CmxDalJJZEROS2FIWlhiMWRNTWpCQlFWaGhSVkZDUnkwdExTMHRMUzB0TFMxMmQzZGpPRUZCUVVGQlIyMUVlbEUwU1cxRk9VMUJFZ1ZDTmpRMk14b0xDSXY3QkJBQ0dnTlZVMFE0SFhDTCt3UT0SAggAIgMKATA" 
    
    mock_return_airline = "JetBlue"
    mock_return_dep_time = "8:59 PM"
    mock_return_arr_time = "11:48 PM"  
    mock_return_price = 813.0
    mock_return_stops = "Nonstop"     

    print(f"   🎯 Target Return Flight:")
    print(f"      - URL:     {mock_search_url}")
    print(f"      - Airline: {mock_return_airline}")
    print(f"      - Depart:  {mock_return_dep_time}")
    print(f"      - Arrive:  {mock_return_arr_time}")
    print(f"      - Price:   ${mock_return_price}")
    print(f"      - Stops:   {mock_return_stops}")
    
    # Run Tool 3 with ALL strict parameters
    final_link = await generate_booking_link.ainvoke({
        "search_url": mock_search_url,
        "return_airline": mock_return_airline,
        "return_departure_time": mock_return_dep_time,
        "return_arrival_time": mock_return_arr_time, # NEW
        "return_price": mock_return_price,
        "return_stops": mock_return_stops            # NEW
    })
    
    print("\n==================================================")
    print("🎉 TEST RESULT:")
    
    if "http" in final_link and "Error" not in final_link:
        print(f"✅ SUCCESS! Final Deep Link Generated:")
        print(f"{final_link}")
        print("\n(Copy-paste the link above into your browser. It should show the 'Review Trip' page with BOTH flights.)")
        
        # Optional: Save to file
        with open("tests/booking_link_result.txt", "w", encoding="utf-8") as f:
            f.write(f"--- FINAL DEEP LINK ---\n")
            f.write(f"Target: {mock_return_airline} at {mock_return_dep_time}\n")
            f.write(f"Link: {final_link}\n")
    else:
        print(f"❌ FAILURE: Tool returned error message -> {final_link}")

if __name__ == "__main__":
    asyncio.run(run_booking_link_test())