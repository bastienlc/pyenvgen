"""Tests for topological ordering and full environment generation."""

from __future__ import annotations

import pytest

from pyenvgen.generation import (
    CircularDependencyError,
    generate_env,
    generate_value,
    _topological_order,
)
from pyenvgen.schema import EnvSchema


class TestTopologicalOrder:
    def _schema(self, variables: dict) -> EnvSchema:
        return EnvSchema.model_validate({"variables": variables})

    def test_all_defaults_contains_all_names(self) -> None:
        schema = self._schema({
            "A": {"generation": {"rule": "default", "value": "1"}},
            "B": {"generation": {"rule": "default", "value": "2"}},
            "C": {"generation": {"rule": "default", "value": "3"}},
        })
        order = _topological_order(schema)
        assert set(order) == {"A", "B", "C"}

    def test_template_after_dependency(self) -> None:
        schema = self._schema({
            "URL": {"generation": {"rule": "template", "template": "http://{{ HOST }}:{{ PORT }}"}},
            "HOST": {"generation": {"rule": "default", "value": "localhost"}},
            "PORT": {"generation": {"rule": "default", "value": "8080"}},
        })
        order = _topological_order(schema)
        assert order.index("HOST") < order.index("URL")
        assert order.index("PORT") < order.index("URL")

    def test_chained_templates(self) -> None:
        schema = self._schema({
            "C": {"generation": {"rule": "template", "template": "{{ B }}-c"}},
            "B": {"generation": {"rule": "template", "template": "{{ A }}-b"}},
            "A": {"generation": {"rule": "default", "value": "a"}},
        })
        order = _topological_order(schema)
        assert order.index("A") < order.index("B") < order.index("C")

    def test_circular_dependency_raises(self) -> None:
        schema = self._schema({
            "A": {"generation": {"rule": "template", "template": "{{ B }}"}},
            "B": {"generation": {"rule": "template", "template": "{{ A }}"}},
        })
        with pytest.raises(CircularDependencyError):
            _topological_order(schema)

    def test_self_reference_raises(self) -> None:
        schema = self._schema({
            "A": {"generation": {"rule": "template", "template": "{{ A }}"}},
        })
        with pytest.raises(CircularDependencyError):
            _topological_order(schema)


class TestGenerateEnv:
    def _schema(self, variables: dict) -> EnvSchema:
        return EnvSchema.model_validate({"variables": variables})

    def test_generates_all_defaults(self) -> None:
        schema = self._schema({
            "A": {"generation": {"rule": "default", "value": "1"}},
            "B": {"generation": {"rule": "default", "value": "2"}},
        })
        assert generate_env(schema) == {"A": "1", "B": "2"}

    def test_overrides_take_precedence(self) -> None:
        schema = self._schema({
            "A": {"generation": {"rule": "default", "value": "1"}},
        })
        assert generate_env(schema, overrides={"A": "override"}) == {"A": "override"}

    def test_template_resolves_with_generated_values(self) -> None:
        schema = self._schema({
            "HOST": {"generation": {"rule": "default", "value": "db"}},
            "PORT": {"generation": {"rule": "default", "value": "5432"}},
            "DSN": {"generation": {"rule": "template", "template": "postgres://{{ HOST }}:{{ PORT }}/app"}},
        })
        result = generate_env(schema)
        assert result["DSN"] == "postgres://db:5432/app"

    def test_template_uses_override(self) -> None:
        schema = self._schema({
            "HOST": {"generation": {"rule": "default", "value": "localhost"}},
            "DSN": {"generation": {"rule": "template", "template": "postgres://{{ HOST }}/app"}},
        })
        result = generate_env(schema, overrides={"HOST": "prod-db"})
        assert result["DSN"] == "postgres://prod-db/app"

    def test_command_rule(self) -> None:
        schema = self._schema({
            "GREETING": {"generation": {"rule": "command", "command": "echo hello"}},
        })
        result = generate_env(schema)
        assert result["GREETING"] == "hello"

    def test_openssl_random_generates_value(self) -> None:
        schema = self._schema({
            "SECRET": {"generation": {"rule": "openssl", "command": "random", "args": {"length": 16}}},
        })
        result = generate_env(schema)
        assert len(result["SECRET"]) == 32  # hex encoding, 16 bytes = 32 chars

    def test_circular_dep_raises_in_generate_env(self) -> None:
        schema = self._schema({
            "A": {"generation": {"rule": "template", "template": "{{ B }}"}},
            "B": {"generation": {"rule": "template", "template": "{{ A }}"}},
        })
        with pytest.raises(CircularDependencyError):
            generate_env(schema)
