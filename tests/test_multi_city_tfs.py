import base64

import pytest

from fast_flights import (
    FlightData,
    Passengers,
    create_filter,
    create_itinerary_booking_tfs,
    create_next_leg_filter,
)
from fast_flights import flights_pb2 as PB


def decode(tfs: str) -> PB.ReturnFlightQuery:
    padded = tfs + "=" * (-len(tfs) % 4)
    query = PB.ReturnFlightQuery()
    query.ParseFromString(base64.urlsafe_b64decode(padded))
    return query


ROUTES = [
    {
        "date": "2027-01-10",
        "from_airport": "/m/0d6lp",
        "to_airport": "LAX",
        "max_stops": 0,
    },
    {
        "date": "2027-01-12",
        "from_airport": "LAX",
        "to_airport": "SEA",
        "max_stops": 1,
        "airlines": ["AS"],
        "time_restrictions": {"earliest_departure": 8, "latest_departure": 17},
    },
    {
        "date": "2027-01-15",
        "from_airport": "PDX",
        "to_airport": "JFK",
        "max_stops": 2,
    },
]


SELECTED = [
    {
        "from_airport": "SFO",
        "to_airport": "LAX",
        "airline": "UA",
        "flight_number": "123",
    },
    {
        "segments": [
            {
                "from": "LAX",
                "to": "PDX",
                "date": "2027-01-12",
                "airline": "AS",
                "flight_number": "456",
            },
            {
                "from": "PDX",
                "to": "SEA",
                "date": "2027-01-12",
                "airline": "AS",
                "flight_number": "789",
            },
        ]
    },
]


def test_initial_multi_city_filter_supports_five_legs():
    legs = [
        FlightData(date=f"2027-01-{10 + i:02d}", from_airport="SFO", to_airport="LAX")
        for i in range(5)
    ]
    tfs = create_filter(
        flight_data=legs,
        trip="multi-city",
        passengers=Passengers(adults=1),
        seat="economy",
    )

    info = PB.Info()
    info.ParseFromString(base64.urlsafe_b64decode(tfs.as_b64() + b"=" * (-len(tfs.as_b64()) % 4)))
    assert info.trip == PB.Trip.MULTI_CITY
    assert len(info.data) == 5


def test_next_leg_filter_encodes_selected_prefix_and_filters():
    query = decode(create_next_leg_filter(legs=ROUTES, selected_legs=SELECTED))

    assert query.step == 3
    assert query.field_19 == 2
    assert len(query.legs) == 3
    assert query.legs[0].location_filter_1.filter_type == 2
    assert [segment.flight_number for segment in query.legs[1].selected_flight] == [
        "456",
        "789",
    ]
    assert not query.legs[2].selected_flight
    assert query.legs[1].airlines == ["AS"]
    assert query.legs[1].earliest_departure == 8
    assert query.legs[1].latest_departure == 17
    assert query.legs[1].earliest_arrival == 0
    assert query.legs[1].latest_arrival == 23


def test_itinerary_booking_tfs_selects_every_leg():
    final = {
        **ROUTES[2],
        "from_airport": "PDX",
        "to_airport": "JFK",
        "airline": "DL",
        "flight_number": "101",
    }
    booking_legs = [
        {**ROUTES[0], **SELECTED[0]},
        {**ROUTES[1], **SELECTED[1]},
        final,
    ]
    query = decode(create_itinerary_booking_tfs(legs=booking_legs))

    assert query.step == 4
    assert all(leg.selected_flight for leg in query.legs)
    assert query.legs[-1].selected_flight[0].flight_number == "101"


@pytest.mark.parametrize("count", [0, 1, 6])
def test_multi_city_filter_rejects_invalid_leg_counts(count: int):
    legs = [
        FlightData(date="2027-01-10", from_airport="SFO", to_airport="LAX")
        for _ in range(count)
    ]
    with pytest.raises(ValueError, match="between 2 and 5"):
        create_filter(
            flight_data=legs,
            trip="multi-city",
            passengers=Passengers(adults=1),
            seat="economy",
        )


def test_next_leg_filter_rejects_non_chronological_dates():
    legs = [ROUTES[1], ROUTES[0]]
    with pytest.raises(ValueError, match="nondecreasing"):
        create_next_leg_filter(legs=legs, selected_legs=[SELECTED[0]])
