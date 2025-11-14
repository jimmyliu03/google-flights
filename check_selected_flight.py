#!/usr/bin/env python3
"""
Check what flight is actually being selected.
"""

from fast_flights import (
    create_filter,
    get_flights_from_filter,
    FlightData,
    Passengers,
)

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

outbound = get_flights_from_filter(filter, data_source='js')

if outbound and outbound.best:
    print("First 3 'best' itineraries:")
    print("=" * 80)

    for i, itin in enumerate(outbound.best[:3], 1):
        print(f"\n{i}. {itin.airline_names[0] if itin.airline_names else 'Unknown'}")
        print(f"   Overall route: {itin.departure_airport} → {itin.arrival_airport}")
        print(f"   Price: ${itin.itinerary_summary.price:.2f}")
        print(f"   Number of flights in itinerary: {len(itin.flights)}")
        print(f"   Flights:")

        for j, flight in enumerate(itin.flights, 1):
            print(f"     {j}. {flight.airline} {flight.flight_number}: {flight.departure_airport} → {flight.arrival_airport}")

        print(f"   TFU: {itin.tfu}")
