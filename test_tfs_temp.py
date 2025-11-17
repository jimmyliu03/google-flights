#!/usr/bin/env python3
"""Temporary test script to fetch flight results for a specific TFS"""

from fast_flights import get_flights_from_tfs

# TFS parameter provided by user
tfs = "CBwQAhogEgoyMDI1LTEyLTMwKAJqBwgBEgNPQUtyBwgBEgNMQVNAAUgBcAGCAQsI____________AZgBAg"

print("=" * 80)
print("Fetching flights for TFS:")
print(f"  {tfs}")
print(f"  URL: https://www.google.com/travel/flights?tfs={tfs}")
print("=" * 80)

def format_time(time_list):
    """Format time from list to HH:MM string, handling missing minutes"""
    if not time_list or len(time_list) == 0:
        return "N/A"
    
    hour = time_list[0] if time_list[0] is not None else 0
    minute = time_list[1] if len(time_list) >= 2 and time_list[1] is not None else 0
    
    return f"{hour:02d}:{minute:02d}"

# Fetch flights using JS data source for detailed information
print("\nFetching flights (this may take a moment)...")
try:
    result = get_flights_from_tfs(tfs, data_source='js', mode='fallback')
    
    if result and hasattr(result, 'best'):
        print(f"\n✓ Found {len(result.best)} best flights")
        print(f"✓ Found {len(result.other)} other flights")
        print(f"Total: {len(result.best) + len(result.other)} flights")
        
        print("\n" + "=" * 80)
        print("BEST FLIGHTS")
        print("=" * 80)
        
        for i, itinerary in enumerate(result.best, 1):
            print(f"\n{i}. {itinerary.airline_code} - ${itinerary.itinerary_summary.price if itinerary.itinerary_summary else 'N/A'} {itinerary.itinerary_summary.currency if itinerary.itinerary_summary else ''}")
            print(f"   Route: {itinerary.departure_airport} → {itinerary.arrival_airport}")
            print(f"   Travel time: {itinerary.travel_time} minutes")
            print(f"   Flights: {len(itinerary.flights)} segment(s)")
            
            for j, flight in enumerate(itinerary.flights, 1):
                print(f"     Segment {j}: {flight.airline} {flight.flight_number}")
                print(f"       {flight.departure_airport} → {flight.arrival_airport}")
                
                # Format times using helper function
                dep_time = format_time(flight.departure_time)
                arr_time = format_time(flight.arrival_time)
                
                print(f"       Depart: {dep_time}, Arrive: {arr_time}")
                print(f"       Duration: {flight.travel_time} minutes")
                if flight.aircraft:
                    print(f"       Aircraft: {flight.aircraft}")
            
            if itinerary.layovers:
                print(f"   Layovers: {len(itinerary.layovers)}")
                for k, layover in enumerate(itinerary.layovers, 1):
                    print(f"     {k}. {layover.airport} - {layover.duration} minutes")
        
        print("\n" + "=" * 80)
        print("OTHER FLIGHTS (first 5)")
        print("=" * 80)
        
        for i, itinerary in enumerate(result.other[:5], 1):
            print(f"\n{i}. {itinerary.airline_code} - ${itinerary.itinerary_summary.price if itinerary.itinerary_summary else 'N/A'} {itinerary.itinerary_summary.currency if itinerary.itinerary_summary else ''}")
            print(f"   Route: {itinerary.departure_airport} → {itinerary.arrival_airport}")
            print(f"   Travel time: {itinerary.travel_time} minutes, {len(itinerary.flights)} segment(s)")
            
            # Show just the flight numbers
            flight_nums = [f"{f.airline} {f.flight_number}" for f in itinerary.flights]
            print(f"   Flights: {', '.join(flight_nums)}")
    
    else:
        print("✗ No flights found or invalid response")
        if result:
            print(f"Result type: {type(result)}")
            print(f"Has 'best' attr: {hasattr(result, 'best')}")

except Exception as e:
    print(f"✗ Error fetching flights: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
