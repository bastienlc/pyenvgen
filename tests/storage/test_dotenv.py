"""Tests for the .env storage backend."""

from pathlib import Path

from pyenvgen.storage import DotEnvStorage
from . import schema


class TestDotEnvStorage:
    def test_creates_new_file(self, tmp_path: Path) -> None:
        p = tmp_path / ".env"
        s = schema("FOO", "BAR")
        DotEnvStorage(p).store({"FOO": "1", "BAR": "2"}, s)
        content = p.read_text()
        assert "FOO=1" in content
        assert "BAR=2" in content

    def test_updates_existing_value_in_place(self, tmp_path: Path) -> None:
        p = tmp_path / ".env"
        p.write_text("# My config\nFOO=old\nBAR=keep\n")
        s = schema("FOO")
        DotEnvStorage(p).store({"FOO": "new"}, s)
        content = p.read_text()
        assert "FOO=new" in content
        assert "FOO=old" not in content

    def test_preserves_comments_and_blanks(self, tmp_path: Path) -> None:
        p = tmp_path / ".env"
        original = "# top comment\n\nFOO=old\n# another comment\nBAR=untouched\n"
        p.write_text(original)
        s = schema("FOO")
        DotEnvStorage(p).store({"FOO": "new"}, s)
        content = p.read_text()
        assert "# top comment" in content
        assert "# another comment" in content
        assert "BAR=untouched" in content
        assert "\n\n" in content  # blank line preserved

    def test_preserves_unrelated_vars(self, tmp_path: Path) -> None:
        p = tmp_path / ".env"
        p.write_text("UNRELATED=stays\nFOO=old\n")
        s = schema("FOO")
        DotEnvStorage(p).store({"FOO": "updated"}, s)
        assert "UNRELATED=stays" in p.read_text()

    def test_appends_new_key(self, tmp_path: Path) -> None:
        p = tmp_path / ".env"
        p.write_text("EXISTING=1\n")
        s = schema("NEW_KEY")
        DotEnvStorage(p).store({"NEW_KEY": "hello"}, s)
        content = p.read_text()
        assert "EXISTING=1" in content
        assert "NEW_KEY=hello" in content

    def test_export_prefix_preserved(self, tmp_path: Path) -> None:
        p = tmp_path / ".env"
        p.write_text("export FOO=old\n")
        s = schema("FOO")
        DotEnvStorage(p).store({"FOO": "new"}, s)
        assert "export FOO=new" in p.read_text()

    def test_internal_vars_excluded(self, tmp_path: Path) -> None:
        p = tmp_path / ".env"
        s = schema("PUBLIC", "SECRET", internal={"SECRET"})
        DotEnvStorage(p).store({"PUBLIC": "a", "SECRET": "b"}, s)
        content = p.read_text()
        assert "PUBLIC=a" in content
        assert "SECRET" not in content

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        p = tmp_path / "deep" / "dir" / ".env"
        s = schema("X")
        DotEnvStorage(p).store({"X": "1"}, s)
        assert p.exists()
