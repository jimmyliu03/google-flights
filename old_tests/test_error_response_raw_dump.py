import hashlib
import json

import pytest

from fast_flights import core


class _Response:
    def __init__(self, text: str):
        self.text = text


def test_error_response_payload_is_dumped_before_decoding(monkeypatch, capsys):
    raw_payload = json.dumps(
        [
            "type.googleapis.com/travel.frontend.flights.ErrorResponse",
            [
                [
                    None,
                    [[1783229001196007, 44793028, 186418482], None, None, None, None, [[0]]],
                    0,
                    "SepJaqf7C8T5rcUPsoryWA",
                    "HLLtqUXTmDdQAMMg4gBG---------vwkl16AAAAAGpJ6kkDI5PSA",
                ],
                0,
            ],
        ],
        separators=(",", ":"),
    )
    html = (
        "<html><body>"
        f"<script class=\"ds:1\">AF_initDataCallback({{key:'ds:1',data:{raw_payload},sideChannel:{{}}}});</script>"
        "</body></html>"
    )
    decode_called = False

    def fail_if_called(*_args, **_kwargs):
        nonlocal decode_called
        decode_called = True
        raise AssertionError("decoder should not be called for ErrorResponse payloads")

    monkeypatch.setattr(core.ResultDecoder, "decode", fail_if_called)

    with pytest.raises(RuntimeError, match="Google Flights returned ErrorResponse payload"):
        core.parse_response(_Response(html), "js")

    stderr = capsys.readouterr().err
    digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    assert decode_called is False
    assert f"sha256={digest}" in stderr
    assert "[fast_flights][ERROR_RESPONSE_RAW][BEGIN]" in stderr
    assert f"[fast_flights][ERROR_RESPONSE_RAW][1/1] {raw_payload}" in stderr
    assert "[fast_flights][ERROR_RESPONSE_RAW][END]" in stderr
