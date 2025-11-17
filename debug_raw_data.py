#!/usr/bin/env python3
"""Debug script to inspect raw data structure"""

from fast_flights import get_flights_from_tfs
from fast_flights.decoder import NLData, FlightDecoder

tfs = "CBwQAhogEgoyMDI1LTEyLTMwKAJqBwgBEgNPQUtyBwgBEgNMQVNAAUgBcAGCAQsI____________AZgBAg"

print("Fetching flights...")
result = get_flights_from_tfs(tfs, data_source='js', mode='fallback')

if result and hasattr(result, 'best'):
    # Find XE 657
    for itinerary in result.best:
        for flight in itinerary.flights:
            if flight.airline == "XE" and flight.flight_number == "657":
                print("\n" + "=" * 80)
                print(f"Found XE 657 - checking raw data")
                print("=" * 80)
                
                # Try to access the raw itinerary data if available
                # The issue is we need to look at the actual raw nested list data
                # that was passed to the FlightDecoder
                
                # Let's check the result object
                print(f"\nItinerary object type: {type(itinerary)}")
                print(f"Has __dict__: {hasattr(itinerary, '__dict__')}")
                
                # Print all attributes
                if hasattr(itinerary, '__dict__'):
                    for attr, value in itinerary.__dict__.items():
                        print(f"  {attr}: {type(value)}")
                
                break
    
    # Let's also try to intercept at a lower level
    # by looking at the core.py parse_response function
    print("\n\nWe need to check the raw JS data being parsed...")
    print("The issue is likely in how the raw nested list from Google is structured.")
    print("\nNext step: inspect the actual JS data extraction in core.py")

