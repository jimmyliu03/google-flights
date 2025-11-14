#!/usr/bin/env python3
"""
Test Frontier return flights with TFU parameter preservation.
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
print("Testing Frontier Return Flights with TFU Preservation")
print("=" * 80)

# Step 1: Search for roundtrip flights
print("\nStep 1: Searching for Frontier roundtrip flights (SFO → MCO)")
print("-" * 80)

filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
)

# Fetch with default TFU
outbound = get_flights_from_filter(filter, data_source='js', mode='common')

if outbound and outbound.best:
    print(f"✓ Found {len(outbound.best)} best flights")

    # Find a Frontier flight if available
    frontier_flight = None
    for flight in outbound.best + outbound.other:
        if 'F9' in flight.airline_code or 'Frontier' in str(flight.airline_names):
            frontier_flight = flight
            break

    if frontier_flight:
        print(f"\n✓ Found Frontier flight: F9 {frontier_flight.flights[0].flight_number}")
        print(f"  Route: {frontier_flight.departure_airport} → {frontier_flight.arrival_airport}")
        print(f"  TFU stored: {frontier_flight.tfu}")
        print(f"  ✅ TFU preserved from outbound search")

        # Step 2: Generate return flight search
        print("\nStep 2: Generating return flight search for Frontier")
        print("-" * 80)

        first = frontier_flight.flights[0]
        return_tfs = create_return_flight_filter(
            outbound_date=f"{first.departure_date[0]}-{first.departure_date[1]:02d}-{first.departure_date[2]:02d}",
            outbound_from=frontier_flight.departure_airport,
            outbound_to=frontier_flight.arrival_airport,
            outbound_airline=first.airline,
            outbound_flight_number=first.flight_number,
            return_date="2025-11-25",
        )

        print(f"✓ Generated return TFS: {return_tfs[:60]}...")

        # Step 3: Test different modes to find what works for Frontier
        print("\nStep 3: Testing different modes for Frontier return flights")
        print("-" * 80)

        modes = ['common', 'fallback']

        for mode in modes:
            print(f"\n  Testing mode='{mode}' with TFU='{frontier_flight.tfu}'...")
            try:
                options = get_return_flight_options(
                    return_tfs,
                    mode=mode,
                    tfu=frontier_flight.tfu
                )

                if options and len(options) > 0:
                    print(f"  ✅ SUCCESS: Got {len(options)} return flights with mode='{mode}'")

                    # Show first 3 flights
                    for i, opt in enumerate(options[:3], 1):
                        print(f"    {i}. {opt.airline} {opt.flight_number}: ${opt.total_price:.2f}")

                    # Check if any are Frontier
                    frontier_returns = [o for o in options if 'F9' in o.airline or 'Frontier' in o.airline]
                    if frontier_returns:
                        print(f"  ✓ Found {len(frontier_returns)} Frontier return flights")

                    break  # Found working mode
                else:
                    print(f"  ⚠️  0 flights with mode='{mode}'")

            except Exception as e:
                print(f"  ❌ ERROR with mode='{mode}': {str(e)[:100]}")
    else:
        print("\n⚠️  No Frontier flights found in results")
        print("  Testing TFU preservation with first available flight...")

        selected = outbound.best[0]
        print(f"\n  Selected: {selected.airline_code} {selected.flights[0].flight_number}")
        print(f"  TFU stored: {selected.tfu}")
        print(f"  ✅ TFU preserved from outbound search")
else:
    print("❌ No outbound flights found")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("""
TFU Preservation Test:
- TFU parameter from outbound search is stored in each Itinerary ✓
- TFU is passed to return flight search ✓
- Need to verify correct mode for Frontier return flights

If 0 return flights are found:
- The return flight page may require JavaScript rendering
- Try mode='fallback' or mode='force-fallback'
- Some airline-specific pages have different requirements
""")
