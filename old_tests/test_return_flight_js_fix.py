#!/usr/bin/env python3
"""
Test script to verify the decoder fix for return flight pages with data_source='js'.

This tests that the decoder now handles None values gracefully when return flight
pages have data[2] = None (no "best" flights section).
"""

from fast_flights import get_flights_from_tfs

# Return flight TFS string - has outbound flight selected (UA2230), showing return options
return_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBBAgBEAKYAQE"

print("=" * 80)
print("Testing JS Data Source Fix for Return Flight Pages")
print("=" * 80)

print(f"\nReturn Flight TFS: {return_tfs[:50]}...")
print(f"\nFetching with data_source='js', mode='common'...")

try:
    result = get_flights_from_tfs(return_tfs, data_source='js', mode='common')

    if result is None:
        print("\n⚠ Result is None - no data returned")
    elif hasattr(result, 'best'):
        # JS data source returns DecodedResult
        print("\n✓ Successfully parsed JS data!")
        print(f"\nBest flights: {len(result.best)}")
        print(f"Other flights: {len(result.other)}")

        # Display all return flight options
        all_flights = result.best + result.other
        print(f"\nTotal return flight options: {len(all_flights)}")
        print("\n" + "-" * 80)
        print("Return Flight Options:")
        print("-" * 80)

        for i, itinerary in enumerate(all_flights[:15], 1):
            if not itinerary.flights:
                continue

            first_flight = itinerary.flights[0]
            print(f"\n{i}. {first_flight.airline_name} {first_flight.flight_number}")
            print(f"   Route: {itinerary.departure_airport} → {itinerary.arrival_airport}")

            # Handle time data safely
            if first_flight.departure_time and len(first_flight.departure_time) >= 2:
                print(f"   Departure: {first_flight.departure_time[0]:02d}:{first_flight.departure_time[1]:02d}")
            if first_flight.arrival_time and len(first_flight.arrival_time) >= 2:
                print(f"   Arrival: {first_flight.arrival_time[0]:02d}:{first_flight.arrival_time[1]:02d}")

            print(f"   Duration: {itinerary.travel_time} min")
            print(f"   Stops: {len(itinerary.flights) - 1}")
            if first_flight.aircraft:
                print(f"   Aircraft: {first_flight.aircraft}")

            if itinerary.itinerary_summary:
                print(f"   Total Price: ${itinerary.itinerary_summary.price:.2f} {itinerary.itinerary_summary.currency}")

            # Show connection details if multi-leg
            if len(itinerary.flights) > 1:
                print(f"   Connections:")
                for j, flight in enumerate(itinerary.flights, 1):
                    print(f"     {j}. {flight.airline_name} {flight.flight_number}: {flight.departure_airport} → {flight.arrival_airport}")

        if len(all_flights) > 15:
            print(f"\n... and {len(all_flights) - 15} more return flight options")

        print("\n" + "=" * 80)
        print("✓ SUCCESS: JS data source now works for return flight pages!")
        print("=" * 80)
    else:
        # HTML data source returns Result
        print("\n⚠ Unexpected result type (HTML instead of JS)")
        print(f"Result type: {type(result)}")

except Exception as e:
    print(f"\n⚠ Error: {e}")
    print("\nIf you still see 'Found non list type' error, the fix may not be applied correctly.")
    import traceback
    traceback.print_exc()

print()
