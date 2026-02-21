"""Template generation rule – renders a Jinja2 template against existing values."""

from __future__ import annotations

import jinja2
import jinja2.meta

from pyenvgen.schema import TemplateGeneration


def generate_template(rule: TemplateGeneration, existing: dict[str, str]) -> str:
    """Render *rule.template* as a Jinja2 template against *existing* values."""
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    tmpl = env.from_string(rule.template)
    return tmpl.render(**existing)


def template_deps(template_str: str, all_names: set[str]) -> set[str]:
    """Return the variable names referenced in a Jinja2 template string.

    Only returns names that appear in *all_names* (i.e. declared schema variables).
    """
    env = jinja2.Environment()
    ast = env.parse(template_str)
    refs = jinja2.meta.find_undeclared_variables(ast)
    return refs & all_names
