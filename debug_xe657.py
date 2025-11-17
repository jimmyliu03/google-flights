#!/usr/bin/env python3
"""Debug script to inspect XE 657 flight data"""

from fast_flights import get_flights_from_tfs
import json

tfs = "CBwQAhogEgoyMDI1LTEyLTMwKAJqBwgBEgNPQUtyBwgBEgNMQVNAAUgBcAGCAQsI____________AZgBAg"

print("Fetching flights...")
result = get_flights_from_tfs(tfs, data_source='js', mode='fallback')

if result and hasattr(result, 'best'):
    # Find XE 657
    for itinerary in result.best:
        for flight in itinerary.flights:
            if flight.airline == "XE" and flight.flight_number == "657":
                print("\n" + "=" * 80)
                print(f"Found XE 657!")
                print("=" * 80)
                print(f"\nFlight object attributes:")
                print(f"  airline: {flight.airline}")
                print(f"  flight_number: {flight.flight_number}")
                print(f"  departure_airport: {flight.departure_airport}")
                print(f"  arrival_airport: {flight.arrival_airport}")
                print(f"  departure_time: {flight.departure_time}")
                print(f"  departure_time type: {type(flight.departure_time)}")
                print(f"  arrival_time: {flight.arrival_time}")
                print(f"  arrival_time type: {type(flight.arrival_time)}")
                print(f"  departure_date: {flight.departure_date}")
                print(f"  arrival_date: {flight.arrival_date}")
                print(f"  travel_time: {flight.travel_time}")
                
                # Check if departure_time has data
                if flight.departure_time:
                    print(f"\n  departure_time length: {len(flight.departure_time)}")
                    print(f"  departure_time contents: {list(flight.departure_time)}")
                    
                    if len(flight.departure_time) >= 2:
                        print(f"  departure_time[0]: {flight.departure_time[0]} (type: {type(flight.departure_time[0])})")
                        print(f"  departure_time[1]: {flight.departure_time[1]} (type: {type(flight.departure_time[1])})")
                else:
                    print(f"\n  departure_time is None or empty")
                
                # Print the full raw_itinerary if available
                if hasattr(itinerary, 'raw_itinerary') and itinerary.raw_itinerary:
                    print(f"\nRaw itinerary data available: {type(itinerary.raw_itinerary)}")
                
                break
    
    # Also check if it's in the "other" flights
    print("\n\nChecking in 'other' flights as well...")
    for i, itinerary in enumerate(result.other):
        for flight in itinerary.flights:
            if flight.airline == "XE" and flight.flight_number == "657":
                print(f"\nFound XE 657 in 'other' flights at index {i}!")
                print(f"  departure_time: {flight.departure_time}")
                break

else:
    print("No results found")
