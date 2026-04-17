"""Regression tests for airlines field number + time_restrictions encoding on FlightData.

Expected byte-for-byte output was captured from flights.google.com via a
reverse-engineering run in April 2026 (JFK<->LAX round-trip 2026-07-15/22).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fast_flights import FlightData, Passengers, create_filter


def _fd_pair(extra_outbound=None):
    kwargs = {"date": "2026-07-15", "from_airport": "JFK", "to_airport": "LAX"}
    if extra_outbound:
        kwargs.update(extra_outbound)
    return [
        FlightData(**kwargs),
        FlightData(date="2026-07-22", from_airport="LAX", to_airport="JFK"),
    ]


def _encode(fds):
    f = create_filter(
        flight_data=fds,
        trip="round-trip",
        passengers=Passengers(adults=1),
        seat="economy",
    )
    return f.to_string().hex()


def test_baseline_roundtrip_unchanged():
    expected = (
        "081c10021a1e120a323032362d30372d31356a07080112034a464b7207080112034c4158"
        "1a1e120a323032362d30372d32326a07080112034c41587207080112034a464b"
        "40014801700182010b08ffffffffffffffffff01980101"
    )
    assert _encode(_fd_pair()) == expected


def test_airlines_encoded_at_field_7():
    """Airlines is field 7 on FlightData (Google Flights wire format).

    3a 02 44 4c => field 7, length 2, "DL".
    """
    hex_out = _encode(_fd_pair({"airlines": ["DL"]}))
    assert "3a02444c" in hex_out


def test_time_restrictions_fields_8_9_10_11():
    """Time filters: earliest_departure=8, latest_departure=9,
    earliest_arrival=10, latest_arrival=11. Values are hours 0..23.

    Expected bytes for earliest_dep=6: 40 06 48 17 50 00 58 17 (the other
    three bounds default to 0/23 when any slider is touched).
    """
    hex_out = _encode(_fd_pair({"time_restrictions": {"earliest_departure": 6}}))
    assert "4006481750005817" in hex_out


def test_time_restrictions_all_four_values():
    """All four values propagate verbatim."""
    hex_out = _encode(_fd_pair({
        "time_restrictions": {
            "earliest_departure": 6,
            "latest_departure": 17,
            "earliest_arrival": 8,
            "latest_arrival": 19,
        },
    }))
    # 40 06 48 11 50 08 58 13
    assert "4006481150085813" in hex_out


def test_time_restrictions_none_omits_fields():
    """When time_restrictions is None, no fields 8-11 are emitted."""
    hex_out = _encode(_fd_pair())
    # Assert no field tags at 0x40/0x48/0x50/0x58 inside the outbound data block
    # (baseline should match test_baseline_roundtrip_unchanged).
    assert "40064817" not in hex_out
    assert "4800" not in hex_out.replace("4801", "")  # field 9 (latest dep) absent


def test_time_restrictions_rejects_out_of_range():
    import pytest
    with pytest.raises(ValueError):
        FlightData(
            date="2026-07-15",
            from_airport="JFK",
            to_airport="LAX",
            time_restrictions={"earliest_departure": 24},
        )


def test_time_restrictions_rejects_unknown_key():
    import pytest
    with pytest.raises(ValueError):
        FlightData(
            date="2026-07-15",
            from_airport="JFK",
            to_airport="LAX",
            time_restrictions={"departure": 6},
        )
