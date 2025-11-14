# Return Flight Functionality - Implementation Summary

## What Was Accomplished

### 1. Fixed JS Data Source for Return Flights

**Problem:** Return flight pages have a different data structure than initial searches:
- Initial searches: `data[2]` contains "best" flights
- Return flights: `data[2] = None`, all flights in `data[3]`

**Solution:** Modified `decoder.py` to handle `None` values gracefully:
- `NLData.__getitem__`: Returns `None` when encountering `None` during path traversal
- `DecoderKey.decode`: Converts `None` to empty list `[]` when a decoder expects a list

**Result:** ✅ JS data source now works for return flight pages

### 2. Created Return Flight API Functions

**New functions in `fast_flights/return_flight.py`:**

```python
# Generate TFS for return flight search
create_return_flight_filter(
    outbound_date, outbound_from, outbound_to,
    outbound_airline, outbound_flight_number, return_date
) -> str

# Decode TFS to extract flight details
decode_return_flight_tfs(tfs: str) -> Dict[str, Any]

# Fetch all return flight options
get_return_flight_options(
    return_search_tfs: str,
    mode='fallback',
    currency=''
) -> List[ReturnFlightOption]
```

**ReturnFlightOption dataclass:**
- airline, flight_number
- departure_airport, arrival_airport
- departure_date, departure_time, arrival_time
- duration_minutes, stops
- total_price, currency
- aircraft (optional)
- raw_itinerary (optional)

### 3. Test Results

**Verified working:**
✅ `decode_return_flight_tfs()` - Works with all TFS strings, no dependencies
✅ JS data parsing - Successfully extracts 15-18 return flights with full details
✅ Top + Other sections - Properly combines both flight categories
✅ Multi-airline support - Tested with UA (United), F9 (Frontier), AS (Alaska)

## Important Findings

### Return Flight Page Behavior

**Two scenarios exist:**

1. **Pre-rendered data (some pages):**
   - Flight data exists in initial HTML/JS
   - Works with `mode='common'`
   - Example: UA return flights (15 flights loaded)

2. **JavaScript-rendered data (most pages):**
   - Flight data NOT in initial HTML/JS
   - Requires `mode='fallback'`, `mode='local'`, or `mode='bright-data'`
   - Example: Frontier return flights (0 flights without JS rendering)

### Mode Recommendations

| Mode | Description | Return Flight Support |
|------|-------------|----------------------|
| `common` | Direct HTTP scraping | ⚠️ Works for some, not all |
| `fallback` | Tries `common`, falls back to Playwright | ✅ **Recommended** |
| `force-fallback` | Always uses Playwright serverless | ✅ Requires browserless.io auth |
| `local` | Uses local Playwright | ✅ Requires `pip install 'fast-flights[local]'` |
| `bright-data` | Uses Bright Data proxy | ✅ Requires API key |

**Best practice:** Use `mode='fallback'` (default) for maximum compatibility

## Usage Examples

### Complete Roundtrip Workflow

```python
from fast_flights import (
    create_filter,
    get_flights_from_filter,
    create_return_flight_filter,
    get_return_flight_options,
    FlightData,
    Passengers,
)

# 1. Search for outbound flights
filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
)

outbound = get_flights_from_filter(filter, data_source='js')

# 2. User selects an outbound flight
selected = outbound.best[0]
first_flight = selected.flights[0]

# 3. Generate return flight search TFS
return_tfs = create_return_flight_filter(
    outbound_date=f"{first_flight.departure_date[0]}-{first_flight.departure_date[1]:02d}-{first_flight.departure_date[2]:02d}",
    outbound_from=selected.departure_airport,
    outbound_to=selected.arrival_airport,
    outbound_airline=first_flight.airline,
    outbound_flight_number=first_flight.flight_number,
    return_date="2025-11-25",
)

# 4. Fetch all return flight options
return_options = get_return_flight_options(return_tfs)  # Uses mode='fallback' by default

# 5. Display return flights
for option in return_options:
    print(f"{option.airline} {option.flight_number}: ${option.total_price:.2f}")
```

### Decode Existing TFS (No Dependencies)

```python
from fast_flights import decode_return_flight_tfs

tfs = "CBwQAhpFEgoyMDI1LTExLTE4IiAKA1NGTxIKMjAyNS0xMS0xOBoDTUNPKgJVQTIEMjIzMGoMCAISCC9tLzBkNmxwcgcIARIDTUNPGkQSCjIwMjUtMTEtMjUiHwoDTUNPEgoyMDI1LTExLTI1GgNTRk8qAlVBMgM2MjZqBwgBEgNNQ09yDAgCEggvbS8wZDZscEABSAFwAYIBBAgBEAKYAQE"

decoded = decode_return_flight_tfs(tfs)

print(f"Outbound: {decoded['outbound']['airline']} {decoded['outbound']['flight_number']}")
# Output: Outbound: UA 2230

if decoded['return']:
    print(f"Return: {decoded['return']['airline']} {decoded['return']['flight_number']}")
    # Output: Return: UA 626
```

## Technical Details

### Decoder Changes

**File: `fast_flights/decoder.py`**

```python
# Modified NLData.__getitem__ to handle None
def __getitem__(self, decode_path: Union[int, DecodePath]) -> NLBaseType:
    if isinstance(decode_path, int):
        return self.data[decode_path]
    it = self.data
    for index in decode_path:
        # Return None early if we encounter None during traversal
        if it is None:
            return None
        assert isinstance(it, list), f'Found non list type...'
        it = it[index]
    return it

# Modified DecoderKey.decode to convert None to empty list
def decode(self, root: NLData) -> Union[NLBaseType, V]:
    data = root[self.decode_path]

    # Handle None values - return empty list if decoder expects a list
    if data is None and self.decoder is not None:
        return []

    if isinstance(data, list) and self.decoder:
        return self.decoder(NLData(data))
    return data
```

### Return Flight Data Structure

```
JavaScript data structure:
data[0] = Airports list
data[1] = Unknown
data[2] = None (no "best" section on return pages)
data[3] = [
    [0] = All return flight itineraries (top + other combined)
    ...
]
```

The `get_return_flight_options()` function:
1. Tries JS data source first: `result_js.best + result_js.other`
2. Falls back to HTML if JS fails (provides all details except flight numbers)
3. Returns unified list of `ReturnFlightOption` objects

## Files Modified

1. **fast_flights/decoder.py** - Handle None in nested list traversal
2. **fast_flights/return_flight.py** - New API functions
3. **fast_flights/__init__.py** - Export new functions
4. **test_get_return_flight_options.py** - Complete workflow test
5. **example.md** - Comprehensive documentation

## Known Limitations

1. **Flight number availability depends on data source:**
   - JS data source: Includes flight numbers ✅
   - HTML data source: No flight numbers ❌

2. **Some return flight pages require JavaScript rendering:**
   - Cannot use `mode='common'` for all pages
   - Recommend `mode='fallback'` for reliability

3. **Mode dependencies:**
   - `mode='local'` requires: `pip install 'fast-flights[local]'` + `playwright install`
   - `mode='bright-data'` requires: `BRIGHT_DATA_API_KEY` environment variable
   - `mode='force-fallback'` requires: browserless.io authentication

## Success Metrics

✅ Decoder handles return flight structure (data[2] = None)
✅ Successfully extracts 15+ return flights with details
✅ Flight numbers extracted from JS data
✅ Both "top" and "other" sections properly combined
✅ Works with multiple airlines (UA, F9, AS)
✅ `decode_return_flight_tfs()` works without any dependencies
✅ Complete API documented in example.md
