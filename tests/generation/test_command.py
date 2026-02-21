"""Tests for the command generation rule."""

from __future__ import annotations

import pytest

from pyenvgen.generation import generate_value
from pyenvgen.schema import CommandGeneration


class TestGenerateValueCommand:
    def test_echo(self) -> None:
        rule = CommandGeneration(command="echo hello")
        assert generate_value(rule) == "hello"

    def test_strips_trailing_newline(self) -> None:
        rule = CommandGeneration(command="printf 'world\\n'")
        assert generate_value(rule) == "world"

    def test_multiword_output(self) -> None:
        rule = CommandGeneration(command="echo -n foo")
        assert generate_value(rule) == "foo"

    def test_failed_command_raises(self) -> None:
        rule = CommandGeneration(command="exit 1")
        with pytest.raises(Exception):
            generate_value(rule)
