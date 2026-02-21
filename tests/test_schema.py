"""Tests for the schema module."""

import pytest
from pydantic import ValidationError

from pyenvgen.schema import (
    DefaultGeneration,
    EnvSchema,
    VarType,
    VariableSchema,
)


class TestVariableSchema:
    def test_minimal_variable(self) -> None:
        var = VariableSchema(generation=DefaultGeneration(value="hello"))
        assert var.type == VarType.STR
        assert var.required is True
        assert var.internal is False
        assert var.generation.value == "hello"

    def test_int_variable_with_range(self) -> None:
        raw = {
            "type": "int",
            "generation": {"rule": "default", "value": "42"},
            "validation": {"range": {"min": 0, "max": 100}},
        }
        var = VariableSchema.model_validate(raw)
        assert var.type == VarType.INT
        assert var.validation.range is not None
        assert var.validation.range.min == 0

    def test_discriminated_union_default(self) -> None:
        raw = {
            "generation": {"rule": "default", "value": "x"},
        }
        var = VariableSchema.model_validate(raw)
        assert isinstance(var.generation, DefaultGeneration)

    def test_unknown_rule_rejected(self) -> None:
        raw = {
            "generation": {"rule": "magic", "value": "x"},
        }
        with pytest.raises(ValidationError):
            VariableSchema.model_validate(raw)


class TestEnvSchema:
    def test_valid_schema(self) -> None:
        raw = {
            "variables": {
                "PORT": {
                    "type": "int",
                    "generation": {"rule": "default", "value": "8080"},
                    "validation": {"range": {"min": 1, "max": 65535}},
                }
            }
        }
        schema = EnvSchema.model_validate(raw)
        assert "PORT" in schema.variables

    def test_range_on_str_rejected(self) -> None:
        raw = {
            "variables": {
                "NAME": {
                    "type": "str",
                    "generation": {"rule": "default", "value": "x"},
                    "validation": {"range": {"min": 1, "max": 10}},
                }
            }
        }
        with pytest.raises(ValidationError, match="range"):
            EnvSchema.model_validate(raw)

    def test_length_on_int_rejected(self) -> None:
        raw = {
            "variables": {
                "PORT": {
                    "type": "int",
                    "generation": {"rule": "default", "value": "80"},
                    "validation": {"length": {"min": 1}},
                }
            }
        }
        with pytest.raises(ValidationError, match="length"):
            EnvSchema.model_validate(raw)
