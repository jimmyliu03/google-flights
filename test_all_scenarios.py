#!/usr/bin/env python3
"""Test exclude_basic_economy for both initial search and return flight selection"""

import base64
from fast_flights import create_filter, Passengers, FlightData, create_return_flight_filter, get_flights_from_filter, get_flights_from_tfs

print("=" * 80)
print("PART 1: One-Way Flight Search")
print("=" * 80)

# Expected TFS values from user
expected_oneway_exclude = "CBwQAhoeEgoyMDI1LTEyLTEwagcIARIDU0ZPcgcIARIDTUNPQAFIAXABggELCP___________wGYAQLIAQE"
expected_oneway_include = "CBwQAhoeEgoyMDI1LTEyLTEwagcIARIDU0ZPcgcIARIDTUNPQAFIAXABggELCP___________wGYAQLIAQA"

print("\nTesting one-way flight (SFO → MCO, exclude_basic_economy=True):")
tfs_oneway_exclude = create_filter(
    flight_data=[
        FlightData(date="2025-12-10", from_airport="SFO", to_airport="MCO"),
    ],
    trip="one-way",
    passengers=Passengers(adults=1),
    seat="economy",
    exclude_basic_economy=True
)
oneway_exclude_b64 = tfs_oneway_exclude.as_b64().decode('utf-8')

print(f"Expected: {expected_oneway_exclude}")
print(f"Actual:   {oneway_exclude_b64}")
print(f"✓ Match: {oneway_exclude_b64 == expected_oneway_exclude}" if oneway_exclude_b64 == expected_oneway_exclude else f"✗ MISMATCH")

# Decode and verify
decoded_oneway_exclude = base64.urlsafe_b64decode(oneway_exclude_b64 + '===')
expected_decoded_exclude = base64.urlsafe_b64decode(expected_oneway_exclude + '===')
print(f"Expected hex: {expected_decoded_exclude.hex()}")
print(f"Actual hex:   {decoded_oneway_exclude.hex()}")

# Verify TFS returns flights
print("\nVerifying TFS returns flights...")
oneway_exclude_valid = False
try:
    result = get_flights_from_tfs(oneway_exclude_b64, data_source='js', mode='fallback')
    if result and hasattr(result, 'best') and len(result.best) > 0:
        print(f"✓ TFS valid: Found {len(result.best)} best flights")
        oneway_exclude_valid = True
    else:
        print("✗ TFS returned no flights")
except Exception as e:
    print(f"✗ TFS validation failed: {e}")

print("\nTesting one-way flight (SFO → MCO, exclude_basic_economy=False):")
tfs_oneway_include = create_filter(
    flight_data=[
        FlightData(date="2025-12-10", from_airport="SFO", to_airport="MCO"),
    ],
    trip="one-way",
    passengers=Passengers(adults=1),
    seat="economy",
    exclude_basic_economy=False
)
oneway_include_b64 = tfs_oneway_include.as_b64().decode('utf-8')

print(f"Expected: {expected_oneway_include}")
print(f"Actual:   {oneway_include_b64}")
print(f"✓ Match: {oneway_include_b64 == expected_oneway_include}" if oneway_include_b64 == expected_oneway_include else f"✗ MISMATCH")

# Decode and verify
decoded_oneway_include = base64.urlsafe_b64decode(oneway_include_b64 + '===')
expected_decoded_include = base64.urlsafe_b64decode(expected_oneway_include + '===')
print(f"Expected hex: {expected_decoded_include.hex()}")
print(f"Actual hex:   {decoded_oneway_include.hex()}")

# Verify TFS returns flights
print("\nVerifying TFS returns flights...")
oneway_include_valid = False
try:
    result = get_flights_from_tfs(oneway_include_b64, data_source='js', mode='fallback')
    if result and hasattr(result, 'best') and len(result.best) > 0:
        print(f"✓ TFS valid: Found {len(result.best)} best flights")
        oneway_include_valid = True
    else:
        print("✗ TFS returned no flights")
except Exception as e:
    print(f"✗ TFS validation failed: {e}")

print("\n" + "=" * 80)
print("PART 2: Initial Roundtrip Search (Outbound + Return)")
print("=" * 80)

# Test data from user's URLs
expected_with_basic = "CBwQAhoeEgoyMDI1LTEyLTEwagcIARIDU0ZPcgcIARIDTUNPGh4SCjIwMjUtMTItMTRqBwgBEgNNQ09yBwgBEgNTRk9AAUgBcAGCAQsI____________AZgBAQ"
expected_without_basic = "CBwQAhoeEgoyMDI1LTEyLTEwagcIARIDU0ZPcgcIARIDTUNPGh4SCjIwMjUtMTItMTRqBwgBEgNNQ09yBwgBEgNTRk9AAUgBcAGCAQsI____________AZgBAcgBAQ"

print("\nTesting WITH basic economy (exclude_basic_economy=False):")
tfs_with = create_filter(
    flight_data=[
        FlightData(date="2025-12-10", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-12-14", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
    exclude_basic_economy=False
)
actual_with = tfs_with.as_b64().decode('utf-8')

print(f"Expected: {expected_with_basic}")
print(f"Actual:   {actual_with}")
print(f"✓ Match: {actual_with == expected_with_basic}" if actual_with == expected_with_basic else f"✗ MISMATCH")

# Decode both to see hex difference
expected_bytes_with = base64.urlsafe_b64decode(expected_with_basic + '===')
actual_bytes_with = base64.urlsafe_b64decode(actual_with + '===')
print(f"Expected hex: {expected_bytes_with.hex()}")
print(f"Actual hex:   {actual_bytes_with.hex()}")

# Verify TFS returns flights
print("\nVerifying TFS returns flights...")
roundtrip_with_valid = False
try:
    result = get_flights_from_tfs(actual_with, data_source='js', mode='fallback')
    if result and hasattr(result, 'best') and len(result.best) > 0:
        print(f"✓ TFS valid: Found {len(result.best)} best flights")
        roundtrip_with_valid = True
    else:
        print("✗ TFS returned no flights")
except Exception as e:
    print(f"✗ TFS validation failed: {e}")
print()

print("Testing WITHOUT basic economy (exclude_basic_economy=True):")
tfs_without = create_filter(
    flight_data=[
        FlightData(date="2025-12-10", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-12-14", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
    exclude_basic_economy=True
)
actual_without = tfs_without.as_b64().decode('utf-8')

print(f"Expected: {expected_without_basic}")
print(f"Actual:   {actual_without}")
print(f"✓ Match: {actual_without == expected_without_basic}" if actual_without == expected_without_basic else f"✗ MISMATCH")

# Decode both to see hex difference
expected_bytes_without = base64.urlsafe_b64decode(expected_without_basic + '===')
actual_bytes_without = base64.urlsafe_b64decode(actual_without + '===')
print(f"Expected hex: {expected_bytes_without.hex()}")
print(f"Actual hex:   {actual_bytes_without.hex()}")

# Verify TFS returns flights
print("\nVerifying TFS returns flights...")
roundtrip_without_valid = False
try:
    result = get_flights_from_tfs(actual_without, data_source='js', mode='fallback')
    if result and hasattr(result, 'best') and len(result.best) > 0:
        print(f"✓ TFS valid: Found {len(result.best)} best flights")
        roundtrip_without_valid = True
    else:
        print("✗ TFS returned no flights")
except Exception as e:
    print(f"✗ TFS validation failed: {e}")

print("\n" + "=" * 80)
print("PART 3: Fetching Real Outbound Flights")
print("=" * 80)

print("\nFetching real flights WITH basic economy (exclude_basic_economy=False)...")
try:
    result_with = get_flights_from_filter(tfs_with, data_source='js', mode='fallback')
    if result_with and hasattr(result_with, 'best') and len(result_with.best) > 0:
        first_flight_with = result_with.best[0]
        print(f"✓ Found {len(result_with.best)} best flights")
        print(f"  First flight: {first_flight_with.flights[0].airline if first_flight_with.flights else 'N/A'} "
              f"{first_flight_with.flights[0].flight_number if first_flight_with.flights else 'N/A'}")
        print(f"  Price: {first_flight_with.itinerary_summary.currency if first_flight_with.itinerary_summary else ''}"
              f"{first_flight_with.itinerary_summary.price if first_flight_with.itinerary_summary else 'N/A'}")
    else:
        print("✗ No flights found")
        first_flight_with = None
except Exception as e:
    print(f"✗ Error fetching flights: {e}")
    first_flight_with = None

print("\nFetching real flights WITHOUT basic economy (exclude_basic_economy=True)...")
try:
    result_without = get_flights_from_filter(tfs_without, data_source='js', mode='fallback')
    if result_without and hasattr(result_without, 'best') and len(result_without.best) > 0:
        first_flight_without = result_without.best[0]
        print(f"✓ Found {len(result_without.best)} best flights")
        print(f"  First flight: {first_flight_without.flights[0].airline if first_flight_without.flights else 'N/A'} "
              f"{first_flight_without.flights[0].flight_number if first_flight_without.flights else 'N/A'}")
        print(f"  Price: {first_flight_without.itinerary_summary.currency if first_flight_without.itinerary_summary else ''}"
              f"{first_flight_without.itinerary_summary.price if first_flight_without.itinerary_summary else 'N/A'}")
    else:
        print("✗ No flights found")
        first_flight_without = None
except Exception as e:
    print(f"✗ Error fetching flights: {e}")
    first_flight_without = None

print("\n" + "=" * 80)
print("PART 4: Return Flight Selection (Using Real Outbound Flight)")
print("=" * 80)

# Test with basic economy (using real flight data)
if first_flight_with and first_flight_with.flights and len(first_flight_with.flights) > 0:
    outbound_flight = first_flight_with.flights[0]

    # Build connecting_segments for multi-leg flights
    connecting_segments = None
    if len(first_flight_with.flights) > 1:
        connecting_segments = []
        for i in range(1, len(first_flight_with.flights)):
            segment = first_flight_with.flights[i]
            to_airport = (first_flight_with.flights[i+1].departure_airport
                         if i+1 < len(first_flight_with.flights)
                         else first_flight_with.arrival_airport)
            connecting_segments.append({
                'from': segment.departure_airport,
                'to': to_airport,
                'airline': segment.airline,
                'flight_number': segment.flight_number,
                'date': f"{segment.departure_date[0]}-{segment.departure_date[1]:02d}-{segment.departure_date[2]:02d}",
            })

    print(f"\nUsing real outbound flight (WITH basic economy):")
    print(f"  Airline: {outbound_flight.airline}")
    print(f"  Flight Number: {outbound_flight.flight_number}")
    print(f"  Route: SFO → MCO")
    print(f"  Date: 2025-12-10")
    if connecting_segments:
        print(f"  Connecting flight: {len(first_flight_with.flights)} segments")
        for i, seg in enumerate(connecting_segments, 1):
            print(f"    Segment {i+1}: {seg['from']} → {seg['to']} ({seg['airline']} {seg['flight_number']})")
    else:
        print(f"  Direct flight")

    return_tfs_with = create_return_flight_filter(
        outbound_date="2025-12-10",
        outbound_from="SFO",
        outbound_to="MCO",
        outbound_airline=outbound_flight.airline,
        outbound_flight_number=outbound_flight.flight_number,
        connecting_segments=connecting_segments,
        return_date="2025-12-14",
        seat="economy",  # Must match initial search seat class
        exclude_basic_economy=False  # Should match initial search setting
    )
    
    print(f"\nReturn TFS (with basic): {return_tfs_with[:80]}...")
    print(f"URL: https://www.google.com/travel/flights?tfs={return_tfs_with}")
    
    # Decode and check for field_25
    decoded_with = base64.urlsafe_b64decode(return_tfs_with + '===')
    has_field_25_with = b'\xc8\x01\x01' in decoded_with
    print(f"Field 25 (exclude) present: {has_field_25_with}")
    print(f"✓ Correct (should NOT have field 25)" if not has_field_25_with else f"✗ INCORRECT (should NOT have field 25)")

    # Verify return TFS returns flights
    print("\nVerifying return TFS returns flights...")
    return_with_valid = False
    try:
        result = get_flights_from_tfs(return_tfs_with, data_source='js', mode='fallback')
        if result and hasattr(result, 'best'):
            total_flights = len(result.best) + (len(result.other) if hasattr(result, 'other') else 0)
            if total_flights > 0:
                print(f"✓ Return TFS valid: Found {len(result.best)} best + {len(result.other) if hasattr(result, 'other') else 0} other flights")
                return_with_valid = True
            else:
                print("✗ Return TFS returned no flights")
        else:
            print("✗ Return TFS returned no flights")
    except Exception as e:
        print(f"✗ Return TFS validation failed: {e}")
else:
    print("\n✗ Skipping return flight test (WITH basic) - no outbound flight data available")
    has_field_25_with = None
    return_with_valid = False

print()

# Test without basic economy (using real flight data)
if first_flight_without and first_flight_without.flights and len(first_flight_without.flights) > 0:
    outbound_flight = first_flight_without.flights[0]

    # Build connecting_segments for multi-leg flights
    connecting_segments = None
    if len(first_flight_without.flights) > 1:
        connecting_segments = []
        for i in range(1, len(first_flight_without.flights)):
            segment = first_flight_without.flights[i]
            to_airport = (first_flight_without.flights[i+1].departure_airport
                         if i+1 < len(first_flight_without.flights)
                         else first_flight_without.arrival_airport)
            connecting_segments.append({
                'from': segment.departure_airport,
                'to': to_airport,
                'airline': segment.airline,
                'flight_number': segment.flight_number,
                'date': f"{segment.departure_date[0]}-{segment.departure_date[1]:02d}-{segment.departure_date[2]:02d}",
            })

    print(f"Using real outbound flight (WITHOUT basic economy):")
    print(f"  Airline: {outbound_flight.airline}")
    print(f"  Flight Number: {outbound_flight.flight_number}")
    print(f"  Route: SFO → MCO")
    print(f"  Date: 2025-12-10")
    if connecting_segments:
        print(f"  Connecting flight: {len(first_flight_without.flights)} segments")
        for i, seg in enumerate(connecting_segments, 1):
            print(f"    Segment {i+1}: {seg['from']} → {seg['to']} ({seg['airline']} {seg['flight_number']})")
    else:
        print(f"  Direct flight")

    return_tfs_without = create_return_flight_filter(
        outbound_date="2025-12-10",
        outbound_from="SFO",
        outbound_to="MCO",
        outbound_airline=outbound_flight.airline,
        outbound_flight_number=outbound_flight.flight_number,
        connecting_segments=connecting_segments,
        return_date="2025-12-14",
        seat="economy",  # Must match initial search seat class
        exclude_basic_economy=True  # Should match initial search setting
    )
    
    print(f"\nReturn TFS (exclude basic): {return_tfs_without[:80]}...")
    print(f"URL: https://www.google.com/travel/flights?tfs={return_tfs_without}")
    
    # Decode and check for field_25
    decoded_without = base64.urlsafe_b64decode(return_tfs_without + '===')
    has_field_25_without = b'\xc8\x01\x01' in decoded_without
    print(f"Field 25 (exclude) present: {has_field_25_without}")
    print(f"✓ Correct (SHOULD have field 25)" if has_field_25_without else f"✗ INCORRECT (SHOULD have field 25)")

    # Verify return TFS returns flights
    print("\nVerifying return TFS returns flights...")
    return_without_valid = False
    try:
        result = get_flights_from_tfs(return_tfs_without, data_source='js', mode='fallback')
        if result and hasattr(result, 'best'):
            total_flights = len(result.best) + (len(result.other) if hasattr(result, 'other') else 0)
            if total_flights > 0:
                print(f"✓ Return TFS valid: Found {len(result.best)} best + {len(result.other) if hasattr(result, 'other') else 0} other flights")
                return_without_valid = True
            else:
                print("✗ Return TFS returned no flights")
        else:
            print("✗ Return TFS returned no flights")
    except Exception as e:
        print(f"✗ Return TFS validation failed: {e}")
else:
    print("\n✗ Skipping return flight test (WITHOUT basic) - no outbound flight data available")
    has_field_25_without = None
    return_without_valid = False

print("\n" + "=" * 80)
print("PART 5: Business Class Roundtrip (SFO → IST)")
print("=" * 80)

print("\nCreating business class roundtrip filter (SFO → IST, Feb 5-18, 2026)...")
tfs_business = create_filter(
    flight_data=[
        FlightData(date="2026-02-05", from_airport="SFO", to_airport="IST"),
        FlightData(date="2026-02-18", from_airport="IST", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="business",
    exclude_basic_economy=False
)
business_b64 = tfs_business.as_b64().decode('utf-8')
print(f"TFS: {business_b64}")
print(f"URL: https://www.google.com/travel/flights?tfs={business_b64}")

print("\nFetching real business class flights...")
business_flight_found = False
business_return_success = False
try:
    result_business = get_flights_from_filter(tfs_business, data_source='js', mode='fallback')
    if result_business and hasattr(result_business, 'best') and len(result_business.best) > 0:
        first_business = result_business.best[0]
        print(f"✓ Found {len(result_business.best)} best flights")
        print(f"  First outbound: {first_business.flights[0].airline if first_business.flights else 'N/A'} "
              f"{first_business.flights[0].flight_number if first_business.flights else 'N/A'}")
        print(f"  Route: {first_business.departure_airport} → {first_business.arrival_airport}")
        print(f"  Segments: {len(first_business.flights)}")
        print(f"  Price: {first_business.itinerary_summary.currency if first_business.itinerary_summary else ''}"
              f"{first_business.itinerary_summary.price if first_business.itinerary_summary else 'N/A'}")

        business_flight_found = True

        # Build connecting segments if multi-leg
        outbound_flight = first_business.flights[0]
        connecting_segments = None
        if len(first_business.flights) > 1:
            connecting_segments = []
            for i in range(1, len(first_business.flights)):
                segment = first_business.flights[i]
                to_airport = (first_business.flights[i+1].departure_airport
                             if i+1 < len(first_business.flights)
                             else first_business.arrival_airport)
                connecting_segments.append({
                    'from': segment.departure_airport,
                    'to': to_airport,
                    'airline': segment.airline,
                    'flight_number': segment.flight_number,
                    'date': f"{segment.departure_date[0]}-{segment.departure_date[1]:02d}-{segment.departure_date[2]:02d}",
                })

        print(f"\nGenerating return flight filter...")
        print(f"  Outbound: {outbound_flight.airline} {outbound_flight.flight_number}")
        if connecting_segments:
            print(f"  Connecting segments: {len(connecting_segments)}")
            for i, seg in enumerate(connecting_segments, 1):
                print(f"    Segment {i+1}: {seg['from']} → {seg['to']} ({seg['airline']} {seg['flight_number']})")

        return_tfs_business = create_return_flight_filter(
            outbound_date="2026-02-05",
            outbound_from="SFO",
            outbound_to="IST",
            outbound_airline=outbound_flight.airline,
            outbound_flight_number=outbound_flight.flight_number,
            connecting_segments=connecting_segments,
            return_date="2026-02-18",
            seat="business",  # Must match initial search seat class
            exclude_basic_economy=False
        )

        print(f"\nReturn TFS: {return_tfs_business[:80]}...")
        print(f"URL: https://www.google.com/travel/flights?tfs={return_tfs_business}")

        # Verify the return filter can be decoded
        try:
            decoded_business = base64.urlsafe_b64decode(return_tfs_business + '===')
            print(f"✓ Return TFS is valid (length: {len(decoded_business)} bytes)")
        except Exception as e:
            print(f"✗ Failed to decode return TFS: {e}")

        # Verify return TFS returns flights
        print("\nVerifying return TFS returns flights...")
        try:
            result = get_flights_from_tfs(return_tfs_business, data_source='js', mode='fallback')
            if result:
                if hasattr(result, 'best'):
                    total_flights = len(result.best) + (len(result.other) if hasattr(result, 'other') else 0)
                    if total_flights > 0:
                        print(f"✓ Return TFS valid: Found {len(result.best)} best + {len(result.other) if hasattr(result, 'other') else 0} other flights")
                        business_return_success = True
                    else:
                        print(f"✗ Return TFS returned no flights (result type: {type(result)})")
                else:
                    print(f"✗ Result missing 'best' attribute (type: {type(result)}, attrs: {dir(result) if result else 'None'})")
            else:
                print("✗ Result is None")
        except Exception as e:
            print(f"✗ Return TFS validation failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("✗ No business class flights found")
except Exception as e:
    print(f"✗ Error fetching business class flights: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"One-way (exclude basic):         {'✓ PASS' if (oneway_exclude_b64 == expected_oneway_exclude and oneway_exclude_valid) else '✗ FAIL'}")
print(f"One-way (include basic):         {'✓ PASS' if (oneway_include_b64 == expected_oneway_include and oneway_include_valid) else '✗ FAIL'}")
print(f"Roundtrip (with basic):          {'✓ PASS' if (actual_with == expected_with_basic and roundtrip_with_valid) else '✗ FAIL'}")
print(f"Roundtrip (exclude basic):       {'✓ PASS' if (actual_without == expected_without_basic and roundtrip_without_valid) else '✗ FAIL'}")
if has_field_25_with is not None:
    print(f"Return flight (with basic):      {'✓ PASS' if (not has_field_25_with and return_with_valid) else '✗ FAIL'}")
else:
    print(f"Return flight (with basic):      ⊘ SKIPPED (no flight data)")
if has_field_25_without is not None:
    print(f"Return flight (exclude basic):   {'✓ PASS' if (has_field_25_without and return_without_valid) else '✗ FAIL'}")
else:
    print(f"Return flight (exclude basic):   ⊘ SKIPPED (no flight data)")
print(f"Business class roundtrip:        {'✓ PASS' if business_flight_found and business_return_success else '✗ FAIL' if business_flight_found else '⊘ SKIPPED (no flight data)'}")
