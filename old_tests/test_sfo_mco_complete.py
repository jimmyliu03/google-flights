#!/usr/bin/env python3
"""
Complete workflow test: Search for roundtrip flights, then generate return flight URLs.

This demonstrates:
1. Searching for roundtrip flights (SFO -> MCO, Nov 18-25, 2025)
2. Extracting outbound flight details from results
3. Generating return flight selection URLs for each outbound option
"""

from fast_flights import (
    create_filter,
    get_flights_from_filter,
    FlightData,
    Passengers,
    create_return_flight_url,
)

print("=" * 80)
print("Complete SFO → MCO Roundtrip Flight Workflow")
print("=" * 80)

# Step 1: Create initial roundtrip search filter
filter = create_filter(
    flight_data=[
        FlightData(
            date="2025-11-18",
            from_airport="SFO",
            to_airport="MCO",
        ),
        FlightData(
            date="2025-11-25",
            from_airport="MCO",
            to_airport="SFO",
        )
    ],
    trip="round-trip",
    passengers=Passengers(adults=1, children=0, infants_in_seat=0, infants_on_lap=0),
    seat="economy",
    max_stops=2,
)

print("\nStep 1: Initial Roundtrip Search")
print("-" * 80)
print(f"Filter: {filter.as_b64().decode('utf-8')}")
print(f"URL: https://www.google.com/travel/flights?tfs={filter.as_b64().decode('utf-8')}")

print("\nStep 2: Fetch Available Flights (using JS data source)")
print("-" * 80)

result = get_flights_from_filter(filter, data_source='js')

if result is None or len(result.best) == 0:
    print("No flights found!")
    exit(1)

print(f"Found {len(result.best)} best flights and {len(result.other)} other flights")

# Step 3: Generate return flight URLs for top 3 best flights
print("\nStep 3: Generate Return Flight Selection URLs")
print("-" * 80)

print("\nTop 3 Best Outbound Flights with Return Selection URLs:\n")

for i, itinerary in enumerate(result.best[:3], 1):
    # Extract details from the first flight in the itinerary
    first_flight = itinerary.flights[0]

    print(f"{i}. {itinerary.airline_names[0]} Flight {first_flight.flight_number}")
    print(f"   Route: {itinerary.departure_airport} → {itinerary.arrival_airport}")
    print(f"   Departure: {first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d} at {first_flight.departure_time[0]:02d}:{first_flight.departure_time[1]:02d}")
    print(f"   Duration: {itinerary.travel_time} min")
    print(f"   Stops: {len(itinerary.flights) - 1}")
    print(f"   Price: ${itinerary.itinerary_summary.price:.2f}")

    # Generate return flight TFS
    return_tfs = create_return_flight_url(
        outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
        outbound_from=itinerary.departure_airport,
        outbound_to=itinerary.arrival_airport,
        outbound_airline=first_flight.airline,
        outbound_flight_number=first_flight.flight_number,
        return_date="2025-11-25",
    )

    print(f"   Return Flight TFS: {return_tfs}")
    print(f"   Return Flight URL: https://www.google.com/travel/flights?tfs={return_tfs}")
    print()

print("=" * 80)
print("✓ Workflow completed successfully!")
print("\nUsage:")
print("1. Click any 'Return Flight URL' above to see return flight options")
print("2. The URL pre-selects the outbound flight and shows available returns")
print("=" * 80)
