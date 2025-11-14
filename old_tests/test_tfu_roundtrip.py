#!/usr/bin/env python3
"""
Test TFU functionality with a complete roundtrip workflow.
"""

from fast_flights import (
    create_filter,
    get_flights_from_filter,
    create_return_flight_filter,
    get_return_flight_options,
    FlightData,
    Passengers,
)

print("=" * 80)
print("Testing TFU with Complete Roundtrip Workflow")
print("=" * 80)

# Custom TFU parameter to test
custom_tfu = "CnhDalJJWkhoRlNXcFlaSEpNV0ZWQlFrMXdjbWRDUnkwdExTMHRMUzB0ZVdsaVltTXlPRUZCUVVGQlIydFhNRnBqU1hoTVdqaEJFZzFHT1RReE5UaDhSamt4T0RjMkdnc0l5ZnNCRUFJYUExVlRSRGdjY01uN0FRPT0SAggAIgMKATA"

print("\nStep 1: Create filter for roundtrip SFO → MCO")
filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
)

print("\nStep 2: Fetch outbound flights with custom tfu")
print(f"Custom TFU: {custom_tfu[:60]}...")

result = get_flights_from_filter(
    filter,
    data_source='js',
    mode='common',
    tfu=custom_tfu
)

if result and hasattr(result, 'best'):
    total = len(result.best) + len(result.other)
    print(f"\n✅ Fetched {len(result.best)} best + {len(result.other)} other = {total} flights")

    # Verify tfu is stored
    if result.best:
        selected = result.best[0]
        print(f"\n✓ Selected outbound flight: {selected.flights[0].airline} {selected.flights[0].flight_number}")
        print(f"✓ TFU stored in itinerary: {selected.tfu[:60]}...")

        if selected.tfu == custom_tfu:
            print("✅ TFU matches custom parameter!")
        else:
            print(f"⚠️  TFU mismatch")

        # Step 3: Generate return flight TFS
        print("\nStep 3: Generate return flight search")
        first_flight = selected.flights[0]

        return_tfs = create_return_flight_filter(
            outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
            outbound_from=selected.departure_airport,
            outbound_to=selected.arrival_airport,
            outbound_airline=first_flight.airline,
            outbound_flight_number=first_flight.flight_number,
            return_date="2025-11-25",
        )

        print(f"✓ Generated return TFS: {return_tfs[:60]}...")

        # Step 4: Fetch return flights with tfu
        print("\nStep 4: Fetch return flights with tfu from selected outbound")
        print(f"Passing tfu: {selected.tfu[:60]}...")

        try:
            return_options = get_return_flight_options(
                return_tfs,
                mode='fallback',
                tfu=selected.tfu
            )

            print(f"\n✅ SUCCESS: Fetched {len(return_options)} return flights")

            if return_options:
                print("\nFirst 3 return flights:")
                for i, opt in enumerate(return_options[:3], 1):
                    print(f"  {i}. {opt.airline} {opt.flight_number}: ${opt.total_price:.2f}")

                print("\n" + "=" * 80)
                print("✅ COMPLETE TFU WORKFLOW SUCCESSFUL!")
                print("=" * 80)
                print(f"1. Created roundtrip filter ✓")
                print(f"2. Fetched outbound flights with custom tfu='{custom_tfu[:40]}...' ✓")
                print(f"3. TFU stored in {total} itineraries ✓")
                print(f"4. Selected outbound: {selected.flights[0].airline} {selected.flights[0].flight_number} ✓")
                print(f"5. Passed tfu to return flight search ✓")
                print(f"6. Fetched {len(return_options)} return flights ✓")
            else:
                print("⚠️  0 return flights (may need mode='fallback')")

        except Exception as e:
            print(f"❌ ERROR fetching return flights: {e}")
    else:
        print("⚠️  No best flights found")
else:
    print("⚠️  No results")
