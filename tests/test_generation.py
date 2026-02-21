"""Tests for the generation module."""

import pytest

from pyenvgen.generation import generate_env, generate_value
from pyenvgen.schema import (
    CommandGeneration,
    DefaultGeneration,
    EnvSchema,
)


class TestGenerateValue:
    def test_default_rule(self) -> None:
        rule = DefaultGeneration(value="hello")
        assert generate_value(rule) == "hello"

    def test_unimplemented_rule_raises(self) -> None:
        rule = CommandGeneration(command="echo hi")
        with pytest.raises(NotImplementedError, match="command"):
            generate_value(rule)


class TestGenerateEnv:
    def test_generates_all_defaults(self) -> None:
        schema = EnvSchema.model_validate(
            {
                "variables": {
                    "A": {"generation": {"rule": "default", "value": "1"}},
                    "B": {"generation": {"rule": "default", "value": "2"}},
                }
            }
        )
        result = generate_env(schema)
        assert result == {"A": "1", "B": "2"}

    def test_overrides_take_precedence(self) -> None:
        schema = EnvSchema.model_validate(
            {
                "variables": {
                    "A": {"generation": {"rule": "default", "value": "1"}},
                }
            }
        )
        result = generate_env(schema, overrides={"A": "override"})
        assert result == {"A": "override"}
