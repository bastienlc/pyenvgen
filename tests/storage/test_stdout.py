"""Tests for the stdout storage backend."""

from pyenvgen.storage import StdoutStorage
from . import schema


class TestStdoutStorage:
    def test_prints_non_internal_vars(self, capsys) -> None:  # type: ignore[no-untyped-def]
        s = schema("PUBLIC", "SECRET", internal={"SECRET"})
        storage = StdoutStorage()
        storage.store({"PUBLIC": "hello", "SECRET": "hidden"}, s)

        captured = capsys.readouterr()
        assert "PUBLIC=hello" in captured.out
        assert "SECRET" not in captured.out

    def test_empty_values(self, capsys) -> None:  # type: ignore[no-untyped-def]
        s = schema("A")
        StdoutStorage().store({}, s)
        assert capsys.readouterr().out == ""
