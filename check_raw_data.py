#!/usr/bin/env python3
"""
Check what's in the raw JS data when fetching return flights.
"""

from fast_flights import get_flights_from_tfs

# Known-good UA TFS
ua_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBBAgBEAKYAQE"

# Frontier TFS (dynamically generated)
f9_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJGOTIENDE1OGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBAggBmAEB"

print("Comparing UA TFS vs Frontier TFS with mode='common'")
print("=" * 80)

for name, tfs in [("UA (known-good)", ua_tfs), ("Frontier (dynamic)", f9_tfs)]:
    print(f"\n{name}:")
    print("-" * 80)

    result = get_flights_from_tfs(tfs, data_source='js', mode='common')

    if result and hasattr(result, 'raw'):
        print(f"Raw data exists: {len(result.raw)} elements")
        print(f"Raw[2] (best flights): {result.raw[2]}")
        print(f"Raw[3] (other flights): {result.raw[3]}")

        if result.raw[2] is not None:
            print(f"  Raw[2] has {len(result.raw[2])} items")
            if len(result.raw[2]) > 0:
                print(f"  Raw[2][0] has {len(result.raw[2][0])} items")

        if result.raw[3] is not None:
            print(f"  Raw[3] has {len(result.raw[3])} items")
            if len(result.raw[3]) > 0:
                print(f"  Raw[3][0] has {len(result.raw[3][0])} items")

        print(f"\nResult:")
        print(f"  Best: {len(result.best)}")
        print(f"  Other: {len(result.other)}")
