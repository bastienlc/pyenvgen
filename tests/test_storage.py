"""Tests for the storage module."""

from pyenvgen.schema import EnvSchema
from pyenvgen.storage import StdoutStorage, get_storage


class TestStdoutStorage:
    def test_prints_non_internal_vars(self, capsys) -> None:  # type: ignore[no-untyped-def]
        schema = EnvSchema.model_validate(
            {
                "variables": {
                    "PUBLIC": {
                        "generation": {"rule": "default", "value": "x"},
                    },
                    "SECRET": {
                        "generation": {"rule": "default", "value": "y"},
                        "internal": True,
                    },
                }
            }
        )
        storage = StdoutStorage()
        storage.store({"PUBLIC": "hello", "SECRET": "hidden"}, schema)

        captured = capsys.readouterr()
        assert "PUBLIC=hello" in captured.out
        assert "SECRET" not in captured.out


class TestGetStorage:
    def test_stdout_backend(self) -> None:
        backend = get_storage("stdout")
        assert isinstance(backend, StdoutStorage)

    def test_unknown_backend_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="Unknown storage"):
            get_storage("nonexistent")
