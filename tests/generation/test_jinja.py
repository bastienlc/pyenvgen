"""Tests for Jinja2 pre-rendering applied across all generation rules."""

from __future__ import annotations

import pytest

from pyenvgen.generation import generate_value, _jinja_deps, _rule_jinja_deps
from pyenvgen.schema import CommandGeneration, DefaultGeneration, OpenSSLGeneration


class TestDefaultJinja:
    def test_simple_substitution(self) -> None:
        rule = DefaultGeneration(value="{{ HOST }}:{{ PORT }}")
        result = generate_value(rule, existing={"HOST": "localhost", "PORT": "5432"})
        assert result == "localhost:5432"

    def test_no_template_syntax(self) -> None:
        rule = DefaultGeneration(value="static-value")
        assert generate_value(rule, existing={}) == "static-value"

    def test_missing_variable_raises(self) -> None:
        rule = DefaultGeneration(value="{{ MISSING }}")
        with pytest.raises(Exception):
            generate_value(rule, existing={})

    def test_arithmetic_expression(self) -> None:
        rule = DefaultGeneration(value="{{ VALUE | int + 1 }}")
        assert generate_value(rule, existing={"VALUE": "41"}) == "42"

    def test_multiple_vars(self) -> None:
        rule = DefaultGeneration(value="postgres://{{ HOST }}:{{ PORT }}/{{ DB }}")
        result = generate_value(
            rule, existing={"HOST": "db", "PORT": "5432", "DB": "mydb"}
        )
        assert result == "postgres://db:5432/mydb"


class TestCommandJinja:
    def test_command_uses_existing_var(self) -> None:
        rule = CommandGeneration(command="echo {{ GREETING }}")
        result = generate_value(rule, existing={"GREETING": "hello"})
        assert result == "hello"

    def test_command_without_template(self) -> None:
        rule = CommandGeneration(command="echo world")
        assert generate_value(rule, existing={}) == "world"

    def test_missing_var_in_command_raises(self) -> None:
        rule = CommandGeneration(command="echo {{ MISSING }}")
        with pytest.raises(Exception):
            generate_value(rule, existing={})


class TestOpenSSLJinja:
    def test_openssl_command_field_rendered(self) -> None:
        """The command field is Jinja-rendered; here it stays 'fernet'."""
        rule = OpenSSLGeneration(command="{{ KEY_TYPE }}", args={})
        result = generate_value(rule, existing={"KEY_TYPE": "fernet"})
        # Fernet key is a non-empty base64 string
        assert len(result) > 0

    def test_openssl_args_string_rendered(self) -> None:
        """String values in args are Jinja-rendered before execution."""
        rule = OpenSSLGeneration(command="random", args={"length": "{{ LENGTH }}", "encoding": "hex"})
        result = generate_value(rule, existing={"LENGTH": "16"})
        assert len(result) == 32  # 16 bytes → 32 hex chars


class TestJinjaDeps:
    def test_jinja_deps_simple(self) -> None:
        deps = _jinja_deps("{{ A }} and {{ B }}", {"A", "B", "C"})
        assert deps == {"A", "B"}

    def test_jinja_deps_unknown_filtered(self) -> None:
        deps = _jinja_deps("{{ A }} {{ UNKNOWN }}", {"A", "B"})
        assert deps == {"A"}

    def test_jinja_deps_no_vars(self) -> None:
        assert _jinja_deps("static", {"A", "B"}) == set()

    def test_rule_jinja_deps_default(self) -> None:
        rule = DefaultGeneration(value="{{ X }}-{{ Y }}")
        assert _rule_jinja_deps(rule, {"X", "Y", "Z"}) == {"X", "Y"}

    def test_rule_jinja_deps_command(self) -> None:
        rule = CommandGeneration(command="echo {{ HOST }}")
        assert _rule_jinja_deps(rule, {"HOST", "PORT"}) == {"HOST"}

    def test_rule_jinja_deps_openssl_args(self) -> None:
        rule = OpenSSLGeneration(command="random", args={"length": "{{ LEN }}"})
        assert _rule_jinja_deps(rule, {"LEN"}) == {"LEN"}
