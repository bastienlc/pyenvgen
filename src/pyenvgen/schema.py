"""Pydantic models for the pyenvgen YAML schema.

The schema defines:
- Variable type (for marshmallow validation)
- Generation rule (how to produce the value)
- Validation constraints (mapped to marshmallow validators)
- Special properties (e.g. internal)
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Variable types
# ---------------------------------------------------------------------------


class VarType(str, Enum):
    """Supported environment variable types."""

    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"


# ---------------------------------------------------------------------------
# Validation rules – each maps to a marshmallow validator
# ---------------------------------------------------------------------------


class LengthValidation(BaseModel):
    """Maps to marshmallow.validate.Length."""

    min: int | None = None
    max: int | None = None


class RangeValidation(BaseModel):
    """Maps to marshmallow.validate.Range (for int / float)."""

    min: float | None = None
    max: float | None = None
    min_inclusive: bool = True
    max_inclusive: bool = True


class OneOfValidation(BaseModel):
    """Maps to marshmallow.validate.OneOf."""

    choices: list[str]


class RegexpValidation(BaseModel):
    """Maps to marshmallow.validate.Regexp."""

    pattern: str


class ValidationRules(BaseModel):
    """Container for all validation constraints on a single variable.

    All fields are optional – omitting a field means no constraint of that kind.
    """

    length: LengthValidation | None = None
    range: RangeValidation | None = None
    one_of: OneOfValidation | None = None
    regexp: RegexpValidation | None = None


# ---------------------------------------------------------------------------
# Generation rules – discriminated union for future extensibility
# ---------------------------------------------------------------------------


class DefaultGeneration(BaseModel):
    """Use a default value specified in the schema.

    The ``value`` string is rendered as a Jinja2 template before being
    returned, so it may reference other already-generated variables.
    """

    rule: Literal["default"] = "default"
    value: str


class CommandGeneration(BaseModel):
    """Generate value by executing a shell command.

    The ``command`` string is rendered as a Jinja2 template before execution,
    so it may reference other already-generated variables.
    """

    rule: Literal["command"] = "command"
    command: str


class OpenSSLGeneration(BaseModel):
    """Generate value using an OpenSSL command.

    The ``command`` string and any string values inside ``args`` are rendered
    as Jinja2 templates before execution.
    """

    rule: Literal["openssl"] = "openssl"
    command: str
    args: dict[str, Any] = Field(default_factory=dict)


GenerationRule = Annotated[
    Union[DefaultGeneration, CommandGeneration, OpenSSLGeneration],
    Field(discriminator="rule"),
]

# ---------------------------------------------------------------------------
# Variable definition
# ---------------------------------------------------------------------------


class VariableSchema(BaseModel):
    """Full definition of a single environment variable."""

    type: VarType = VarType.STR
    generation: GenerationRule
    validation: ValidationRules = Field(default_factory=ValidationRules)
    internal: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# Top-level schema
# ---------------------------------------------------------------------------


class EnvSchema(BaseModel):
    """Root schema loaded from the YAML file."""

    variables: dict[str, VariableSchema]

    @model_validator(mode="after")
    def _check_validation_matches_type(self) -> EnvSchema:
        """Ensure validation rules are compatible with the declared type."""
        for name, var in self.variables.items():
            if var.validation.range is not None and var.type not in (
                VarType.INT,
                VarType.FLOAT,
            ):
                raise ValueError(
                    f"Variable '{name}': 'range' validation is only valid "
                    f"for int/float types, got '{var.type.value}'"
                )
            if var.validation.length is not None and var.type != VarType.STR:
                raise ValueError(
                    f"Variable '{name}': 'length' validation is only valid "
                    f"for str type, got '{var.type.value}'"
                )
        return self
