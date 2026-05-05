"""Regression tests for travel-advisory handling in ResultDecoder.

Repro of a production cron failure (fred-app bundle search, 2026-05-04):
when Google injects an airspace-closure advisory into ``data[2][0]`` or
``data[3][0]`` as a sibling to itineraries, the previous decoder failed
with ``AssertionError: Found non list type while trying to decode [0, 0]``
because the advisory entry's first element is an int marker, not a list.

Live captures of the same query showed the advisory at ``data[22][0]``
with shape::

    [12, null, null, null, null,
     ["Travel restricted", "Airspace closure may affect flights.", 2]]

Google's placement is non-deterministic — sometimes ``data[22]``, sometimes
inline as a sibling — which is why the bundle cron sees intermittent 503s
on Warsaw→Asia routes.
"""

from fast_flights.decoder import (
    DecodedResult,
    ResultDecoder,
    TravelWarning,
    _is_itinerary_entry,
    _parse_travel_warning,
)


_WARNING_ENTRY = [
    12,
    None,
    None,
    None,
    None,
    ["Travel restricted", "Airspace closure may affect flights.", 2],
]


def _minimal_itinerary():
    """Return a minimally-structured itinerary el that decodes cleanly."""
    inner_flight = [None] * 23
    inner_flight[3] = "WAW"  # departure_airport
    inner_flight[4] = "Warsaw Frederic Chopin"
    inner_flight[5] = "Helsinki Airport"
    inner_flight[6] = "HEL"
    inner_flight[8] = [10, 30]
    inner_flight[10] = [13, 0]
    inner_flight[11] = 150
    inner_flight[14] = ""
    inner_flight[17] = "Aircraft"
    inner_flight[20] = [2026, 6, 12]
    inner_flight[21] = [2026, 6, 12]
    inner_flight[22] = ["AY", "100", None, "Finnair"]
    inner_flight[15] = []  # codeshares

    main = [None] * 14
    main[0] = "AY"
    main[1] = ["Finnair"]
    main[2] = [inner_flight]
    main[3] = "WAW"
    main[4] = [2026, 6, 12]
    main[5] = [10, 30]
    main[6] = "HEL"
    main[7] = [2026, 6, 12]
    main[8] = [13, 0]
    main[9] = 150
    main[13] = []  # layovers

    summary_b64 = ""  # ItinerarySummary.from_b64("") is tolerated downstream
    return [main, [None, summary_b64]]


def _root_with(best_entries, other_entries=None, warnings_at_22=None):
    """Build a 31-element root mimicking Google's data[*] response shape."""
    other = other_entries if other_entries is not None else [_minimal_itinerary()]
    root = [None] * 31
    root[2] = [best_entries]
    root[3] = [other]
    if warnings_at_22 is not None:
        root[22] = warnings_at_22
    return root


def test_inline_warning_does_not_crash_decoder():
    """Repro: warning entry inline in BEST. Previously crashed with AssertionError."""
    root = _root_with(best_entries=[_WARNING_ENTRY, _minimal_itinerary()])

    result = ResultDecoder.decode(root)

    assert isinstance(result, DecodedResult)
    assert len(result.best) == 1, "the itinerary entry should still decode"
    assert result.warnings, "the inline advisory should surface as a warning"
    assert result.warnings[0].title == "Travel restricted"
    assert result.warnings[0].code == 12
    assert result.warnings[0].severity == 2


def test_top_level_warning_at_data_22_is_collected():
    root = _root_with(
        best_entries=[_minimal_itinerary()],
        warnings_at_22=[_WARNING_ENTRY],
    )

    result = ResultDecoder.decode(root)

    assert len(result.best) == 1
    titles = [w.title for w in result.warnings]
    assert "Travel restricted" in titles


def test_clean_response_has_empty_warnings():
    root = _root_with(best_entries=[_minimal_itinerary()])

    result = ResultDecoder.decode(root)

    assert result.warnings == []


def test_is_itinerary_entry_discriminator():
    assert _is_itinerary_entry(_minimal_itinerary()) is True
    assert _is_itinerary_entry(_WARNING_ENTRY) is False
    assert _is_itinerary_entry([]) is False
    assert _is_itinerary_entry(None) is False
    assert _is_itinerary_entry("a string") is False


def test_parse_travel_warning_extracts_fields():
    parsed = _parse_travel_warning(_WARNING_ENTRY)
    assert isinstance(parsed, TravelWarning)
    assert parsed.code == 12
    assert parsed.title == "Travel restricted"
    assert parsed.message == "Airspace closure may affect flights."
    assert parsed.severity == 2


def test_parse_travel_warning_returns_none_for_unrelated():
    assert _parse_travel_warning([1, 2, 3]) is None
    assert _parse_travel_warning("not a list") is None
    assert _parse_travel_warning([]) is None
