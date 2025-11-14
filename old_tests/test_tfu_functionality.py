#!/usr/bin/env python3
"""
Test TFU functionality - verify tfu is preserved through the booking flow.
"""

from fast_flights import (
    get_flights_from_tfs,
    create_return_flight_filter,
    get_return_flight_options,
)

print("=" * 80)
print("Testing TFU Functionality")
print("=" * 80)

# Frontier TFS with custom tfu parameter
frontier_tfs = "CBwQAhpnEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTEFTKgJGOTIENDE1OCIgCgNMQVMSCjIwMjUtMTEtMTgaA01DTyoCRjkyBDE4NzZqDAgCEggvbS8wZDZscHIHCAESA01DTxojEgoyMDI1LTExLTI1agcIARIDTUNPcgwIAhIIL20vMGQ2bHBAAUgBcAGCAQsI____________AZgBAQ"
frontier_tfu = "CnhDalJJWkhoRlNXcFlaSEpNV0ZWQlFrMXdjbWRDUnkwdExTMHRMUzB0ZVdsaVltTXlPRUZCUVVGQlIydFhNRnBqU1hoTVdqaEJFZzFHT1RReE5UaDhSamt4T0RjMkdnc0l5ZnNCRUFJYUExVlRSRGdjY01uN0FRPT0SAggAIgMKATA"

print("\nStep 1: Fetch outbound flights with custom tfu parameter")
print(f"TFS: {frontier_tfs[:60]}...")
print(f"TFU: {frontier_tfu[:60]}...")

try:
    result = get_flights_from_tfs(
        frontier_tfs,
        data_source='js',
        mode='common',
        tfu=frontier_tfu
    )

    if result and hasattr(result, 'best'):
        total_flights = len(result.best) + len(result.other)
        print(f"\n✅ SUCCESS: Fetched {len(result.best)} best + {len(result.other)} other = {total_flights} flights")

        # Verify tfu is stored in itineraries
        if result.best:
            first = result.best[0]
            print(f"\n✓ TFU stored in itinerary: {first.tfu[:60]}...")

            if first.tfu == frontier_tfu:
                print("✅ TFU matches the input parameter!")
            else:
                print(f"⚠️  TFU mismatch: expected {frontier_tfu[:30]}, got {first.tfu[:30]}")

            print(f"\nFirst flight details:")
            if first.flights:
                f = first.flights[0]
                print(f"  {f.airline} {f.flight_number}")
                print(f"  {first.departure_airport} → {first.arrival_airport}")
                print(f"  Departure: {f.departure_date[0]}-{f.departure_date[1]:02d}-{f.departure_date[2]:02d}")

        # Step 2: Create return flight filter
        print("\n" + "=" * 80)
        print("Step 2: Generate return flight TFS")
        print("=" * 80)

        selected = result.best[0]
        first_flight = selected.flights[0]

        return_tfs = create_return_flight_filter(
            outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
            outbound_from=selected.departure_airport,
            outbound_to=selected.arrival_airport,
            outbound_airline=first_flight.airline,
            outbound_flight_number=first_flight.flight_number,
            return_date="2025-11-25",
        )

        print(f"\n✓ Generated return TFS: {return_tfs[:60]}...")

        # Step 3: Fetch return flights with tfu from selected outbound
        print("\n" + "=" * 80)
        print("Step 3: Fetch return flights using tfu from selected outbound")
        print("=" * 80)

        print(f"\nPassing tfu from selected itinerary: {selected.tfu[:60]}...")

        try:
            return_options = get_return_flight_options(
                return_tfs,
                mode='common',
                tfu=selected.tfu  # Pass tfu from selected outbound flight
            )

            print(f"\n✅ SUCCESS: Fetched {len(return_options)} return flight options")

            if return_options:
                print("\nFirst 3 return flights:")
                for i, opt in enumerate(return_options[:3], 1):
                    print(f"  {i}. {opt.airline} {opt.flight_number}: ${opt.total_price:.2f}")
                    print(f"     {opt.departure_airport} → {opt.arrival_airport}")
                    print(f"     Departs: {opt.departure_time}, Duration: {opt.duration_minutes} min")

                print("\n✅ Complete TFU flow successful!")
                print("   1. Outbound flights fetched with custom tfu ✓")
                print("   2. TFU stored in each itinerary ✓")
                print("   3. TFU passed to return flight search ✓")
                print("   4. Return flights fetched successfully ✓")
            else:
                print("⚠️  0 return flights found")

        except Exception as e:
            print(f"❌ ERROR fetching return flights: {e}")
    else:
        print("⚠️  No results found")

except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("""
TFU Parameter Flow:
1. User provides custom tfu when fetching outbound flights
2. Each Itinerary object stores the tfu value in itinerary.tfu field
3. When user selects outbound flight, they access selected.tfu
4. User passes selected.tfu to get_return_flight_options()
5. Return flight search uses the same tfu value

This ensures tfu is preserved through the entire booking flow.
""")
