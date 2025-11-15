#!/usr/bin/env python3
"""Test exclude_basic_economy with the user's correct URLs"""

import base64
from fast_flights import create_filter, Passengers, FlightData

# Test data from user's URLs
expected_with_basic = "CBwQAhoeEgoyMDI1LTEyLTEwagcIARIDU0ZPcgcIARIDTUNPGh4SCjIwMjUtMTItMTRqBwgBEgNNQ09yBwgBEgNTRk9AAUgBcAGCAQsI____________AZgBAQ"
expected_without_basic = "CBwQAhoeEgoyMDI1LTEyLTEwagcIARIDU0ZPcgcIARIDTUNPGh4SCjIwMjUtMTItMTRqBwgBEgNNQ09yBwgBEgNTRk9AAUgBcAGCAQsI____________AZgBAcgBAQ"

print("Testing WITH basic economy (exclude_basic_economy=False):")
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
print(f"Match: {actual_with == expected_with_basic}")
print()

# Decode both to see hex difference
expected_bytes_with = base64.b64decode(expected_with_basic + "==")
actual_bytes_with = base64.b64decode(actual_with + "==")
print(f"Expected hex: {expected_bytes_with.hex()}")
print(f"Actual hex:   {actual_bytes_with.hex()}")
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
print(f"Match: {actual_without == expected_without_basic}")
print()

# Decode both to see hex difference
expected_bytes_without = base64.b64decode(expected_without_basic + "==")
actual_bytes_without = base64.b64decode(actual_without + "==")
print(f"Expected hex: {expected_bytes_without.hex()}")
print(f"Actual hex:   {actual_bytes_without.hex()}")
