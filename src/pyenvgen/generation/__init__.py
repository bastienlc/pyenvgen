"""Generation module – produces environment variable values from schemas.

Each generation rule has a corresponding function that takes the variable
schema and (optionally) existing values, and returns the generated string.
"""

from __future__ import annotations

from pyenvgen.schema import DefaultGeneration, EnvSchema, GenerationRule


def _generate_default(rule: DefaultGeneration) -> str:
    """Return the literal default value from the schema."""
    return rule.value


_GENERATORS: dict[str, object] = {
    "default": _generate_default,
}


def generate_value(
    rule: GenerationRule,
    existing: dict[str, str] | None = None,
) -> str:
    """Dispatch to the appropriate generator for *rule*.

    Parameters
    ----------
    rule
        The generation rule from the variable schema.
    existing
        Already-generated values (useful for template rule in the future).

    Returns
    -------
    str
        The generated value as a string (will be validated/cast later).
    """
    if rule.rule == "default":
        assert isinstance(rule, DefaultGeneration)
        return _generate_default(rule)

    raise NotImplementedError(
        f"Generation rule '{rule.rule}' is not yet implemented"
    )


def generate_env(
    schema: EnvSchema,
    overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Generate all environment variable values from *schema*.

    Parameters
    ----------
    schema
        The parsed environment schema.
    overrides
        Values that take precedence over generated ones (e.g. from an
        existing .env file or CLI arguments).

    Returns
    -------
    dict[str, str]
        Mapping of variable name → generated string value.
    """
    overrides = overrides or {}
    result: dict[str, str] = {}

    for name, var_schema in schema.variables.items():
        if name in overrides:
            result[name] = overrides[name]
        else:
            result[name] = generate_value(var_schema.generation, existing=result)

    return result
