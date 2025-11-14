#!/usr/bin/env python3
"""
Complete workflow: Fetch outbound flights, select one, then fetch return flight options.
"""

from fast_flights import (
    create_filter,
    get_flights_from_filter,
    get_flights_from_tfs,
    FlightData,
    Passengers,
    create_return_flight_filter,
)

print("=" * 80)
print("Complete Workflow: SFO → MCO Return Flight Options")
print("=" * 80)

# Step 1: Get initial roundtrip search results
print("\nStep 1: Fetching outbound flights (SFO → MCO, Nov 18)...")
print("-" * 80)

filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    max_stops=2,
)

result = get_flights_from_filter(filter, data_source='js')

if result is None or len(result.best) == 0:
    print("No flights found!")
    exit(1)

print(f"✓ Found {len(result.best)} best flights and {len(result.other)} other flights")

# Step 2: Select the first outbound flight
print("\nStep 2: Selecting First Outbound Flight")
print("-" * 80)

selected = result.best[0]
first_flight = selected.flights[0]

print(f"✓ Selected: {selected.airline_names[0]} Flight {first_flight.flight_number}")
print(f"  Route: {selected.departure_airport} → {selected.arrival_airport}")
print(f"  Date: {first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}")
print(f"  Departure: {first_flight.departure_time[0]:02d}:{first_flight.departure_time[1]:02d}")
print(f"  Duration: {selected.travel_time} min")
print(f"  Stops: {len(selected.flights) - 1}")
print(f"  Price: ${selected.itinerary_summary.price:.2f}")

# Step 3: Fetch return flight options
print("\nStep 3: Fetching Return Flight Options (MCO → SFO, Nov 25)...")
print("-" * 80)

return_tfs = create_return_flight_filter(
    outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
    outbound_from=selected.departure_airport,
    outbound_to=selected.arrival_airport,
    outbound_airline=first_flight.airline,
    outbound_flight_number=first_flight.flight_number,
    return_date="2025-11-25",
)

print(f"TFS: {return_tfs}")
print("\nFetching return flights...")

# Use the new get_flights_from_tfs function
# Try with mode='common' first to see if it works without fallback
try:
    return_result = get_flights_from_tfs(return_tfs, data_source='html', mode='common')
except Exception as e:
    print(f"\n⚠ Error fetching return flights: {e}")
    print("\nNote: Return flight fetching requires the page to fully load.")
    print("The generated TFS URL is correct. You can:")
    print(f"  1. Visit the URL in a browser: https://www.google.com/travel/flights?tfs={return_tfs}")
    print("  2. Use mode='local' with Playwright installed")
    print("  3. Use mode='bright-data' with Bright Data API")
    exit(0)

print("\n" + "=" * 80)
print("RETURN FLIGHT OPTIONS")
print("=" * 80)

if return_result is None:
    print("No return flights found!")
    exit(1)

# Display return flights (html data source returns Result with flights list)
print(f"\nFound {len(return_result.flights)} return flight options")
print(f"Current price level: {return_result.current_price}")
print("-" * 80)

for i, flight in enumerate(return_result.flights[:10], 1):
    print(f"\n{i}. {flight.name}")
    print(f"   {'⭐ BEST' if flight.is_best else ''}")
    print(f"   Departure: {flight.departure}")
    print(f"   Arrival: {flight.arrival} ({flight.arrival_time_ahead})")
    print(f"   Duration: {flight.duration}")
    print(f"   Stops: {flight.stops}")
    if flight.delay:
        print(f"   Delay: {flight.delay}")
    print(f"   Price: {flight.price}")

if len(return_result.flights) > 10:
    print(f"\n... and {len(return_result.flights) - 10} more flights")

print("\n" + "=" * 80)
print(f"✓ Successfully fetched {len(return_result.flights)} return flights!")
print("=" * 80)
