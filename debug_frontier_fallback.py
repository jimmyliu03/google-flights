#!/usr/bin/env python3
"""
Debug why Frontier fallback returns 0 flights.
"""

from fast_flights import get_flights_from_tfs

frontier_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJGOTIENDE1OGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBAggBmAEB"

print("Testing Frontier TFS with different data sources and modes")
print("=" * 80)

tests = [
    ("JS + common", 'js', 'common'),
    ("JS + fallback", 'js', 'fallback'),
    ("HTML + common", 'html', 'common'),
    ("HTML + fallback", 'html', 'fallback'),
]

for name, data_source, mode in tests:
    print(f"\n{name}:")
    print("-" * 80)

    try:
        result = get_flights_from_tfs(frontier_tfs, data_source=data_source, mode=mode)

        if data_source == 'js' and hasattr(result, 'best'):
            print(f"  Result type: DecodedResult")
            print(f"  Best: {len(result.best)}")
            print(f"  Other: {len(result.other)}")
            print(f"  Total: {len(result.best) + len(result.other)}")
        elif data_source == 'html' and hasattr(result, 'flights'):
            print(f"  Result type: Result (HTML)")
            print(f"  Flights: {len(result.flights)}")
        else:
            print(f"  Result: {result}")

    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        print(f"  ERROR: {error_msg}")

print("\n" + "=" * 80)
print("Checking if 'fallback' mode actually triggers Playwright fallback...")
print("=" * 80)
print("""
The 'fallback' mode tries:
1. Direct HTTP fetch (primp client)
2. If that fails, falls back to Playwright serverless

For Frontier, even though mode='fallback', the HTTP fetch succeeds
(returns a page), but the page has no flight data because it needs
JavaScript execution to load flights.

The fallback only triggers if the HTTP request FAILS, not if the
page loads but has empty data.
""")
