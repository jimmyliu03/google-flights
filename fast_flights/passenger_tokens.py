"""Read or repair passenger fields without reserializing Google's opaque fields."""
import base64
from .flights_impl import Passengers


def _varint(raw, offset):
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(raw):
            break
        byte = raw[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
    raise ValueError("Invalid TFS varint")


def _fields(tfs):
    try:
        raw = base64.b64decode(tfs + '=' * (-len(tfs) % 4), altchars=b'-_', validate=True)
    except Exception as exc:
        raise ValueError("Invalid TFS encoding") from exc
    offset = 0
    while offset < len(raw):
        start = offset
        key, offset = _varint(raw, offset)
        field, wire = key >> 3, key & 7
        if field == 0:
            raise ValueError("Invalid TFS field")
        values = []
        if wire == 0:
            value, offset = _varint(raw, offset)
            values = [value]
        elif wire == 2:
            size, offset = _varint(raw, offset)
            end = offset + size
            if field == 8:
                while offset < end:
                    value, offset = _varint(raw, offset)
                    values.append(value)
                if offset != end:
                    raise ValueError("Invalid packed passengers")
            offset = end
        elif wire in (1, 5):
            offset += 8 if wire == 1 else 4
        else:
            raise ValueError("Unsupported TFS wire type")
        if offset > len(raw):
            raise ValueError("Truncated TFS field")
        if field == 8 and wire not in (0, 2):
            raise ValueError("Invalid passenger field")
        yield field, values, raw[start:offset]


def get_passengers_from_tfs(tfs: str) -> Passengers:
    """Decode and validate the complete party (packed or unpacked field 8)."""
    values = [value for field, items, _ in _fields(tfs) if field == 8 for value in items]
    if not values or any(value not in (1, 2, 3, 4) for value in values):
        raise ValueError("Missing or invalid TFS passengers")
    return Passengers(adults=values.count(1), children=values.count(2),
                      infants_in_seat=values.count(3), infants_on_lap=values.count(4))


def set_passengers_in_tfs(tfs: str, passengers: Passengers) -> str:
    """Replace field 8; retain all other fields byte for byte."""
    if not tfs:
        raise ValueError("Missing TFS")
    retained = []
    insertion = None
    for field, _, raw in _fields(tfs):
        if field == 8:
            if insertion is None:
                insertion = len(retained)
        else:
            retained.append(raw)
    replacement = [bytes((0x40, value)) for value in passengers.pb]
    index = len(retained) if insertion is None else insertion
    retained[index:index] = replacement
    return base64.urlsafe_b64encode(b''.join(retained)).rstrip(b'=').decode()
