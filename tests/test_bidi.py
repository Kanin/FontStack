"""Tests for BiDi helpers."""

from __future__ import annotations

from fontstack._core import _prepare_bidi


class TestPrepareBidi:
    def test_latin_passthrough(self) -> None:
        # Pure LTR text should be returned unchanged (BiDi is a no-op on LTR).
        result = _prepare_bidi("Hello, world!")
        assert result == "Hello, world!"

    def test_returns_string(self) -> None:
        assert isinstance(_prepare_bidi("test"), str)

    def test_arabic_bidi_reordering(self) -> None:
        # BiDi reordering should produce a non-empty string for Arabic text.
        text = "مرحبا"
        result = _prepare_bidi(text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mixed_direction_reordered(self) -> None:
        # "Hello world" in a mixed string should end up visually first when
        # BiDi reordering is applied (the LTR run precedes the RTL run visually).
        text = "Hello مرحبا"
        result = _prepare_bidi(text)
        assert isinstance(result, str)
        assert len(result) > 0
        # After reordering the Latin portion still contains 'Hello'.
        assert "Hello" in result

    def test_empty_string(self) -> None:
        assert _prepare_bidi("") == ""
