"""Tests for the validation module."""

import pytest
from marshmallow import ValidationError

from pyenvgen.schema import EnvSchema
from pyenvgen.validation import validate_env


class TestValidateEnv:
    def test_valid_values(self) -> None:
        schema = EnvSchema.model_validate(
            {
                "variables": {
                    "PORT": {
                        "type": "int",
                        "generation": {"rule": "default", "value": "8080"},
                        "validation": {"range": {"min": 1, "max": 65535}},
                    },
                    "NAME": {
                        "type": "str",
                        "generation": {"rule": "default", "value": "app"},
                        "validation": {"length": {"min": 1}},
                    },
                }
            }
        )
        result = validate_env(schema, {"PORT": "8080", "NAME": "app"})
        assert result["PORT"] == 8080
        assert result["NAME"] == "app"

    def test_type_casting(self) -> None:
        schema = EnvSchema.model_validate(
            {
                "variables": {
                    "ENABLED": {
                        "type": "bool",
                        "generation": {"rule": "default", "value": "true"},
                    },
                    "RATE": {
                        "type": "float",
                        "generation": {"rule": "default", "value": "3.14"},
                    },
                }
            }
        )
        result = validate_env(schema, {"ENABLED": "true", "RATE": "3.14"})
        assert result["ENABLED"] is True
        assert result["RATE"] == pytest.approx(3.14)

    def test_one_of_validation_rejects_invalid(self) -> None:
        schema = EnvSchema.model_validate(
            {
                "variables": {
                    "LEVEL": {
                        "type": "str",
                        "generation": {"rule": "default", "value": "INFO"},
                        "validation": {
                            "one_of": {"choices": ["DEBUG", "INFO", "ERROR"]}
                        },
                    }
                }
            }
        )
        with pytest.raises(ValidationError):
            validate_env(schema, {"LEVEL": "INVALID"})

    def test_range_validation_rejects_out_of_bounds(self) -> None:
        schema = EnvSchema.model_validate(
            {
                "variables": {
                    "PORT": {
                        "type": "int",
                        "generation": {"rule": "default", "value": "80"},
                        "validation": {"range": {"min": 1, "max": 1024}},
                    }
                }
            }
        )
        with pytest.raises(ValidationError):
            validate_env(schema, {"PORT": "99999"})
