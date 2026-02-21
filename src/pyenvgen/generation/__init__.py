"""Generation module – produces environment variable values from schemas.

Each generation rule lives in its own submodule:
- ``default``  → :mod:`pyenvgen.generation.default`
- ``command``  → :mod:`pyenvgen.generation.command`
- ``template`` → :mod:`pyenvgen.generation.template`
- ``openssl``  → :mod:`pyenvgen.generation.openssl`

This package exposes the public API: :func:`generate_value` and
:func:`generate_env`.  It also handles topological ordering so that
``template`` variables are always generated after the variables they
reference.
"""

from __future__ import annotations

from graphlib import CycleError, TopologicalSorter

from pyenvgen.schema import (
    CommandGeneration,
    DefaultGeneration,
    EnvSchema,
    GenerationRule,
    OpenSSLGeneration,
    TemplateGeneration,
)

from pyenvgen.generation.command import generate_command
from pyenvgen.generation.default import generate_default
from pyenvgen.generation.openssl import generate_openssl
from pyenvgen.generation.template import generate_template, template_deps


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CircularDependencyError(Exception):
    """Raised when template variables form a circular dependency."""


# ---------------------------------------------------------------------------
# Topological ordering
# ---------------------------------------------------------------------------


def _topological_order(schema: EnvSchema) -> list[str]:
    """Return variable names in a safe generation order.

    Non-template variables have no dependencies and are treated as roots.
    Template variables depend on every variable name they reference.

    Raises
    ------
    CircularDependencyError
        If the dependency graph contains a cycle.
    """
    all_names = set(schema.variables)

    # Build dependency map: name -> set of names that must be generated first
    deps: dict[str, set[str]] = {}
    for name, var in schema.variables.items():
        if var.generation.rule == "template":
            assert isinstance(var.generation, TemplateGeneration)
            deps[name] = template_deps(var.generation.template, all_names)
        else:
            deps[name] = set()

    try:
        return list(TopologicalSorter(deps).static_order())
    except CycleError as exc:
        raise CircularDependencyError(
            f"Circular dependency detected among variables: {exc.args[1]}"
        ) from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


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
        Already-generated values (required for the ``template`` rule).

    Returns
    -------
    str
        The generated value as a string (will be validated/cast later).
    """
    existing = existing or {}
    if rule.rule == "default":
        assert isinstance(rule, DefaultGeneration)
        return generate_default(rule)
    if rule.rule == "command":
        assert isinstance(rule, CommandGeneration)
        return generate_command(rule)
    if rule.rule == "template":
        assert isinstance(rule, TemplateGeneration)
        return generate_template(rule, existing)
    if rule.rule == "openssl":
        assert isinstance(rule, OpenSSLGeneration)
        return generate_openssl(rule)

    raise NotImplementedError(f"Generation rule '{rule.rule}' is not yet implemented")


def generate_env(
    schema: EnvSchema,
    overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Generate all environment variable values from *schema*.

    Variables are generated in topological order so templates can safely
    reference other variables.

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

    for name in _topological_order(schema):
        if name in overrides:
            result[name] = overrides[name]
        else:
            result[name] = generate_value(
                schema.variables[name].generation, existing=result
            )

    return result
