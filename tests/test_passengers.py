import base64
import pytest

from fast_flights import (
    Passengers, FlightData, create_filter, create_booking_tfs,
    create_return_flight_filter, create_return_flight_url,
    create_next_leg_filter, create_itinerary_booking_tfs,
    get_passengers_from_tfs, set_passengers_in_tfs,
)
from fast_flights import flights_pb2 as PB

PARTY = dict(adults=2, children=1, infants_in_seat=1, infants_on_lap=1)
OUTBOUND = dict(outbound_date='2027-01-10', outbound_from='SFO', outbound_to='LAX',
                outbound_airline='UA', outbound_flight_number='123')
LEGS = [dict(date='2027-01-10', from_airport='SFO', to_airport='LAX', airline='UA', flight_number='123'),
        dict(date='2027-01-12', from_airport='LAX', to_airport='SEA', airline='AS', flight_number='456')]


@pytest.mark.parametrize('factory', [
    lambda p: create_filter(flight_data=[FlightData(date='2027-01-10', from_airport='SFO', to_airport='LAX')],
                            trip='one-way', seat='economy', passengers=p).as_b64().decode(),
    lambda p: create_return_flight_filter(**OUTBOUND, return_date='2027-01-12', passengers=p),
    lambda p: create_return_flight_url(**OUTBOUND, return_date='2027-01-12', passengers=p),
    lambda p: create_booking_tfs(**OUTBOUND, passengers=p),
    lambda p: create_booking_tfs(**OUTBOUND, return_date='2027-01-12', return_airline='UA', return_flight_number='456', passengers=p),
    lambda p: create_next_leg_filter(legs=LEGS, selected_legs=[LEGS[0]], passengers=p),
    lambda p: create_itinerary_booking_tfs(legs=LEGS, passengers=p),
])
def test_every_builder_encodes_complete_party(factory):
    tfs = factory(Passengers(**PARTY))
    assert get_passengers_from_tfs(tfs).asdict() == PARTY
    raw = base64.urlsafe_b64decode(tfs + '=' * (-len(tfs) % 4))
    assert b'\x40\x01\x40\x01\x40\x02\x40\x03\x40\x04' in raw


def test_return_default_keeps_one_adult():
    tfs = create_return_flight_filter(**OUTBOUND, return_date='2027-01-12')
    assert get_passengers_from_tfs(tfs).asdict() == Passengers().asdict()


@pytest.mark.parametrize('party', [dict(adults=0), dict(adults=10), dict(children=-1),
    dict(adults=True), dict(children=1.5), dict(adults='2'), dict(infants_on_lap=2)])
def test_invalid_parties(party):
    with pytest.raises(ValueError):
        Passengers(**party)


def test_nine_including_lap_infants():
    assert len(Passengers(adults=4, children=1, infants_on_lap=4).pb) == 9
    with pytest.raises(ValueError):
        Passengers(adults=4, children=2, infants_on_lap=4)


def test_repair_preserves_opaque_fields_and_reads_packed_tokens():
    # Field 8 packed; an unknown field retains its exact original bytes.
    raw = b'\x08\x1c\x42\x02\x01\x02\xf2\x01\x04test'
    tfs = base64.urlsafe_b64encode(raw).decode().rstrip('=')
    assert get_passengers_from_tfs(tfs).asdict() == dict(adults=1, children=1, infants_in_seat=0, infants_on_lap=0)
    repaired = set_passengers_in_tfs(tfs, Passengers(**PARTY))
    decoded = base64.urlsafe_b64decode(repaired + '=' * (-len(repaired) % 4))
    assert decoded == b'\x08\x1c\x40\x01\x40\x01\x40\x02\x40\x03\x40\x04\xf2\x01\x04test'
    assert get_passengers_from_tfs(repaired).asdict() == PARTY


def test_legacy_scalar_token_decodes_with_repeated_schema():
    query = PB.ReturnFlightQuery()
    query.ParseFromString(b'\x08\x1c\x40\x01')
    assert list(query.passengers) == [PB.Passenger.ADULT]


@pytest.mark.parametrize('tfs', ['', '%%%', 'QA', 'QgIB', 'QAU'])
def test_invalid_tokens(tfs):
    with pytest.raises(ValueError):
        get_passengers_from_tfs(tfs)
