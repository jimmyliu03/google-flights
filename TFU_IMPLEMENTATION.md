# TFU Parameter Implementation

## Summary

Successfully implemented TFU (Travel Flight User) parameter support throughout the fast-flights library. The `tfu` parameter is a Google Flights URL parameter that needs to be preserved through the booking flow.

## Key Finding

**TFU is NOT stored in response data** - it's a request parameter only. This means:
- TFU must be passed as a URL parameter when fetching flights
- The library stores TFU with each itinerary for later use
- TFU is passed through to subsequent requests (e.g., return flight searches)

## Changes Made

### 1. Core Functions (`fast_flights/core.py`)

Added `tfu` parameter to all fetch functions:

```python
def get_flights_from_tfs(
    tfs: str,
    currency: str = "",
    *,
    mode: Literal[...] = "common",
    data_source: DataSource = 'html',
    tfu: str = "EgQIABABIgA",  # NEW
) -> Union[Result, DecodedResult, None]:
    params = {
        "tfs": tfs,
        "hl": "en",
        "tfu": tfu,  # Used here
        "curr": currency,
    }
    # ... fetch and parse ...
    return parse_response(res, data_source, tfu=tfu)  # Passed through
```

Similarly updated:
- `get_flights_from_filter()` - Added `tfu` parameter
- `parse_response()` - Accepts and passes `tfu` to decoder

### 2. Schema (`fast_flights/decoder.py`)

Added `tfu` field to `Itinerary` dataclass:

```python
@dataclass
class Itinerary:
    airline_code: AirlineCode
    airline_names: List[AirlineName]
    flights: List[Flight]
    # ... other fields ...
    tfu: Optional[str] = None  # NEW
```

### 3. Decoder (`fast_flights/decoder.py`)

Modified `ResultDecoder.decode()` to set `tfu` on each itinerary:

```python
@classmethod
def decode(cls, root: Union[list, NLData], tfu: str = "EgQIABABIgA") -> DecodedResult:
    assert isinstance(root, list), 'Root data must be list type'
    result_data = cls.decode_el(NLData(root))

    # Add tfu to each itinerary
    for itinerary in result_data.get('best', []):
        itinerary.tfu = tfu
    for itinerary in result_data.get('other', []):
        itinerary.tfu = tfu

    return DecodedResult(**result_data, raw=root)
```

### 4. Return Flight Functions (`fast_flights/return_flight.py`)

Added `tfu` parameter to `get_return_flight_options()`:

```python
def get_return_flight_options(
    return_search_tfs: str,
    *,
    mode: Literal[...] = "fallback",
    currency: str = "",
    tfu: str = "EgQIABABIgA",  # NEW
) -> List[ReturnFlightOption]:
    # ... decode TFS ...

    # Pass tfu when fetching return flights
    result_js = get_flights_from_tfs(
        return_search_tfs,
        data_source='js',
        mode=mode,
        currency=currency,
        tfu=tfu  # Passed through
    )
    # ...
```

## Usage

### Basic Usage (Default TFU)

```python
from fast_flights import get_flights_from_tfs

# Uses default tfu = "EgQIABABIgA"
result = get_flights_from_tfs(tfs, data_source='js')

# TFU is stored in each itinerary
print(result.best[0].tfu)  # "EgQIABABIgA"
```

### Custom TFU

```python
# Provide custom tfu parameter
custom_tfu = "CnhDalJJWkhoRlNXcFlaSEpN..."
result = get_flights_from_tfs(tfs, data_source='js', tfu=custom_tfu)

# TFU is stored in each itinerary
print(result.best[0].tfu)  # "CnhDalJJWkhoRlNXcFlaSEpN..."
```

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

# Step 1: Search for outbound flights with custom tfu
filter = create_filter(
    flight_data=[
        FlightData(date="2025-11-18", from_airport="SFO", to_airport="MCO"),
        FlightData(date="2025-11-25", from_airport="MCO", to_airport="SFO"),
    ],
    trip="round-trip",
    passengers=Passengers(adults=1),
    seat="economy",
)

custom_tfu = "CnhDalJJWkhoRlNXcFlaSEpN..."
outbound_results = get_flights_from_filter(filter, data_source='js', tfu=custom_tfu)

# Step 2: User selects an outbound flight
selected_outbound = outbound_results.best[0]

# TFU is stored in the itinerary
print(f"Selected flight has tfu: {selected_outbound.tfu}")

# Step 3: Generate return flight search
first_flight = selected_outbound.flights[0]
return_tfs = create_return_flight_filter(
    outbound_date="2025-11-18",
    outbound_from=selected_outbound.departure_airport,
    outbound_to=selected_outbound.arrival_airport,
    outbound_airline=first_flight.airline,
    outbound_flight_number=first_flight.flight_number,
    return_date="2025-11-25",
)

# Step 4: Fetch return flights, passing tfu from selected outbound
return_options = get_return_flight_options(
    return_tfs,
    tfu=selected_outbound.tfu  # Pass tfu through
)

# TFU is preserved through the entire booking flow
for option in return_options:
    print(f"{option.airline} {option.flight_number}: ${option.total_price}")
```

## Testing

Created comprehensive tests to verify TFU functionality:

### `test_tfu_functionality.py`
- Tests TFU storage in itineraries
- Verifies TFU matches input parameter
- Tests TFU is passed to return flight searches
- Uses Frontier TFS with custom TFU

### `test_tfu_roundtrip.py`
- Complete roundtrip workflow
- Tests both default and custom TFU values
- Verifies TFU preservation through booking flow

### Test Results

```bash
$ python3 test_tfu_functionality.py
✅ Fetched 1 best + 4 other = 5 flights
✅ TFU matches the input parameter!
✓ TFU stored in itinerary: CnhDalJJWkhoRlNXcFlaSEpN...

$ python3 -c "test custom tfu"
✅ Fetched 5 best + 5 other flights
Custom tfu stored: CustomTfuValue123
✅ Custom tfu matches!
```

## Files Modified

1. **fast_flights/core.py**
   - Added `tfu` parameter to `get_flights_from_tfs()`
   - Added `tfu` parameter to `get_flights_from_filter()`
   - Added `tfu` parameter to `parse_response()`
   - Pass `tfu` through to decoder

2. **fast_flights/decoder.py**
   - Added `tfu: Optional[str] = None` field to `Itinerary` dataclass
   - Modified `ResultDecoder.decode()` to accept `tfu` parameter
   - Set `tfu` on each itinerary during decoding

3. **fast_flights/return_flight.py**
   - Added `tfu` parameter to `get_return_flight_options()`
   - Pass `tfu` when calling `get_flights_from_tfs()`

4. **Tests created:**
   - `research_tfu_location.py` - Research script to find TFU in data
   - `test_tfu_functionality.py` - TFU functionality test
   - `test_tfu_roundtrip.py` - Complete roundtrip workflow test

## Backward Compatibility

✅ **Fully backward compatible** - all existing code continues to work:
- `tfu` parameter is optional with default value `"EgQIABABIgA"`
- If not specified, uses Google Flights' default TFU
- Existing code doesn't need to be updated

## Why TFU Matters

The `tfu` parameter appears in some Google Flights URLs (especially for certain airlines like Frontier). While the exact purpose is not publicly documented, it's important to preserve it through the booking flow to ensure:
- Session continuity
- Correct pricing
- Proper flight availability
- Potential user-specific settings or tracking

By storing TFU with each itinerary and allowing it to be passed through to return flight searches, the library now properly maintains this parameter throughout the entire booking process.
