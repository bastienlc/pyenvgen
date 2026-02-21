"""Tests for the template generation rule and template dependency detection."""

from __future__ import annotations

import pytest

from pyenvgen.generation import generate_value
from pyenvgen.generation.template import template_deps
from pyenvgen.schema import TemplateGeneration


class TestGenerateValueTemplate:
    def test_simple_substitution(self) -> None:
        rule = TemplateGeneration(template="{{ HOST }}:{{ PORT }}")
        result = generate_value(rule, existing={"HOST": "localhost", "PORT": "5432"})
        assert result == "localhost:5432"

    def test_no_substitution(self) -> None:
        rule = TemplateGeneration(template="static-value")
        assert generate_value(rule, existing={}) == "static-value"

    def test_missing_variable_raises(self) -> None:
        rule = TemplateGeneration(template="{{ MISSING }}")
        with pytest.raises(Exception):
            generate_value(rule, existing={})

    def test_arithmetic_expression(self) -> None:
        rule = TemplateGeneration(template="{{ VALUE | int + 1 }}")
        assert generate_value(rule, existing={"VALUE": "41"}) == "42"


class TestTemplateDeps:
    def test_simple(self) -> None:
        deps = template_deps("{{ A }} and {{ B }}", {"A", "B", "C"})
        assert deps == {"A", "B"}

    def test_only_known_vars(self) -> None:
        # UNKNOWN is not in the schema so it should be filtered out
        deps = template_deps("{{ A }} {{ UNKNOWN }}", {"A", "B"})
        assert deps == {"A"}

    def test_no_vars(self) -> None:
        assert template_deps("static", {"A", "B"}) == set()
