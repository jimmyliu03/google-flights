#!/usr/bin/env python3
"""
Test script to parse and display return flight details from a TFS string.

Usage:
    python test_parse_return_tfs.py
"""

from fast_flights import get_flights_from_tfs

# TFS string from user (may include &tfu parameter)
raw_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBBAgBEAKYAQE&tfu=CmxDalJJTkZsRFNsSlJhekE1Vkc5QlFsaHZlbWRDUnkwdExTMHRMUzB0TFMxNWJHOXpNMEZCUVVGQlIydFhkbmR6VFU5V1pGVkJFZ1pWUVRJeU16QWFDd2o1dEFVUUFob0RWVk5FT0J4dytiUUYSAggAIgMKATA"

# Extract just the TFS part (before &tfu=)
tfs = raw_tfs.split('&')[0]

print("=" * 80)
print("Return Flight TFS Parser")
print("=" * 80)

print(f"\nTFS String: {tfs}")
print(f"\nFull URL: https://www.google.com/travel/flights?tfs={tfs}")

# Decode the TFS to show what flight was selected
print("\n" + "-" * 80)
print("Decoding TFS to extract selected outbound flight info...")
print("-" * 80)

import base64
from fast_flights import flights_pb2 as PB

try:
    # Try URL-safe base64 decoding (handles _ and - characters)
    # Add padding if needed
    tfs_padded = tfs + "=" * ((4 - len(tfs) % 4) % 4)
    try:
        tfs_bytes = base64.urlsafe_b64decode(tfs_padded)
    except:
        # Fall back to standard base64
        tfs_bytes = base64.b64decode(tfs_padded)

    query = PB.ReturnFlightQuery()
    query.ParseFromString(tfs_bytes)

    print(f"\nQuery Type: {query.query_type}")
    print(f"Step: {query.step}")

    if len(query.legs) >= 1:
        outbound_leg = query.legs[0]
        print(f"\nSelected Outbound Flight:")
        print(f"  Date: {outbound_leg.date}")
        if outbound_leg.HasField('selected_flight'):
            print(f"  From: {outbound_leg.selected_flight.from_airport}")
            print(f"  To: {outbound_leg.selected_flight.to_airport}")
            print(f"  Airline: {outbound_leg.selected_flight.airline}")
            print(f"  Flight Number: {outbound_leg.selected_flight.flight_number}")

    if len(query.legs) >= 2:
        return_leg = query.legs[1]
        print(f"\nReturn Flight Search:")
        print(f"  Date: {return_leg.date}")
        print(f"  (Searching for flights on this date)")

except Exception as e:
    print(f"Error decoding TFS: {e}")

# Fetch return flights
print("\n" + "=" * 80)
print("Fetching Return Flight Options...")
print("=" * 80)

try:
    # Try with JS data source to get detailed flight information including flight numbers
    # Using mode='fallback' which will automatically try different methods
    print("\nAttempting to fetch with data_source='js', mode='fallback'...")
    print("This will try direct scraping first, then fall back to Playwright if needed\n")

    result = get_flights_from_tfs(tfs, data_source='js', mode='fallback')

    print(f"\n✓ Successfully fetched return flights!")
    print("\n" + "-" * 80)
    print("Return Flight Options:")
    print("-" * 80)

    # JS data source returns DecodedResult with 'best' and 'other' lists
    if hasattr(result, 'best'):
        print(f"\nBest Return Flights ({len(result.best)} options):")
        print("-" * 80)

        for i, itinerary in enumerate(result.best[:10], 1):
            first_flight = itinerary.flights[0]
            print(f"\n{i}. {itinerary.airline_names[0]} Flight {first_flight.flight_number}")
            print(f"   Route: {itinerary.departure_airport} → {itinerary.arrival_airport}")
            print(f"   Departure: {first_flight.departure_time[0]:02d}:{first_flight.departure_time[1]:02d}")
            print(f"   Arrival: {first_flight.arrival_time[0]:02d}:{first_flight.arrival_time[1]:02d}")
            print(f"   Duration: {itinerary.travel_time} min")
            print(f"   Stops: {len(itinerary.flights) - 1}")
            print(f"   Aircraft: {first_flight.aircraft}")
            if itinerary.itinerary_summary:
                print(f"   Total Trip Price: ${itinerary.itinerary_summary.price:.2f}")

            # Show all flight segments if there are stops
            if len(itinerary.flights) > 1:
                print(f"   Segments:")
                for j, flight in enumerate(itinerary.flights, 1):
                    print(f"     {j}. {flight.airline_name} {flight.flight_number}: {flight.departure_airport} → {flight.arrival_airport}")

        if len(result.other) > 0:
            print(f"\n\nOther Return Flights ({len(result.other)} options, showing first 5):")
            print("-" * 80)

            for i, itinerary in enumerate(result.other[:5], 1):
                first_flight = itinerary.flights[0]
                print(f"\n{i}. {itinerary.airline_names[0]} Flight {first_flight.flight_number}")
                print(f"   Route: {itinerary.departure_airport} → {itinerary.arrival_airport}")
                print(f"   Departure: {first_flight.departure_time[0]:02d}:{first_flight.departure_time[1]:02d}")
                print(f"   Arrival: {first_flight.arrival_time[0]:02d}:{first_flight.arrival_time[1]:02d}")
                print(f"   Duration: {itinerary.travel_time} min")
                print(f"   Stops: {len(itinerary.flights) - 1}")
                if itinerary.itinerary_summary:
                    print(f"   Total Trip Price: ${itinerary.itinerary_summary.price:.2f}")
    else:
        # Fallback to HTML format display
        print(f"\n✓ Successfully fetched {len(result.flights)} return flights!")
        print(f"Current price level: {result.current_price}")

        for i, flight in enumerate(result.flights[:15], 1):
            print(f"\n{i}. {flight.name}")
            if flight.is_best:
                print(f"   ⭐ BEST FLIGHT")
            print(f"   Departure: {flight.departure}")
            print(f"   Arrival: {flight.arrival} ({flight.arrival_time_ahead})")
            print(f"   Duration: {flight.duration}")
            print(f"   Stops: {flight.stops} stop(s)")
            if flight.delay:
                print(f"   Delay: {flight.delay}")
            print(f"   Price: {flight.price}")

        if len(result.flights) > 15:
            print(f"\n... and {len(result.flights) - 15} more flights")

except Exception as e:
    print(f"\n⚠ Error fetching flights: {e}")
    print("\nTo get flight numbers with data_source='js', you need JavaScript execution:")
    print("\n1. mode='local' (requires Playwright):")
    print("   pip install 'fast-flights[local]'")
    print(f"   result = get_flights_from_tfs('{tfs}', mode='local', data_source='js')")
    print("\n2. mode='bright-data' (requires Bright Data API):")
    print("   export BRIGHT_DATA_API_KEY='your-key'")
    print(f"   result = get_flights_from_tfs('{tfs}', mode='bright-data', data_source='js')")
    print("\n3. View in browser:")
    print(f"   https://www.google.com/travel/flights?tfs={tfs}")

print("\n" + "=" * 80)
