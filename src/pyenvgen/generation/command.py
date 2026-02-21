"""Command generation rule – executes a shell command and captures its stdout."""

from __future__ import annotations

import subprocess

from pyenvgen.schema import CommandGeneration


def generate_command(rule: CommandGeneration) -> str:
    """Execute *rule.command* in a shell and return its stripped stdout."""
    result = subprocess.run(
        rule.command,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
