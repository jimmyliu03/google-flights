#!/usr/bin/env python3
"""
Debug why the Frontier return flight TFS returns 0 results.
"""

from fast_flights import (
    create_filter,
    get_flights_from_filter,
    create_return_flight_filter,
    get_flights_from_tfs,
    FlightData,
    Passengers,
)

# Step 1: Get outbound flights
print("Step 1: Getting outbound flights...")
filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
    max_stops=2,
)

outbound_results = get_flights_from_filter(filter, data_source='js')
selected_outbound = outbound_results.best[0]
first_flight = selected_outbound.flights[0]

print(f"Selected: {selected_outbound.airline_names[0]} {first_flight.flight_number}")
print(f"Airline code: {first_flight.airline}")
print(f"Route: {selected_outbound.departure_airport} → {selected_outbound.arrival_airport}")

# Step 2: Generate return TFS
print("\nStep 2: Generating return flight TFS...")
return_search_tfs = create_return_flight_filter(
    outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
    outbound_from=selected_outbound.departure_airport,
    outbound_to=selected_outbound.arrival_airport,
    outbound_airline=first_flight.airline,
    outbound_flight_number=first_flight.flight_number,
    return_date="2025-11-25",
)

print(f"TFS: {return_search_tfs[:80]}...")

# Step 3: Try to fetch with JS data source
print("\nStep 3: Fetching with JS data source, mode='common'...")
try:
    result = get_flights_from_tfs(return_search_tfs, data_source='js', mode='common')

    if result and hasattr(result, 'best'):
        print(f"✓ Got DecodedResult")
        print(f"  Best: {len(result.best)}")
        print(f"  Other: {len(result.other)}")
        print(f"  Total: {len(result.best) + len(result.other)}")

        if len(result.best) + len(result.other) == 0:
            print("\n⚠ Result has 0 flights!")
            print("Checking raw data...")
            if hasattr(result, 'raw'):
                print(f"Raw data length: {len(result.raw)}")
                if len(result.raw) > 2:
                    print(f"Raw[2]: {result.raw[2]}")
                if len(result.raw) > 3:
                    print(f"Raw[3]: {result.raw[3]}")
    else:
        print(f"⚠ Got unexpected result type: {type(result)}")

except Exception as e:
    print(f"⚠ Error: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Try HTML data source as comparison
print("\nStep 4: Fetching with HTML data source, mode='common'...")
try:
    result_html = get_flights_from_tfs(return_search_tfs, data_source='html', mode='common')

    if result_html and hasattr(result_html, 'flights'):
        print(f"✓ Got HTML Result with {len(result_html.flights)} flights")
    else:
        print(f"⚠ Got unexpected result: {result_html}")

except Exception as e:
    print(f"⚠ Error: {e}")
