"""Regression tests for PriceInsights.from_raw level mapping.

The five raw enum values returned by Google at root[5][0] reflect where
current_price falls relative to typical_price_low / typical_price_high:

    1 = below typical_low                   → "low"
    2 = inside typical, near low end        → "typical"
    3 = inside typical, middle              → "typical"
    4 = inside typical, near high end       → "typical"
    5 = above typical_high                  → "high"

The previous mapping (2 → "low") mislabeled prices that sit just inside
the typical band. Each fixture below is a real Google response captured
on 2026-04-17.
"""

from fast_flights.decoder import PriceInsights


def _make_raw(level: int, current: int, typical_low: int, typical_high: int):
    return [
        level,
        [None, current],
        [None, (typical_low + typical_high) // 2],
        [None, (typical_low + typical_high) // 2 - current],
        [None, typical_low],
        [None, typical_high],
        1,
        None,
        None,
        None,
        [],
        [],
        "Test City",
    ]


def test_level_1_is_low_below_typical_range():
    pi = PriceInsights.from_raw(_make_raw(1, current=28, typical_low=35, typical_high=90))
    assert pi is not None
    assert pi.price_level == "low"


def test_level_2_is_typical_just_inside_low_end():
    pi = PriceInsights.from_raw(_make_raw(2, current=105, typical_low=95, typical_high=175))
    assert pi is not None
    assert pi.price_level == "typical"


def test_level_3_is_typical_in_the_middle():
    pi = PriceInsights.from_raw(_make_raw(3, current=423, typical_low=350, typical_high=490))
    assert pi is not None
    assert pi.price_level == "typical"


def test_level_4_is_typical_near_high_end():
    pi = PriceInsights.from_raw(_make_raw(4, current=304, typical_low=205, typical_high=310))
    assert pi is not None
    assert pi.price_level == "typical"


def test_level_5_is_high_above_typical_range():
    pi = PriceInsights.from_raw(_make_raw(5, current=600, typical_low=200, typical_high=500))
    assert pi is not None
    assert pi.price_level == "high"


def test_unknown_level_falls_back_to_typical():
    pi = PriceInsights.from_raw(_make_raw(99, current=100, typical_low=80, typical_high=120))
    assert pi is not None
    assert pi.price_level == "typical"
