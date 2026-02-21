"""Tests for the default generation rule."""

from __future__ import annotations

from pyenvgen.generation import generate_value
from pyenvgen.schema import DefaultGeneration


class TestGenerateValueDefault:
    def test_returns_value(self) -> None:
        rule = DefaultGeneration(value="hello")
        assert generate_value(rule) == "hello"

    def test_empty_string(self) -> None:
        rule = DefaultGeneration(value="")
        assert generate_value(rule) == ""
