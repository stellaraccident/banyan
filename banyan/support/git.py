from typing import Optional, Union
from pathlib import Path

from .commands import CommandExecutor
from .io import File


class GitRepo:
    """Accesses a git repo (which may be a worktree)."""

    def __init__(
        self,
        root_dir: Path,
        *,
        parent: Optional["GitRepo"] = None,
        executor: Optional[CommandExecutor] = None
    ):
        self.parent = parent
        if executor is None:
            executor = CommandExecutor()
        self.executor = executor.for_dir(root_dir)

    @property
    def root_dir(self) -> Path:
        return self.executor.cwd

    def init(self, bare: bool = False):
        """Runs `git init`."""
        args = ["git", "init", "--quiet"]
        if bare:
            args.append("--bare")
        self.executor.call(args)

    def file(self, local_path: Path | str) -> "GitFile":
        return GitFile(Path(local_path), self)

    def add(self, *file: Union[str, "GitFile"], quiet: bool = True):
        local_paths = [f.local_path if isinstance(f, GitFile) else f for f in file]
        args = ["git", "add", "--"] + local_paths
        self.executor.call(args, quiet=quiet)

    def commit(
        self,
        *,
        message: str = "",
        allow_empty_message: bool = False,
        allow_empty: bool = False,
        quiet: bool = False
    ):
        args = ["git", "commit", "-m", message]
        if allow_empty_message:
            args.append("--allow-empty-message")
        if allow_empty:
            args.append("--allow-empty")
        if quiet:
            args.append("--quiet")
        self.executor.call(args, quiet=quiet)


class GitFile(File):
    """File that exists as part of a git repository."""

    def __init__(self, local_path: Path, git_repo: GitRepo):
        super().__init__(git_repo.root_dir / local_path)
        self.local_path = local_path.as_posix()
        self.git_repo = git_repo
