#!/usr/bin/env python3
"""
Debug Frontier return flights - explicitly test JS data source.
"""

from fast_flights import (
    create_filter,
    get_flights_from_filter,
    create_return_flight_filter,
    get_flights_from_tfs,
    FlightData,
    Passengers,
)

print("=" * 80)
print("Debugging Frontier Return Flights - JS Data Source")
print("=" * 80)

# Step 1: Get Frontier outbound flight
print("\nStep 1: Get Frontier outbound flight")
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

outbound = get_flights_from_filter(filter, data_source='js', mode='common')

if outbound and outbound.best:
    # Find Frontier flight
    frontier = None
    for f in outbound.best + outbound.other:
        if f.airline_code == 'F9':
            frontier = f
            break

    if not frontier:
        frontier = outbound.best[0]
        print(f"⚠️  No Frontier flight found, using: {frontier.airline_code}")
    else:
        print(f"✓ Found Frontier: F9 {frontier.flights[0].flight_number}")

    print(f"  TFU: {frontier.tfu}")

    # Step 2: Generate return TFS
    print("\nStep 2: Generate return flight TFS")
    print("-" * 80)

    first = frontier.flights[0]
    return_tfs = create_return_flight_filter(
        outbound_date=f"{first.departure_date[0]}-{first.departure_date[1]:02d}-{first.departure_date[2]:02d}",
        outbound_from=frontier.departure_airport,
        outbound_to=frontier.arrival_airport,
        outbound_airline=first.airline,
        outbound_flight_number=first.flight_number,
        return_date="2025-11-25",
    )

    print(f"✓ Generated TFS: {return_tfs[:60]}...")

    # Step 3: Test JS data source directly
    print("\nStep 3: Test JS data source directly with different modes")
    print("-" * 80)

    for mode in ['common', 'fallback']:
        print(f"\n  Mode: {mode}")
        print(f"  TFU: {frontier.tfu}")

        try:
            result = get_flights_from_tfs(
                return_tfs,
                data_source='js',
                mode=mode,
                tfu=frontier.tfu
            )

            if result and hasattr(result, 'best'):
                best_count = len(result.best)
                other_count = len(result.other)
                total = best_count + other_count

                print(f"  ✓ JS data source returned result")
                print(f"    Best: {best_count}")
                print(f"    Other: {other_count}")
                print(f"    Total: {total}")

                if total > 0:
                    print(f"  ✅ SUCCESS - Found {total} return flights!")

                    # Show first 3
                    all_flights = result.best + result.other
                    for i, itin in enumerate(all_flights[:3], 1):
                        if itin.flights:
                            f = itin.flights[0]
                            price = itin.itinerary_summary.price if itin.itinerary_summary else 0
                            print(f"    {i}. {f.airline} {f.flight_number}: ${price:.2f}")

                    break  # Found working mode
                else:
                    print(f"  ⚠️  JS returned 0 flights")

                    # Check if raw data exists
                    if hasattr(result, 'raw'):
                        print(f"    Raw data has {len(result.raw)} elements")
                        if len(result.raw) > 3:
                            print(f"    data[2] = {type(result.raw[2])}: {result.raw[2]}")
                            print(f"    data[3] = {type(result.raw[3])}: {len(result.raw[3]) if isinstance(result.raw[3], list) else 'not a list'}")
            else:
                print(f"  ⚠️  JS returned unexpected type: {type(result)}")

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)[:200]}")
            import traceback
            traceback.print_exc()

    # Step 4: Compare with HTML data source
    print("\n\nStep 4: Compare with HTML data source")
    print("-" * 80)

    try:
        result_html = get_flights_from_tfs(
            return_tfs,
            data_source='html',
            mode='common',
            tfu=frontier.tfu
        )

        if result_html and hasattr(result_html, 'flights'):
            print(f"  ✓ HTML data source returned {len(result_html.flights)} flights")
            if result_html.flights:
                for i, f in enumerate(result_html.flights[:3], 1):
                    print(f"    {i}. {f.name}: {f.price}")
        else:
            print(f"  ⚠️  HTML returned unexpected type: {type(result_html)}")

    except Exception as e:
        print(f"  ❌ HTML ERROR: {str(e)[:200]}")

else:
    print("❌ No outbound flights found")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("""
This test explicitly uses data_source='js' to verify:
1. TFU is preserved from outbound flight ✓
2. JS data source is being used (not HTML fallback)
3. Whether JS returns data or needs different mode
4. Comparison with HTML data source

If JS returns 0 flights but HTML has flights:
- The page needs JavaScript rendering (mode='fallback' or higher)
- Check if data[3][0] has flights in the raw data structure
""")
