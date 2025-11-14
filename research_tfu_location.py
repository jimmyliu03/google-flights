#!/usr/bin/env python3
"""
Research where tfu is stored in the JavaScript data structure.
"""

from fast_flights import get_flights_from_tfs
import json

# Frontier TFS with tfu parameter
tfs_with_tfu = "CBwQAhpnEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTEFTKgJGOTIENDE1OCIgCgNMQVMSCjIwMjUtMTEtMTgaA01DTyoCRjkyBDE4NzZqDAgCEggvbS8wZDZscHIHCAESA01DTxojEgoyMDI1LTExLTI1agcIARIDTUNPcgwIAhIIL20vMGQ2bHBAAUgBcAGCAQsI____________AZgBAQ"
tfu = "CnhDalJJWkhoRlNXcFlaSEpNV0ZWQlFrMXdjbWRDUnkwdExTMHRMUzB0ZVdsaVltTXlPRUZCUVVGQlIydFhNRnBqU1hoTVdqaEJFZzFHT1RReE5UaDhSamt4T0RjMkdnc0l5ZnNCRUFJYUExVlRSRGdjY01uN0FRPT0SAggAIgMKATA"

print("=" * 80)
print("Researching TFU Location in JavaScript Data Structure")
print("=" * 80)

print(f"\nTFS: {tfs_with_tfu[:60]}...")
print(f"TFU: {tfu[:60]}...")

# Fetch with JS data source
result = get_flights_from_tfs(tfs_with_tfu, data_source='js', mode='common')

if result and hasattr(result, 'raw'):
    print(f"\nRaw data has {len(result.raw)} elements")

    # Search for tfu-like strings in raw data
    print("\nSearching for tfu or similar base64 strings in raw data...")

    def search_nested(data, path="", depth=0, max_depth=5):
        """Recursively search for tfu-like strings"""
        if depth > max_depth:
            return

        if isinstance(data, str):
            # Check if it looks like the tfu string
            if len(data) > 50 and data.startswith("C"):
                if tfu in data or data in tfu or data[:30] == tfu[:30]:
                    print(f"  Found at {path}: {data[:80]}...")

        elif isinstance(data, list):
            for i, item in enumerate(data):
                search_nested(item, f"{path}[{i}]", depth + 1, max_depth)

        elif isinstance(data, dict):
            for key, value in data.items():
                search_nested(value, f"{path}.{key}", depth + 1, max_depth)

    search_nested(result.raw, "raw")

    # Print structure of first itinerary
    if result.best and len(result.best) > 0:
        print("\nFirst 'best' itinerary structure:")
        first = result.best[0]
        print(f"  Attributes: {[attr for attr in dir(first) if not attr.startswith('_')]}")

        # Check raw_itinerary
        if hasattr(first, 'raw') and first.raw:
            print(f"\n  Raw itinerary data (first 10 elements):")
            for i, elem in enumerate(first.raw[:10]):
                if isinstance(elem, str) and len(elem) > 20:
                    print(f"    [{i}]: {type(elem).__name__} - {elem[:80]}...")
                elif isinstance(elem, list):
                    print(f"    [{i}]: list with {len(elem)} items")
                else:
                    print(f"    [{i}]: {type(elem).__name__} - {elem}")

    # Check other itineraries
    if result.other and len(result.other) > 0:
        print("\nFirst 'other' itinerary structure:")
        first = result.other[0]

        if hasattr(first, 'raw') and first.raw:
            print(f"  Raw itinerary data (first 10 elements):")
            for i, elem in enumerate(first.raw[:10]):
                if isinstance(elem, str) and len(elem) > 20:
                    print(f"    [{i}]: {type(elem).__name__} - {elem[:80]}...")
                elif isinstance(elem, list):
                    print(f"    [{i}]: list with {len(elem)} items")
                else:
                    print(f"    [{i}]: {type(elem).__name__} - {elem}")

print("\n" + "=" * 80)
print("Checking if tfu is in URL/request parameters vs data structure")
print("=" * 80)
print("""
TFU may be:
1. Passed as URL parameter (?tfu=...) but not stored in response data
2. Stored somewhere in the nested list structure we haven't found yet
3. Generated client-side and not included in server response

Next step: Check if tfu needs to be extracted from the original URL
rather than from the response data.
""")
