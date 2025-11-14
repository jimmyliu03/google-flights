#!/usr/bin/env python3
"""
Test the Frontier TFS with all possible mode and data_source combinations.
"""

from fast_flights import get_flights_from_tfs, get_return_flight_options

# Frontier TFS - multi-city with connecting flights
frontier_tfs = "CBwQAhpnEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTEFTKgJGOTIENDE1OCIgCgNMQVMSCjIwMjUtMTEtMTgaA01DTyoCRjkyBDE4NzZqDAgCEggvbS8wZDZscHIHCAESA01DTxojEgoyMDI1LTExLTI1agcIARIDTUNPcgwIAhIIL20vMGQ2bHBAAUgBcAGCAQsI____________AZgBAQ"

print("=" * 80)
print("Testing Frontier TFS with All Mode/DataSource Combinations")
print("=" * 80)

modes = ['common', 'fallback', 'force-fallback']
data_sources = ['js', 'html']

results = []

for mode in modes:
    for data_source in data_sources:
        test_name = f"{data_source.upper()} + {mode}"
        print(f"\n{test_name}:")
        print("-" * 80)

        try:
            result = get_flights_from_tfs(frontier_tfs, data_source=data_source, mode=mode)

            if data_source == 'js' and hasattr(result, 'best'):
                total = len(result.best) + len(result.other)
                print(f"✓ DecodedResult: {len(result.best)} best, {len(result.other)} other = {total} total")

                if total > 0:
                    print(f"✅ SUCCESS - {total} flights found")
                    results.append((test_name, "✅ SUCCESS", total))

                    # Show sample
                    all_flights = result.best + result.other
                    if all_flights and all_flights[0].flights:
                        f = all_flights[0].flights[0]
                        print(f"  Sample: {f.airline_name} {f.flight_number}")
                else:
                    print(f"⚠️  0 flights")
                    results.append((test_name, "⚠️ 0 flights", 0))

            elif data_source == 'html' and hasattr(result, 'flights'):
                total = len(result.flights)
                print(f"✓ Result (HTML): {total} flights")

                if total > 0:
                    print(f"✅ SUCCESS - {total} flights found")
                    results.append((test_name, "✅ SUCCESS", total))
                    print(f"  Sample: {result.flights[0].name}")
                else:
                    print(f"⚠️  0 flights")
                    results.append((test_name, "⚠️ 0 flights", 0))
            else:
                print(f"⚠️  Unexpected result type: {type(result)}")
                results.append((test_name, "⚠️ Unexpected result", 0))

        except Exception as e:
            error_msg = str(e)[:150]
            print(f"❌ ERROR: {error_msg}")
            results.append((test_name, f"❌ ERROR", 0))

print("\n" + "=" * 80)
print("SUMMARY - Settings that Work for Frontier")
print("=" * 80)

working = [r for r in results if r[1] == "✅ SUCCESS"]
not_working = [r for r in results if r[1] != "✅ SUCCESS"]

if working:
    print("\n✅ WORKING COMBINATIONS:")
    for name, status, count in working:
        print(f"  • {name}: {count} flights")
else:
    print("\n⚠️  NO WORKING COMBINATIONS FOUND")

if not_working:
    print("\n❌ NOT WORKING:")
    for name, status, count in not_working:
        print(f"  • {name}: {status}")

print("\n" + "=" * 80)
print("Testing get_return_flight_options() with working settings")
print("=" * 80)

if working:
    best_combo = working[0]
    print(f"\nUsing: {best_combo[0]}")
    # Extract mode from the combo name
    if "force-fallback" in best_combo[0]:
        mode = "force-fallback"
    elif "fallback" in best_combo[0]:
        mode = "fallback"
    else:
        mode = "common"

    try:
        options = get_return_flight_options(frontier_tfs, mode=mode)
        print(f"✅ get_return_flight_options() returned {len(options)} flights")

        for i, opt in enumerate(options[:3], 1):
            print(f"  {i}. {opt.airline} {opt.flight_number}: ${opt.total_price:.2f}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
else:
    print("Cannot test - no working combinations found")

print()
