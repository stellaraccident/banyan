from typing import Any, Optional, Union
from pathlib import Path
import textwrap

from .commands import CommandExecutor
from .io import File

# Can be either a GitFile or a local path.
GitFileLike = Union["GitFile", str, Path]


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

    def init(self, bare: bool = False, quiet: bool = False):
        """Runs `git init`."""
        args = ["git", "init", "--quiet"]
        if bare:
            args.append("--bare")
        self.executor.call(args, quiet=quiet)

    def file(self, local_path: Path | str) -> "GitFile":
        return GitFile(Path(local_path), self)

    def add(self, *file: GitFileLike, quiet: bool = True):
        files = self.from_file_like_list(*file)
        args = ["git", "add", "--"] + [f.path for f in files]
        self.executor.call(args, quiet=quiet)

    def add_text_file(
        self, file: GitFileLike, contents: str, *, dedent: bool = False
    ) -> "GitFile":
        """Helper to write a text file and `git add` it."""
        f = self.from_file_like(file)
        if dedent:
            contents = textwrap.dedent(contents)
        f.path.write_text(contents)
        self.add(f)
        return f

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

    def worktree_list(self) -> dict[Path, dict[str, str | None]]:
        """Lists all worktrees attached to the repository.

        Returns a dict keyed by worktree path. Values are the name/value pairs described
        in `git worktree list --porcelain`. For attributes without a value, the value
        will be None.

        The worktree path is always canonicalized via resolve().
        """
        raw = self.executor.capture_bytes(
            ["git", "worktree", "list", "--porcelain", "-z"], quiet=True
        )
        lines = raw.split(b"\x00")
        worktree_path: Path | None = None
        record: dict[str, str | None] | None = None
        results: dict[str, dict[str, str | None]] = {}

        def accum():
            nonlocal worktree_path
            nonlocal record
            if worktree_path and record:
                results[worktree_path] = record
            worktree_path = None
            record = None

        for line in lines:
            if not line:
                accum()
                continue
            kv = line.split(maxsplit=1)
            if not kv:
                continue
            key = kv[0].decode()
            value = None
            if len(kv) > 1:
                value = kv[1].decode()
            if record is None:
                record = {}
            record[key] = value
            if key == "worktree":
                worktree_path = Path(value).resolve()

        return results

    def from_file_like(self, file_or_local_path: GitFileLike) -> "GitFile":
        return (
            file_or_local_path
            if isinstance(file_or_local_path, GitFile)
            else GitFile(Path(file_or_local_path), self)
        )

    def from_file_like_list(self, *file_or_local_paths: GitFileLike) -> list["GitFile"]:
        return [self.from_file_like(f) for f in file_or_local_paths]


class GitFile(File):
    """File that exists as part of a git repository."""

    def __init__(self, local_path: Path, git_repo: GitRepo):
        super().__init__(git_repo.root_dir / local_path)
        self.local_path = local_path.as_posix()
        self.git_repo = git_repo
