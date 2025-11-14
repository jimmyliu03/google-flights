#!/usr/bin/env python3
"""
Test return flight TFS that has both "top returning flights" and "other returning flights" sections.
This is a roundtrip SFO->LAS->MCO, returning MCO->SFO with flights shown in two categories.
"""

from fast_flights import get_return_flight_options, decode_return_flight_tfs, get_flights_from_tfs

# Return flight TFS with two sections
tfs = "CBwQAhpnEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTEFTKgJGOTIENDE1OCIgCgNMQVMSCjIwMjUtMTEtMTgaA01DTyoCRjkyBDE4NzZqDAgCEggvbS8wZDZscHIHCAESA01DTxojEgoyMDI1LTExLTI1agcIARIDTUNPcgwIAhIIL20vMGQ2bHBAAUgBcAGCAQsI____________AZgBAQ"

print("=" * 80)
print("Test: Return Flights with 'Top' and 'Other' Sections")
print("=" * 80)

print("\n1. Decode TFS to see outbound selection")
print("-" * 80)
try:
    decoded = decode_return_flight_tfs(tfs)
    outbound = decoded.get('outbound', {})
    print(f"Outbound: {outbound.get('airline', 'N/A')} {outbound.get('flight_number', 'N/A')}")
    print(f"  From: {outbound.get('from_airport', 'N/A')}")
    print(f"  To: {outbound.get('to_airport', 'N/A')}")
    print(f"  Date: {outbound.get('date', 'N/A')}")
except Exception as e:
    print(f"Error: {e}")

print("\n2. Check raw JS data structure")
print("-" * 80)
try:
    result = get_flights_from_tfs(tfs, data_source='js')

    if result and hasattr(result, 'best'):
        print(f"✓ JS data parsed successfully")
        print(f"\n  'Top/Best' returning flights: {len(result.best)}")
        print(f"  'Other' returning flights: {len(result.other)}")
        print(f"  Total: {len(result.best) + len(result.other)}")

        if len(result.best) > 0:
            print(f"\n  First 'Top' flight:")
            first = result.best[0]
            if first.flights and len(first.flights) > 0:
                f = first.flights[0]
                print(f"    {f.airline_name} {f.flight_number}")
                print(f"    {first.departure_airport} → {first.arrival_airport}")
                if first.itinerary_summary:
                    print(f"    Price: ${first.itinerary_summary.price:.2f}")

        if len(result.other) > 0:
            print(f"\n  First 'Other' flight:")
            first = result.other[0]
            if first.flights and len(first.flights) > 0:
                f = first.flights[0]
                print(f"    {f.airline_name} {f.flight_number}")
                print(f"    {first.departure_airport} → {first.arrival_airport}")
                if first.itinerary_summary:
                    print(f"    Price: ${first.itinerary_summary.price:.2f}")
    else:
        print("⚠ No JS data structure found")

except Exception as e:
    print(f"⚠ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Test get_return_flight_options() combines both sections")
print("-" * 80)
try:
    options = get_return_flight_options(tfs)

    print(f"\n✓ get_return_flight_options() returned {len(options)} flights")
    print("\nAll Return Flight Options (Top + Other combined):")
    print("-" * 80)

    for i, option in enumerate(options, 1):
        print(f"\n{i}. {option.airline} {option.flight_number}")
        print(f"   {option.departure_airport} → {option.arrival_airport}")
        if option.departure_time and option.arrival_time:
            print(f"   {option.departure_time} - {option.arrival_time}")
        print(f"   Duration: {option.duration_minutes // 60}h {option.duration_minutes % 60}m")
        print(f"   Stops: {option.stops}")
        if option.aircraft:
            print(f"   Aircraft: {option.aircraft}")
        print(f"   Price: ${option.total_price:.2f}")

    print("\n" + "=" * 80)
    print(f"✓ SUCCESS: Both sections properly combined ({len(options)} total)")
    print("=" * 80)

except Exception as e:
    print(f"\n⚠ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 80)
    print("⚠ FAILED: get_return_flight_options() did not work correctly")
    print("=" * 80)

print()
