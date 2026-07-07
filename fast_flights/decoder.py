import abc
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, List, Generic, Optional, Sequence, TypeVar, Union, Tuple
from typing_extensions import TypeAlias, override

from .flights_impl import ItinerarySummary

DecodePath: TypeAlias = List[int]
PriceLevel: TypeAlias = str  # "low", "typical", "high"
NLBaseType: TypeAlias = Union[int, str, None, Sequence['NLBaseType']]

# N(ested)L(ist)Data, this class allows indexing using a path, and as an int to make
# traversal easier within the nested list data
@dataclass
class NLData(Sequence[NLBaseType]):
    data: List[NLBaseType]

    def __getitem__(self, decode_path: Union[int, DecodePath]) -> NLBaseType:
        if isinstance(decode_path, int):
            return self.data[decode_path]
        it = self.data
        for index in decode_path:
            # Return None early if we encounter None during traversal
            # This handles return flight pages where data[2] = None
            if it is None:
                return None
            assert isinstance(it, list), f'Found non list type while trying to decode {decode_path}'
            assert index < len(it), f'Trying to traverse to index out of range when decoding {decode_path}'
            it = it[index]
        return it

    @override
    def __len__(self) -> int:
        return len(self.data)

def normalize_time(data: NLData) -> List[int]:
    """
    Normalize time data to always have [hour, minute] format.
    Google sometimes returns [hour] without minutes, or [hour, 0] where 0 gets filtered.
    This ensures we always have a 2-element list with hour and minute.
    """
    if isinstance(data.data, list):
        # Ensure we have at least 2 elements
        time_list = list(data.data)
        # Pad with 0s if needed (for hour or minute)
        while len(time_list) < 2:
            time_list.append(0)
        # Return only first 2 elements [hour, minute]
        return [time_list[0] if time_list[0] is not None else 0,
                time_list[1] if time_list[1] is not None else 0]
    return [0, 0]  # Default fallback

# DecoderKey is used to specify the path to a field from a decoder class
V = TypeVar('V')
@dataclass
class DecoderKey(Generic[V]):
    decode_path: DecodePath
    decoder: Optional[Callable[[NLData], V]] = None

    def decode(self, root: NLData) -> Union[NLBaseType, V]:
        data = root[self.decode_path]

        # Handle None values - return empty list if decoder expects a list
        # This handles return flight pages where data[2] = None (no "best" flights section)
        if data is None and self.decoder is not None:
            return []

        if isinstance(data, list) and self.decoder:
            assert self.decoder is not None, f'decoder should be provided in order to further decode NLData instances'
            return self.decoder(NLData(data))
        return data

# Decoder is used to aggregate all fields and their paths
class Decoder(abc.ABC):
    @classmethod
    def decode_el(cls, el: NLData) -> Mapping[str, Any]:
        decoded: Mapping[str, Any] = {}
        for field_name, key_decoder in vars(cls).items():
            if isinstance(key_decoder, DecoderKey):
                value = key_decoder.decode(el)
                decoded[field_name.lower()] = value
        return decoded

    @classmethod
    def decode(cls, root: Union[list, NLData]) -> ...:
        ...


# Type Aliases
AirlineCode: TypeAlias = str
AirlineName: TypeAlias = str
AirportCode: TypeAlias = str
AirportName: TypeAlias = str
ProtobufStr: TypeAlias = str
Minute: TypeAlias = int

@dataclass
class Codeshare:
    airline_code: AirlineCode
    flight_number: int
    airline_name: AirlineName

@dataclass
class Flight:
    airline: AirlineCode
    airline_name: AirlineName
    flight_number: str
    operator: str
    codeshares: List[Codeshare]
    aircraft: str
    departure_airport: AirportCode
    departure_airport_name: AirportName
    arrival_airport: AirportCode
    arrival_airport_name: AirportName
    # some_enum: int
    # some_enum: int
    departure_date: Tuple[int, int, int]
    arrival_date: Tuple[int, int, int]
    departure_time: Tuple[int, int]
    arrival_time: Tuple[int, int]
    travel_time: int
    seat_pitch_short: str
    # seat_pitch_long: str

@dataclass
class Layover:
    minutes: Minute
    departure_airport: AirportCode
    departure_airport_name: AirportName
    departure_airport_city: AirportName
    arrival_airport: AirportCode
    arrival_airport_name: AirportName
    arrival_airport_city: AirportName

@dataclass
class Itinerary:
    airline_code: AirlineCode
    airline_names: List[AirlineName]
    flights: List[Flight]
    layovers: List[Layover]
    travel_time: int
    departure_airport: AirportCode
    arrival_airport: AirportCode
    departure_date: Tuple[int, int, int]
    arrival_date: Tuple[int, int, int]
    departure_time: Tuple[int, int]
    arrival_time: Tuple[int, int]
    itinerary_summary: ItinerarySummary
    tfu: Optional[str] = None

@dataclass
class PriceGraphPoint:
    timestamp_ms: int
    price: int

@dataclass
class TravelWarning:
    """A travel advisory dialog Google injects into the response.

    Observed on routes affected by airspace closures (e.g. Warsaw to Asia
    after Russian airspace was closed): Google emits a sibling entry such
    as ``[12, null, null, null, null, ["Travel restricted",
    "Airspace closure may affect flights.", 2]]``. The leading int is a
    type marker (``12`` = travel-restriction advisory) and the trailing
    int in the body is a severity (1=info, 2=warning).

    Two placements appear in the wild:
      * top-level at ``data[22]`` — purely informational, decoder ignores
      * inline as a sibling of itineraries at ``data[2][0]``/``data[3][0]``
        — replaces what the decoder expected to be itinerary shape

    Surfaced via :class:`DecodedResult.warnings` so callers can read them.
    """

    code: int
    title: str
    message: str
    severity: int


@dataclass
class PriceInsights:
    price_level: PriceLevel  # "low", "typical", "high"
    current_price: Optional[int]
    typical_price_low: Optional[int]
    typical_price_high: Optional[int]
    price_difference: Optional[int]  # difference from typical (negative = below typical)
    price_history: List[PriceGraphPoint]
    destination_city: Optional[str]

    @classmethod
    def from_raw(cls, data: list) -> Optional['PriceInsights']:
        """Parse price insights from data[5] of the JS response."""
        if data is None or not isinstance(data, list) or len(data) < 6:
            return None

        try:
            # data[0] is the price level enum. Empirically verified by running
            # 8 real searches and correlating data[0] with where current_price
            # falls relative to typical_price_low/high (data[4][1], data[5][1]):
            #   1 = current_price < typical_low                 → "low"
            #   2 = inside typical, near low end (~0-30% in)    → "typical"
            #   3 = inside typical, middle (~30-60% in)         → "typical"
            #   4 = inside typical, near high end (~60-100% in) → "typical"
            #   5 = current_price > typical_high                → "high"
            # The earlier mapping (2 → "low") mislabeled prices that sit just
            # inside the typical band — the Google Flights UI shows those as
            # "typical" with the dot in the yellow zone of the price bar.
            level_map = {1: "low", 2: "typical", 3: "typical", 4: "typical", 5: "high"}
            raw_level = data[0]
            price_level = level_map.get(raw_level, "typical")

            # data[1] = [null, current_price]
            current_price = data[1][1] if isinstance(data[1], list) and len(data[1]) > 1 else None

            # data[3] = [null, price_difference_from_typical]
            price_difference = data[3][1] if isinstance(data[3], list) and len(data[3]) > 1 else None

            # data[4] = [null, typical_price_low]
            typical_price_low = data[4][1] if isinstance(data[4], list) and len(data[4]) > 1 else None

            # data[5] = [null, typical_price_high]
            typical_price_high = data[5][1] if isinstance(data[5], list) and len(data[5]) > 1 else None

            # data[10] = [[timestamp_ms, price], ...] - price history graph
            price_history = []
            if len(data) > 10 and isinstance(data[10], list) and len(data[10]) > 0:
                raw_history = data[10][0] if isinstance(data[10][0], list) and len(data[10][0]) > 0 and isinstance(data[10][0][0], list) else data[10]
                for point in raw_history:
                    if isinstance(point, list) and len(point) >= 2:
                        price_history.append(PriceGraphPoint(
                            timestamp_ms=point[0],
                            price=point[1]
                        ))

            # data[12] = destination city name
            destination_city = data[12] if len(data) > 12 and isinstance(data[12], str) else None

            return cls(
                price_level=price_level,
                current_price=current_price,
                typical_price_low=typical_price_low,
                typical_price_high=typical_price_high,
                price_difference=price_difference,
                price_history=price_history,
                destination_city=destination_city,
            )
        except (IndexError, TypeError, KeyError):
            return None


@dataclass
class DecodedResult:
    # raw unparsed data
    raw: list

    best: List[Itinerary]
    other: List[Itinerary]

    price_insights: Optional[PriceInsights] = None
    warnings: List[TravelWarning] = field(default_factory=list)


def _list_has(root: Any, path: DecodePath) -> bool:
    it = root
    for index in path:
        if not isinstance(it, list) or index >= len(it):
            return False
        it = it[index]
    return True


def _is_date(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 3
        and all(isinstance(x, int) for x in value[:3])
    )


def _is_time(value: Any) -> bool:
    if not isinstance(value, list) or len(value) < 1:
        return False
    if isinstance(value[0], int):
        return True
    # Midnight arrivals can encode the hour as null and the minute at index 1;
    # normalize_time decodes this as 00:mm, so the guard should admit it too.
    return value[0] is None and len(value) > 1 and isinstance(value[1], int)


def _is_flight_entry(el: Any) -> bool:
    if not isinstance(el, list):
        return False
    if not all(_list_has(el, [idx]) for idx in (2, 3, 4, 5, 6, 8, 10, 11, 14, 15, 17, 20, 21, 22)):
        return False
    if not isinstance(el[3], str) or not isinstance(el[5], str):
        return False
    if not _is_time(el[8]) or not _is_time(el[10]):
        return False
    if not _is_date(el[20]) or not _is_date(el[21]):
        return False
    airline = el[22]
    return (
        isinstance(airline, list)
        and len(airline) > 3
        and isinstance(airline[0], str)
        and isinstance(airline[1], (str, int))
        and isinstance(airline[3], str)
    )


# Discriminate displayable itinerary entries from "decoration" and metadata
# entries Google occasionally injects as siblings inside data[2][0] / data[3][0].
# A real itinerary has every path consumed by ItineraryDecoder plus at least one
# displayable leg. Metadata rows can still have el[0] as a list, so checking only
# that first element is not sufficient and caused the [0, 5] crash.
def _is_itinerary_entry(el: Any) -> bool:
    if not (
        isinstance(el, list)
        and len(el) > 1
        and isinstance(el[0], list)
        and isinstance(el[1], list)
        and len(el[1]) > 1
    ):
        return False

    summary = el[0]
    if not all(_list_has(summary, [idx]) for idx in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13)):
        return False
    if not isinstance(summary[0], str):
        return False
    if not isinstance(summary[1], list):
        return False
    if not isinstance(summary[2], list) or len(summary[2]) == 0:
        return False
    if not isinstance(summary[3], str) or not isinstance(summary[6], str):
        return False
    if not _is_date(summary[4]) or not _is_time(summary[5]):
        return False
    if not _is_date(summary[7]) or not _is_time(summary[8]):
        return False
    if not isinstance(summary[9], int):
        return False
    # Nonstop itineraries have no layovers and Google encodes that field as
    # null; DecoderKey already normalizes null layover lists to [].
    if summary[13] is not None and not isinstance(summary[13], list):
        return False
    return all(_is_flight_entry(flight) for flight in summary[2])


def _parse_travel_warning(el: Any) -> Optional[TravelWarning]:
    """Best-effort parse of a non-itinerary entry into a TravelWarning.

    Expected shape: ``[code, *placeholders, [title, message, severity]]``.
    Returns ``None`` if the body doesn't match — we only surface entries
    that look like travel advisories so callers don't get spurious
    warnings from unrelated decoration markers.

    Body discriminator is strict: forward-scan from index 1 for the first
    sub-list shaped exactly ``[str, str, int]``. This avoids picking up
    later-added action/button sub-lists and is order-independent.
    """
    if not isinstance(el, list) or not el:
        return None
    code = el[0]
    if not isinstance(code, int):
        return None
    body = next(
        (
            x
            for x in el[1:]
            if isinstance(x, list)
            and len(x) >= 3
            and isinstance(x[0], str)
            and isinstance(x[1], str)
            and isinstance(x[2], int)
        ),
        None,
    )
    if body is None:
        return None
    return TravelWarning(code=code, title=body[0], message=body[1], severity=body[2])

class CodeshareDecoder(Decoder):
    AIRLINE_CODE: DecoderKey[AirlineCode] = DecoderKey([0])
    FLIGHT_NUMBER: DecoderKey[str] = DecoderKey([1])
    AIRLINE_NAME: DecoderKey[List[AirlineName]] = DecoderKey([3])

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Codeshare]:
        return [Codeshare(**cls.decode_el(NLData(el))) for el in root]

class FlightDecoder(Decoder):
    OPERATOR: DecoderKey[AirlineName] = DecoderKey([2])
    DEPARTURE_AIRPORT: DecoderKey[AirportCode] = DecoderKey([3])
    DEPARTURE_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([4])
    ARRIVAL_AIRPORT: DecoderKey[AirportCode] = DecoderKey([5])
    ARRIVAL_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([6])
    # SOME_ENUM: DecoderKey[int] = DecoderKey([7])
    # SOME_ENUM: DecoderKey[int] = DecoderKey([9])
    DEPARTURE_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([8], normalize_time)
    ARRIVAL_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([10], normalize_time)
    TRAVEL_TIME: DecoderKey[int] = DecoderKey([11])
    SEAT_PITCH_SHORT: DecoderKey[str] = DecoderKey([14])
    AIRCRAFT: DecoderKey[str] = DecoderKey([17])
    DEPARTURE_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([20])
    ARRIVAL_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([21])
    AIRLINE: DecoderKey[AirlineCode] = DecoderKey([22, 0])
    AIRLINE_NAME: DecoderKey[AirlineName] = DecoderKey([22, 3])
    FLIGHT_NUMBER: DecoderKey[str] = DecoderKey([22, 1])
    # SEAT_PITCH_LONG: DecoderKey[str] = DecoderKey([30])
    CODESHARES: DecoderKey[List[Codeshare]] = DecoderKey([15], CodeshareDecoder.decode)

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Flight]:
        return [Flight(**cls.decode_el(NLData(el))) for el in root]

class LayoverDecoder(Decoder):
    MINUTES: DecoderKey[int] = DecoderKey([0])
    DEPARTURE_AIRPORT: DecoderKey[AirportCode] = DecoderKey([1])
    DEPARTURE_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([4])
    DEPARTURE_AIRPORT_CITY: DecoderKey[AirportName] = DecoderKey([5])
    ARRIVAL_AIRPORT: DecoderKey[AirportCode] = DecoderKey([2])
    ARRIVAL_AIRPORT_NAME: DecoderKey[AirportName] = DecoderKey([6])
    ARRIVAL_AIRPORT_CITY: DecoderKey[AirportName] = DecoderKey([7])

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Layover]:
        return [Layover(**cls.decode_el(NLData(el))) for el in root]

class ItineraryDecoder(Decoder):
    AIRLINE_CODE: DecoderKey[AirlineCode] = DecoderKey([0, 0])
    AIRLINE_NAMES: DecoderKey[List[AirlineName]] = DecoderKey([0, 1])
    FLIGHTS: DecoderKey[List[Flight]] = DecoderKey([0, 2], FlightDecoder.decode)
    DEPARTURE_AIRPORT: DecoderKey[AirportCode] = DecoderKey([0, 3])
    DEPARTURE_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([0, 4])
    DEPARTURE_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([0, 5], normalize_time)
    ARRIVAL_AIRPORT: DecoderKey[AirportCode] = DecoderKey([0, 6])
    ARRIVAL_DATE: DecoderKey[Tuple[int, int, int]] = DecoderKey([0, 7])
    ARRIVAL_TIME: DecoderKey[Tuple[int, int]] = DecoderKey([0, 8], normalize_time)
    TRAVEL_TIME: DecoderKey[int] = DecoderKey([0, 9])
    # UNKNOWN: DecoderKey[int] = DecoderKey([0, 10])
    LAYOVERS: DecoderKey[List[Layover]] = DecoderKey([0, 13], LayoverDecoder.decode)
    # first field of protobuf is the same as [0, 4] on the root? seems like 0,4 is for tracking
    # contains a summary of the flight numbers and the price (as a fixed point sint)
    ITINERARY_SUMMARY: DecoderKey[ItinerarySummary] = DecoderKey([1], lambda data: ItinerarySummary.from_b64(data[1]))
    # contains Flight(s), the price, and a few more
    # FLIGHTS_PROTOBUF: DecoderKey[ProtobufStr] = DecoderKey([8])
    # some struct containing emissions info
    # EMISSIONS: DecoderKey[Emissions] = DecoderKey([22])

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData]) -> List[Itinerary]:
        # Filter decoration entries (e.g. injected travel-restriction
        # warnings) so they don't crash decode_el's [0, 0] traversal.
        # Log unrecognized non-itinerary entries to stderr — silent drops
        # of legitimate itineraries with surprising shapes are worse than
        # the original crash.
        out: List[Itinerary] = []
        for i, el in enumerate(root):
            if _is_itinerary_entry(el):
                try:
                    out.append(Itinerary(**cls.decode_el(NLData(el))))
                except Exception as exc:
                    preview = repr(el)[:200]
                    print(
                        f"[fast_flights] ItineraryDecoder skipped undecodable "
                        f"entry at index {i}: {type(exc).__name__}: {exc}; {preview}",
                        file=sys.stderr,
                        flush=True,
                    )
                continue
            if _parse_travel_warning(el) is None:
                preview = repr(el)[:200]
                print(
                    f"[fast_flights] ItineraryDecoder skipped unrecognized entry "
                    f"at index {i}: {preview}",
                    file=sys.stderr,
                    flush=True,
                )
        return out


class ResultDecoder(Decoder):
    # UNKNOWN_1: DecoderKey[Any] = DecoderKey([0])
    # AIRPORT_DETAILS: DecoderKey[Any] = DecoderKey([1])
    BEST: DecoderKey[List[Itinerary]] = DecoderKey([2, 0], ItineraryDecoder.decode)
    OTHER: DecoderKey[List[Itinerary]] = DecoderKey([3, 0], ItineraryDecoder.decode)

    @classmethod
    @override
    def decode(cls, root: Union[list, NLData], tfu: str = "EgQIABABIgA") -> DecodedResult:
        assert isinstance(root, list), 'Root data must be list type'
        result_data = cls.decode_el(NLData(root))

        # Add tfu to each itinerary
        for itinerary in result_data.get('best', []):
            itinerary.tfu = tfu
        for itinerary in result_data.get('other', []):
            itinerary.tfu = tfu

        # Extract price insights from data[5] if present
        price_insights = None
        if len(root) > 5 and root[5] is not None:
            price_insights = PriceInsights.from_raw(root[5])

        # Collect travel warnings from both placements Google uses:
        #   * data[22][*] — top-level advisory list
        #   * non-itinerary siblings inside data[2][0] / data[3][0]
        warnings: List[TravelWarning] = []
        for idx in (2, 3):
            if idx < len(root) and isinstance(root[idx], list) and root[idx] and isinstance(root[idx][0], list):
                for el in root[idx][0]:
                    if not _is_itinerary_entry(el):
                        parsed = _parse_travel_warning(el)
                        if parsed is not None:
                            warnings.append(parsed)
        if len(root) > 22 and isinstance(root[22], list):
            for el in root[22]:
                parsed = _parse_travel_warning(el)
                if parsed is not None:
                    warnings.append(parsed)

        return DecodedResult(**result_data, raw=root, price_insights=price_insights, warnings=warnings)
