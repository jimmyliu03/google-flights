#!/usr/bin/env python3
"""
Test return flight TFS with two sections (top and other returning flights).
"""

from fast_flights import get_return_flight_options, decode_return_flight_tfs

# TFS with multi-leg outbound (SFO->LAS->MCO) and return flight search
# This should show "top returning flights" and "other returning flights"
return_tfs = "CBwQAhpnEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTEFTKgJGOTIENDE1OCIgCgNMQVMSCjIwMjUtMTEtMTgaA01DTyoCRjkyBDE4NzZqDAgCEggvbS8wZDZscHIHCAESA01DTxojEgoyMDI1LTExLTI1agcIARIDTUNPcgwIAhIIL20vMGQ2bHBAAUgBcAGCAQsI____________AZgBAQ"

print("=" * 80)
print("Testing Return Flight with Two Sections (Top + Other)")
print("=" * 80)

# First, decode the TFS to understand the search
print("\n1. Decoding TFS to see outbound selection...")
print("-" * 80)
try:
    decoded = decode_return_flight_tfs(return_tfs)
    print(f"Outbound: {decoded['outbound']['airline']} {decoded['outbound']['flight_number']}")
    print(f"  Route: {decoded['outbound']['from_airport']} → {decoded['outbound']['to_airport']}")
    print(f"  Date: {decoded['outbound']['date']}")
    print(f"\nReturn search date: {decoded.get('return', {}).get('date', 'N/A')}")
except Exception as e:
    print(f"Error decoding: {e}")

# Test with get_return_flight_options
print("\n2. Fetching return flight options...")
print("-" * 80)
try:
    options = get_return_flight_options(return_tfs)

    print(f"\n✓ Successfully fetched {len(options)} return flight options")

    # Display top 15
    print("\nReturn Flight Options:")
    print("-" * 80)

    for i, option in enumerate(options[:15], 1):
        print(f"\n{i}. {option.airline} {option.flight_number}")
        print(f"   Route: {option.departure_airport} → {option.arrival_airport}")
        if option.departure_date:
            print(f"   Date: {option.departure_date}")
        if option.departure_time:
            print(f"   Departure: {option.departure_time}")
        if option.arrival_time:
            print(f"   Arrival: {option.arrival_time}")
        print(f"   Duration: {option.duration_minutes} min ({option.duration_minutes // 60}h {option.duration_minutes % 60}m)")
        print(f"   Stops: {option.stops}")
        if option.aircraft:
            print(f"   Aircraft: {option.aircraft}")
        print(f"   Price: ${option.total_price:.2f} {option.currency}")

    if len(options) > 15:
        print(f"\n... and {len(options) - 15} more options")

    print("\n" + "=" * 80)
    print(f"✓ SUCCESS: Fetched {len(options)} return flights")
    print("=" * 80)

except Exception as e:
    print(f"\n⚠ Error: {e}")
    import traceback
    traceback.print_exc()

# Test raw JS data extraction to see structure
print("\n3. Testing raw JS data structure...")
print("-" * 80)
try:
    from fast_flights import get_flights_from_tfs
    result = get_flights_from_tfs(return_tfs, data_source='js')

    if result and hasattr(result, 'best'):
        print(f"Best/Top flights: {len(result.best)}")
        print(f"Other flights: {len(result.other)}")
        print(f"Total: {len(result.best) + len(result.other)}")

        if len(result.best) > 0:
            print("\nFirst 'Best' flight:")
            first = result.best[0]
            if first.flights:
                print(f"  {first.flights[0].airline_name} {first.flights[0].flight_number}")

        if len(result.other) > 0:
            print("\nFirst 'Other' flight:")
            first = result.other[0]
            if first.flights:
                print(f"  {first.flights[0].airline_name} {first.flights[0].flight_number}")
    else:
        print("No DecodedResult structure found")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
