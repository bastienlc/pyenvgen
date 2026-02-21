"""Validation module – bridges pyenvgen schemas to marshmallow.

Validates a dict of generated key-value pairs against the variable schemas
using marshmallow for type casting and validation.
"""

from __future__ import annotations

from typing import Any

from marshmallow import Schema, fields, validate as ma_validate

from pyenvgen.schema import EnvSchema, ValidationRules, VarType


def _build_marshmallow_validators(rules: ValidationRules) -> list[Any]:
    """Convert our Pydantic validation rules into marshmallow validators."""
    validators: list[Any] = []

    if rules.length is not None:
        validators.append(
            ma_validate.Length(min=rules.length.min, max=rules.length.max)
        )

    if rules.range is not None:
        validators.append(
            ma_validate.Range(
                min=rules.range.min,
                max=rules.range.max,
                min_inclusive=rules.range.min_inclusive,
                max_inclusive=rules.range.max_inclusive,
            )
        )

    if rules.one_of is not None:
        validators.append(ma_validate.OneOf(rules.one_of.choices))

    if rules.regexp is not None:
        validators.append(ma_validate.Regexp(rules.regexp.pattern))

    return validators


# Map VarType → marshmallow field class
_TYPE_FIELD: dict[VarType, type[fields.Field]] = {
    VarType.STR: fields.String,
    VarType.INT: fields.Integer,
    VarType.FLOAT: fields.Float,
    VarType.BOOL: fields.Boolean,
}


def validate_env(schema: EnvSchema, values: dict[str, str]) -> dict[str, Any]:
    """Validate *values* against *schema* using marshmallow.

    Builds a marshmallow ``Schema`` dynamically from the variable definitions,
    then deserialises *values* through it for type casting and constraint
    checking.

    Returns
    -------
    dict[str, Any]
        The validated (and type-cast) values.

    Raises
    ------
    marshmallow.ValidationError
        If any value fails validation.
    """
    field_map: dict[str, fields.Field] = {}
    for name, var_schema in schema.variables.items():
        field_cls = _TYPE_FIELD[var_schema.type]
        validators = _build_marshmallow_validators(var_schema.validation)
        field_map[name] = field_cls(required=True, validate=validators)

    ma_schema = Schema.from_dict(field_map)()
    return ma_schema.load(values)
