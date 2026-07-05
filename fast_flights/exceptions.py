"""Public exception types raised by fast_flights."""


class GoogleFlightsErrorResponse(RuntimeError):
    """Google returned a typed Flights ErrorResponse instead of itineraries."""

    def __init__(self, *, sha256: str, byte_count: int, char_count: int):
        self.sha256 = sha256
        self.byte_count = byte_count
        self.char_count = char_count
        super().__init__(
            "Google Flights returned ErrorResponse payload "
            f"(raw ds:1 dumped to stderr; sha256={sha256}; "
            f"bytes={byte_count}; chars={char_count})"
        )
