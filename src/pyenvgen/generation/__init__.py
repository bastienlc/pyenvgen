"""Generation module – produces environment variable values from schemas.

Each generation rule lives in its own submodule:
- ``default``  → :mod:`pyenvgen.generation.default`
- ``command``  → :mod:`pyenvgen.generation.command`
- ``openssl``  → :mod:`pyenvgen.generation.openssl`

All rule string fields are rendered as Jinja2 templates against the set of
already-generated variables *before* the rule is executed.  This means any
rule can reference other variables using ``{{ VAR_NAME }}`` syntax, removing
the need for a separate ``template`` rule.

This package exposes the public API: :func:`generate_value` and
:func:`generate_env`.  It also handles topological ordering so that
variables whose Jinja templates reference others are always generated after
the variables they depend on.
"""

from __future__ import annotations

from graphlib import CycleError, TopologicalSorter

import jinja2
import jinja2.meta

from pyenvgen.schema import (
    CommandGeneration,
    DefaultGeneration,
    EnvSchema,
    GenerationRule,
    OpenSSLGeneration,
)

from pyenvgen.generation.command import generate_command
from pyenvgen.generation.default import generate_default
from pyenvgen.generation.openssl import generate_openssl


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CircularDependencyError(Exception):
    """Raised when variables form a circular Jinja dependency."""


# ---------------------------------------------------------------------------
# Jinja helpers
# ---------------------------------------------------------------------------


def _render_string(s: str, existing: dict[str, str]) -> str:
    """Render *s* as a Jinja2 template against *existing* values."""
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    return env.from_string(s).render(**existing)


def _jinja_deps(s: str, all_names: set[str]) -> set[str]:
    """Return schema variable names referenced in Jinja template string *s*."""
    env = jinja2.Environment()
    ast = env.parse(s)
    refs = jinja2.meta.find_undeclared_variables(ast)
    return refs & all_names


def _rule_template_strings(rule: GenerationRule) -> list[str]:
    """Return all string fields of *rule* that may contain Jinja templates."""
    if isinstance(rule, DefaultGeneration):
        return [rule.value]
    if isinstance(rule, CommandGeneration):
        return [rule.command]
    if isinstance(rule, OpenSSLGeneration):
        strings = [rule.command]
        strings.extend(v for v in rule.args.values() if isinstance(v, str))
        return strings
    return []  # pragma: no cover


def _rule_jinja_deps(rule: GenerationRule, all_names: set[str]) -> set[str]:
    """Find all schema variable names referenced in Jinja templates within *rule*."""
    deps: set[str] = set()
    for s in _rule_template_strings(rule):
        deps |= _jinja_deps(s, all_names)
    return deps


def _render_rule(rule: GenerationRule, existing: dict[str, str]) -> GenerationRule:
    """Return a copy of *rule* with all string fields Jinja-rendered against *existing*."""
    if isinstance(rule, DefaultGeneration):
        return rule.model_copy(update={"value": _render_string(rule.value, existing)})
    if isinstance(rule, CommandGeneration):
        return rule.model_copy(update={"command": _render_string(rule.command, existing)})
    if isinstance(rule, OpenSSLGeneration):
        rendered_args = {
            k: _render_string(v, existing) if isinstance(v, str) else v
            for k, v in rule.args.items()
        }
        return rule.model_copy(
            update={
                "command": _render_string(rule.command, existing),
                "args": rendered_args,
            }
        )
    return rule  # pragma: no cover


# ---------------------------------------------------------------------------
# Topological ordering
# ---------------------------------------------------------------------------


def _topological_order(schema: EnvSchema) -> list[str]:
    """Return variable names in a safe generation order.

    Every rule's string fields are scanned for Jinja variable references.
    A variable X depends on Y if any of X's template strings reference Y.

    Raises
    ------
    CircularDependencyError
        If the dependency graph contains a cycle.
    """
    all_names = set(schema.variables)

    deps: dict[str, set[str]] = {
        name: _rule_jinja_deps(var.generation, all_names)
        for name, var in schema.variables.items()
    }

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

    Before dispatching, all string fields in *rule* are rendered as Jinja2
    templates against *existing* so that any rule may reference previously
    generated variables.

    Parameters
    ----------
    rule
        The generation rule from the variable schema.
    existing
        Already-generated values used for Jinja template rendering.

    Returns
    -------
    str
        The generated value as a string (will be validated/cast later).
    """
    existing = existing or {}
    rule = _render_rule(rule, existing)

    if rule.rule == "default":
        assert isinstance(rule, DefaultGeneration)
        return generate_default(rule)
    if rule.rule == "command":
        assert isinstance(rule, CommandGeneration)
        return generate_command(rule)
    if rule.rule == "openssl":
        assert isinstance(rule, OpenSSLGeneration)
        return generate_openssl(rule)

    raise NotImplementedError(f"Generation rule '{rule.rule}' is not yet implemented")  # pragma: no cover


def generate_env(
    schema: EnvSchema,
    overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Generate all environment variable values from *schema*.

    Variables are generated in topological order so that Jinja templates can
    safely reference other variables.

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
