#!/usr/bin/env python3
"""
Test script for get_return_flight_options functionality - OAK to SAN.

This tests the new API for fetching return flight options with flight numbers.
Route: OAK → SAN on Jan 30, 2026, returning Feb 1, 2026
"""

from fast_flights import (
    create_filter,
    get_flights_from_filter,
    create_return_flight_filter,
    get_return_flight_options,
    decode_return_flight_tfs,
    FlightData,
    Passengers,
)

print("=" * 80)
print("Test: get_return_flight_options() - OAK to SAN")
print("=" * 80)

# Step 1: Search for roundtrip flights
print("\nStep 1: Searching for outbound flights (OAK → SAN, Jan 30, 2026)")
print("-" * 80)

filter = create_filter(
    flight_data=[
        FlightData(date="2026-01-30", from_airport="OAK", to_airport="SAN"),
        FlightData(date="2026-02-01", from_airport="SAN", to_airport="OAK"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
    max_stops=2,
)

outbound_results = get_flights_from_filter(filter, data_source='js')

print(f"\nOutbound search TFS: {filter.as_b64().decode('utf-8')}")
print(f"\nFull outbound Google Flights URL:")
print(f"https://www.google.com/travel/flights?tfs={filter.as_b64().decode('utf-8')}&tfu=EgQIABABIgA")

if outbound_results is None or len(outbound_results.best) == 0:
    print("No outbound flights found!")
    exit(1)

print(f"✓ Found {len(outbound_results.best)} best outbound flights")

# Step 2: Select the outbound flight that departs at 11:50am
print("\nStep 2: Selecting outbound flight departing at 11:50am")
print("-" * 80)

selected_outbound = None
for flight_option in outbound_results.best:
    first_flight = flight_option.flights[0]
    departure_time = first_flight.departure_time

    # Departure time is a list [hour, minute]
    if isinstance(departure_time, list) and len(departure_time) >= 2:
        if departure_time[0] == 11 and departure_time[1] == 50:
            selected_outbound = flight_option
            print(f"✓ Found flight departing at {departure_time[0]}:{departure_time[1]:02d}")
            break

if selected_outbound is None:
    print("⚠ Could not find flight departing at 11:50am")
    print("\nAvailable flights:")
    for i, flight_option in enumerate(outbound_results.best[:10], 1):
        first_flight = flight_option.flights[0]
        dep_time = first_flight.departure_time
        if isinstance(dep_time, list) and len(dep_time) >= 2:
            time_str = f"{dep_time[0]}:{dep_time[1]:02d}"
        else:
            time_str = str(dep_time)
        print(f"{i}. {flight_option.airline_names[0]} {first_flight.flight_number} - Departs: {time_str}")
    print("\nUsing first available flight instead...")
    selected_outbound = outbound_results.best[0]

first_flight = selected_outbound.flights[0]

print(f"Selected: {selected_outbound.airline_names[0]} Flight {first_flight.flight_number}")
print(f"Route: {selected_outbound.departure_airport} → {selected_outbound.arrival_airport}")
print(f"Type: {'Direct flight' if len(selected_outbound.flights) == 1 else f'Connecting ({len(selected_outbound.flights)} legs)'}")
if len(selected_outbound.flights) > 1:
    for i, f in enumerate(selected_outbound.flights, 1):
        print(f"  Leg {i}: {f.airline} {f.flight_number} ({f.departure_airport} → {f.arrival_airport})")
print(f"Date: {first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}")

# Format departure and arrival times
dep_time = first_flight.departure_time
arr_time = first_flight.arrival_time
if isinstance(dep_time, list) and len(dep_time) >= 2:
    dep_time_str = f"{dep_time[0]}:{dep_time[1]:02d}"
else:
    dep_time_str = str(dep_time)
if isinstance(arr_time, list) and len(arr_time) >= 2:
    arr_time_str = f"{arr_time[0]}:{arr_time[1]:02d}"
else:
    arr_time_str = str(arr_time)

print(f"Departure Time: {dep_time_str}")
print(f"Arrival Time: {arr_time_str}")
print(f"Price: ${selected_outbound.itinerary_summary.price:.2f}")
print(f"TFU: {selected_outbound.tfu[:60]}..." if selected_outbound.tfu else "TFU: None")

# Build connecting_segments list if this is a multi-leg flight
connecting_segments = None
if len(selected_outbound.flights) > 1:
    connecting_segments = []
    for i in range(1, len(selected_outbound.flights)):
        segment = selected_outbound.flights[i]
        # Use next segment's departure_airport as this segment's arrival, or itinerary arrival for last segment
        to_airport = selected_outbound.flights[i+1].departure_airport if i+1 < len(selected_outbound.flights) else selected_outbound.arrival_airport
        connecting_segments.append({
            'from': segment.departure_airport,
            'to': to_airport,
            'airline': segment.airline,
            'flight_number': segment.flight_number,
        })

return_search_tfs = create_return_flight_filter(
    outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
    outbound_from=selected_outbound.departure_airport,
    outbound_to=selected_outbound.arrival_airport,
    outbound_airline=first_flight.airline,
    outbound_flight_number=first_flight.flight_number,
    connecting_segments=connecting_segments,
    return_date="2026-02-01",
    max_stops=2,
)

print(f"\nGenerated return search TFS: {return_search_tfs}")
print(f"\nFull Google Flights URL:")
print(f"https://www.google.com/travel/flights?tfs={return_search_tfs}&tfu={selected_outbound.tfu}")

# Step 3: Use new API to get return flight options with flight numbers
print("\nStep 3: Fetching return flight options with flight numbers")
print("-" * 80)

try:
    # Use the TFS generated in Step 2
    # Note: Some return flight pages require JS rendering (mode='fallback' or higher)
    # to populate flight data, even though the decoder now handles the structure
    print("Using TFS from Step 2 with mode='fallback'...")
    print("Note: Return flight pages may require JS rendering to load flight data")
    print(f"Passing TFU from selected outbound: {selected_outbound.tfu[:60]}...")
    return_options = get_return_flight_options(return_search_tfs, mode='fallback', tfu=selected_outbound.tfu)

    print(f"\n✓ Successfully fetched {len(return_options)} return flight options with flight numbers!")
    print("\nReturn Flight Options:")
    print("-" * 80)

    # Display top 10 return options
    for i, option in enumerate(return_options[:10], 1):
        print(f"\n{i}. {option.airline} {option.flight_number}")
        print(f"   Route: {option.departure_airport} → {option.arrival_airport}")
        print(f"   Date: {option.departure_date}")
        print(f"   Departure: {option.departure_time}")
        print(f"   Arrival: {option.arrival_time}")
        print(f"   Duration: {option.duration_minutes} min ({option.duration_minutes // 60}h {option.duration_minutes % 60}m)")
        print(f"   Stops: {option.stops}")
        print(f"   Aircraft: {option.aircraft or 'N/A'}")
        print(f"   Total Price: ${option.total_price:.2f} {option.currency}")

    if len(return_options) > 10:
        print(f"\n... and {len(return_options) - 10} more return flight options")

except Exception as e:
    print(f"\n⚠ Error: {e}")
    print("\nUnexpected error occurred. The JS data source should now work for return flights.")
    print("Please check the error message above for details.")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
