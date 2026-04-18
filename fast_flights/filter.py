from typing import Literal, List, Optional
from .flights_impl import FlightData, Passengers, TFSData

def create_filter(
    *,
    flight_data: List[FlightData],
    trip: Literal["round-trip", "one-way", "multi-city"],
    passengers: Passengers,
    seat: Literal["economy", "premium-economy", "business", "first"],
    max_stops: Optional[int] = None,
    exclude_basic_economy: bool = False,
) -> TFSData:
    """Create a filter. (``?tfs=``)

    Args:
        flight_data (list[FlightData]): Flight data as a list.
        trip ("one-way" | "round-trip" | "multi-city"): Trip type.
        passengers (Passengers): Passengers.
        seat ("economy" | "premium-economy" | "business" | "first"): Seat.
        max_stops (int, optional): Maximum number of stops. Defaults to None.
        exclude_basic_economy (bool, optional): Exclude basic economy fares. Defaults to False.
    """
    # Only fan the top-level max_stops out to each leg when the caller
    # actually provided one. The previous unconditional override silently
    # wiped per-leg FlightData(max_stops=N) settings whenever the caller
    # forgot to also pass create_filter(max_stops=N) — turning Nonstop
    # filters into no-op TFS strings (verified via Chrome reverse-engineering
    # against SFO→NYC May 19: nonstop+unfiltered produced byte-identical TFS).
    if max_stops is not None:
        for fd in flight_data:
            fd.max_stops = max_stops

    return TFSData.from_interface(
        flight_data=flight_data,
        trip=trip,
        passengers=passengers,
        seat=seat,
        exclude_basic_economy=exclude_basic_economy,
    )
