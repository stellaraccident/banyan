from typing import Optional

from pathlib import Path

import os
import shlex
import subprocess
import sys


class CommandExecutor:
    """Executes commands as subprocesses, providing logging and exception handling
    controls."""

    def __init__(
        self, *, cwd: Optional[Path] = None, env: Optional[dict[str, str]] = None
    ):
        if cwd is None:
            cwd = Path.cwd()
        self.cwd = cwd
        if env is None:
            env = os.environ
        self.env = dict(env)
        if "GIT_DIR" in self.env:
            del self.env["GIT_DIR"]

    def for_dir(self, cwd: Path) -> "CommandExecutor":
        """Creates a new CommandExecutor for the given directory.

        This should be used in preference to creating a new instance as it preseves
        logging and management hooks.
        """
        return CommandExecutor(cwd=cwd, env=self.env)

    def call(self, args: list[Path | str], *, quiet: bool = False):
        """Calls a command with no stderr/stdout redirection (unless if configured
        by arguments).

        Raises an exception on failure.
        """
        args = _normalize_args(args)
        self._log_command(args, quiet=quiet)
        subprocess.check_call(args, cwd=self.cwd, env=self.env)

    def _log_command(self, args: list[str], *, quiet: bool = False):
        if quiet:
            return
        formatted = shlex.join(args)
        print(f"EXEC: [{self.cwd}]$ {formatted}", file=sys.stderr)


def _normalize_args(args: list[Path | str]) -> list[str]:
    return [str(arg) for arg in args]
