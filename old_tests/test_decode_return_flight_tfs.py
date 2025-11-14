#!/usr/bin/env python3
"""
Test script to extract and decode TFS strings from return flight options.

This script:
1. Fetches return flight options for a selected outbound flight
2. Extracts TFS strings from each return flight option
3. Decodes each TFS to show the selected return flight number and details
"""

import base64
import re
from fast_flights import get_flights_from_tfs, flights_pb2 as PB
from fast_flights.core import fetch

# Return flight selection TFS (outbound flight already selected: UA2230)
# This TFS represents: SFO->MCO on Nov 18 (UA2230 selected), searching for return flights on Nov 25
return_search_tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGiMSCjIwMjUtMTEtMjVqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBBAgBEAKYAQE"

print("=" * 80)
print("Return Flight TFS Extraction and Decoding")
print("=" * 80)

# First, decode the search TFS to show context
print("\nStep 1: Decoding the return flight search TFS")
print("-" * 80)

try:
    tfs_padded = return_search_tfs + "=" * ((4 - len(return_search_tfs) % 4) % 4)
    tfs_bytes = base64.urlsafe_b64decode(tfs_padded)
    query = PB.ReturnFlightQuery()
    query.ParseFromString(tfs_bytes)

    print(f"\nSelected Outbound Flight:")
    outbound = query.legs[0].selected_flight
    print(f"  Airline: {outbound.airline}")
    print(f"  Flight Number: {outbound.flight_number}")
    print(f"  Route: {outbound.from_airport} → {outbound.to_airport}")
    print(f"  Date: {query.legs[0].date}")

    print(f"\nSearching for Return Flights:")
    print(f"  Date: {query.legs[1].date}")
    print(f"  Route: MCO → SFO")

except Exception as e:
    print(f"Error decoding search TFS: {e}")

# Step 2: Fetch the raw HTML to extract TFS strings from return flight options
print("\n" + "=" * 80)
print("Step 2: Fetching return flight page to extract individual TFS strings")
print("-" * 80)

params = {
    "tfs": return_search_tfs,
    "hl": "en",
    "tfu": "EgQIABABIgA",
}

try:
    print("\nFetching return flight selection page...")
    response = fetch(params)

    # Extract TFS strings from the HTML
    # Google Flights embeds TFS in links like: /travel/flights?tfs=...
    tfs_pattern = r'tfs=([A-Za-z0-9_-]+(?:&|"|\'|\s))'
    tfs_matches = re.findall(tfs_pattern, response.text)

    # Clean up the matches (remove trailing characters)
    tfs_strings = []
    for match in tfs_matches:
        # Remove trailing &, ", ', or whitespace
        clean_tfs = match.rstrip('&"\' ')
        if clean_tfs and clean_tfs != return_search_tfs:  # Exclude the search TFS itself
            tfs_strings.append(clean_tfs)

    # Remove duplicates while preserving order
    seen = set()
    unique_tfs = []
    for tfs in tfs_strings:
        if tfs not in seen and len(tfs) > 50:  # Filter out short/invalid TFS strings
            seen.add(tfs)
            unique_tfs.append(tfs)

    print(f"\nFound {len(unique_tfs)} unique return flight TFS strings in the HTML")

    if len(unique_tfs) == 0:
        print("\n⚠ No return flight TFS strings found in HTML")
        print("This might be because:")
        print("  1. The page is still loading (JavaScript required)")
        print("  2. The HTML structure has changed")
        print("  3. TFS strings are embedded differently")
        print("\nDemonstrating with sample TFS strings instead...\n")

        # Sample TFS strings with different return flight selections
        # These represent: Outbound UA2230 (SFO->MCO Nov 18) + different return flights (MCO->SFO Nov 25)
        sample_tfs_list = [
            # Return flight: UA626
            "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGkQSCjIwMjUtMTEtMjUiHwoDTUNPEgoyMDI1LTExLTI1GgNTRk8qAlVBMgM2MjZqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBBAgBEAKYAQE",
            # Return flight: UA2331
            "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGkUSCjIwMjUtMTEtMjUiIAoDTUNPEgoyMDI1LTExLTI1GgNTRk8qAlVBMgQyMzMxagcIARIDTUNPcgwIAhIIL20vMGQ2bHBAAUgBcAGCAQQIARADmAEB",
            # Return flight: UA1549
            "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGkUSCjIwMjUtMTEtMjUiIAoDTUNPEgoyMDI1LTExLTI1GgNTRk8qAlVBMgQxNTQ5agcIARIDTUNPcgwIAhIIL20vMGQ2bHBAAUgBcAGCAQQIARADmAEB",
        ]
        unique_tfs = sample_tfs_list
        print(f"Using {len(sample_tfs_list)} sample TFS strings with different return flight selections")

    # Step 3: Decode each TFS to extract return flight details
    print("\n" + "=" * 80)
    print("Step 3: Decoding each return flight option TFS")
    print("-" * 80)

    for i, tfs in enumerate(unique_tfs[:10], 1):  # Limit to first 10
        print(f"\n{i}. Decoding TFS: {tfs[:50]}...")

        try:
            # Decode the TFS
            tfs_padded = tfs + "=" * ((4 - len(tfs) % 4) % 4)
            tfs_bytes = base64.urlsafe_b64decode(tfs_padded)
            query = PB.ReturnFlightQuery()
            query.ParseFromString(tfs_bytes)

            # Extract outbound flight info
            if len(query.legs) >= 1 and query.legs[0].HasField('selected_flight'):
                outbound = query.legs[0].selected_flight
                print(f"   Outbound: {outbound.airline} {outbound.flight_number}")
                print(f"             {outbound.from_airport} → {outbound.to_airport} on {query.legs[0].date}")

            # Extract return flight info
            if len(query.legs) >= 2 and query.legs[1].HasField('selected_flight'):
                return_flight = query.legs[1].selected_flight
                print(f"   Return:   {return_flight.airline} {return_flight.flight_number}")
                print(f"             {return_flight.from_airport} → {return_flight.to_airport} on {query.legs[1].date}")

                # This is what we're looking for - the return flight number!
                print(f"\n   ✓ Return Flight Number: {return_flight.airline}{return_flight.flight_number}")
            else:
                print("   ⚠ No return flight selected in this TFS (still searching)")

        except Exception as e:
            print(f"   ⚠ Error decoding TFS: {e}")

    if len(unique_tfs) > 10:
        print(f"\n... and {len(unique_tfs) - 10} more return flight options")

except Exception as e:
    print(f"\n⚠ Error fetching page: {e}")

print("\n" + "=" * 80)
print("Summary")
print("-" * 80)
print("""
To get return flight numbers from the return flight selection page:

1. Fetch the return flight selection page HTML using the TFS from step 2
2. Extract individual TFS strings from flight card links in the HTML
3. Decode each TFS to get the selected return flight details
4. The return flight info is in query.legs[1].selected_flight.flight_number

Note: The HTML page may require JavaScript execution to load flight cards with TFS links.
For production use, consider using mode='local' (Playwright) or mode='bright-data'.
""")
print("=" * 80)
