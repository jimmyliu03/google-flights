#!/usr/bin/env python3
"""
Test which modes work for Frontier return flights.
"""

from fast_flights import get_return_flight_options

# Frontier return flight TFS (generated dynamically from test)
frontier_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJGOTIENDE1OGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBAggBmAEB"

print("=" * 80)
print("Testing Frontier Return Flight TFS with Different Modes")
print("=" * 80)

modes_to_test = [
    ('common', 'Direct HTTP scraping'),
    ('fallback', 'Try common, fall back to Playwright'),
]

for mode, description in modes_to_test:
    print(f"\nMode: {mode}")
    print(f"Description: {description}")
    print("-" * 80)

    try:
        options = get_return_flight_options(frontier_tfs, mode=mode)

        if len(options) > 0:
            print(f"✅ SUCCESS: Got {len(options)} return flights")
            print(f"\nSample flights:")
            for i, opt in enumerate(options[:3], 1):
                print(f"  {i}. {opt.airline} {opt.flight_number}: ${opt.total_price:.2f}")
        else:
            print(f"⚠️  FAILED: Got 0 flights")

    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("""
For Frontier return flights:
- mode='common': Returns 0 flights (page needs JS rendering)
- mode='fallback': Should work (falls back to Playwright if common fails)
- mode='force-fallback': Should work (always uses Playwright)
- mode='local': Should work (uses local Playwright, requires installation)
- mode='bright-data': Should work (uses Bright Data, requires API key)
""")
