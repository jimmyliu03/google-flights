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


_UNSET = object()


_METADATA_ENTRY_WITH_INNER_LIST = [
    [
        None,
        [[1783215731165430, 16320100, 3694350293], None, None, None, None, [[0]]],
        0,
        "c7ZJaraMCuSM5LcP1Z_N4Q0",
        "HSQ2vRWrHUckAIEgBQBG--------pfbgq40AAAAAGpJtnMCmjXOA",
    ],
    [None, ""],
]


def _minimal_itinerary(*, layovers=_UNSET, arrival_time=None):
    """Return a minimally-structured itinerary el that decodes cleanly."""
    arrival_time = [13, 0] if arrival_time is None else arrival_time
    inner_flight = [None] * 23
    inner_flight[3] = "WAW"  # departure_airport
    inner_flight[4] = "Warsaw Frederic Chopin"
    inner_flight[5] = "Helsinki Airport"
    inner_flight[6] = "HEL"
    inner_flight[8] = [10, 30]
    inner_flight[10] = arrival_time
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
    main[8] = arrival_time
    main[9] = 150
    main[13] = [] if layovers is _UNSET else layovers

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
    assert _is_itinerary_entry(_minimal_itinerary(layovers=None)) is True
    assert _is_itinerary_entry(_minimal_itinerary(layovers=None, arrival_time=[None, 45])) is True
    assert _is_itinerary_entry(_WARNING_ENTRY) is False
    assert _is_itinerary_entry(_METADATA_ENTRY_WITH_INNER_LIST) is False
    assert _is_itinerary_entry([]) is False
    assert _is_itinerary_entry(None) is False
    assert _is_itinerary_entry("a string") is False


def test_nonstop_itinerary_with_null_layovers_decodes_as_empty_layovers():
    """Google encodes nonstop itinerary layovers as null, not an empty list."""
    root = _root_with(
        best_entries=[_minimal_itinerary(layovers=None)],
        other_entries=[],
    )

    result = ResultDecoder.decode(root)

    assert len(result.best) == 1
    assert result.best[0].layovers == []


def test_midnight_arrival_with_null_hour_decodes():
    """Google can encode 00:mm arrival times as [null, minute]."""
    root = _root_with(
        best_entries=[_minimal_itinerary(layovers=None, arrival_time=[None, 45])],
        other_entries=[],
    )

    result = ResultDecoder.decode(root)

    assert len(result.best) == 1
    assert result.best[0].arrival_time == [0, 45]
    assert result.best[0].flights[0].arrival_time == [0, 45]


def test_metadata_entry_with_inner_list_does_not_crash_decoder():
    """Repro: non-displayable metadata row passed the old el[0] list check.

    The row has no flight legs and no [0][5] summary departure time. It should
    be skipped, not repaired with synthetic time data and not allowed to crash
    the whole response.
    """
    root = _root_with(
        best_entries=[_METADATA_ENTRY_WITH_INNER_LIST, _minimal_itinerary()],
        other_entries=[],
    )

    result = ResultDecoder.decode(root)

    assert len(result.best) == 1
    assert result.best[0].departure_airport == "WAW"


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
