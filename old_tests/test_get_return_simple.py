#!/usr/bin/env python3
"""
Simple test of get_return_flight_options() with a known-good TFS string.
"""

from fast_flights import get_return_flight_options

# Known-good return flight TFS string (UA2230 selected, searching for return flights)
return_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBBAgBEAKYAQE"

print("=" * 80)
print("Testing get_return_flight_options() with known-good TFS")
print("=" * 80)

print(f"\nReturn Flight TFS: {return_tfs[:50]}...")
print("\nCalling get_return_flight_options()...")

options = get_return_flight_options(return_tfs)

print(f"\n✓ Successfully fetched {len(options)} return flight options")
print("\nTop 10 Return Flights:")
print("-" * 80)

for i, option in enumerate(options[:10], 1):
    print(f"\n{i}. {option.airline} {option.flight_number}")
    print(f"   Route: {option.departure_airport} → {option.arrival_airport}")
    print(f"   Date: {option.departure_date}")
    print(f"   Departure: {option.departure_time}")
    print(f"   Arrival: {option.arrival_time}")
    print(f"   Duration: {option.duration_minutes} min ({option.duration_minutes // 60}h {option.duration_minutes % 60}m)")
    print(f"   Stops: {option.stops}")
    if option.aircraft:
        print(f"   Aircraft: {option.aircraft}")
    print(f"   Total Price: ${option.total_price:.2f} {option.currency}")

if len(options) > 10:
    print(f"\n... and {len(options) - 10} more return flight options")

print("\n" + "=" * 80)
print("✓ SUCCESS: get_return_flight_options() works with JS data source!")
print("=" * 80)
