"""Encapsulates a banyan repository."""

from typing import Optional
from pathlib import Path

from banyan.support.errors import ConfigError
from banyan.support.git import GitRepo
from banyan.support.io import File, tomllib

DEPOT_FILENAME = "BANYAN_DEPOT.toml"
WORKSPACE_FILENAME = "BANYAN_WORKSPACE.toml"


class BanyanDepot:
    """Encapsulates a Banyan repository backed by a local git repository."""

    def __init__(self, git_repo: GitRepo):
        self.git_repo = git_repo
        depot_file = git_repo.file(DEPOT_FILENAME)
        self.config = DepotConfig(depot_file)

    @property
    def canonical_path(self) -> Path:
        return self.git_repo.root_dir.resolve()

    def workspace(self, local_path: str | Path) -> "BanyanWorkspace":
        return BanyanWorkspace(self, Path(local_path))


class DepotConfig:
    def __init__(self, depot_file: File):
        depot_file.require_exists()
        with open(depot_file.path, "rb") as f:
            try:
                self.entries = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise ConfigError(f"Cannot parse config file `{depot_file.path}`: {e}")


class WorkspaceConfig:
    def __init__(self, workspace_file: File):
        workspace_file.require_exists()
        self.workspace_file = workspace_file
        with open(self.workspace_file.path, "rb") as f:
            try:
                self.entries = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise ConfigError(
                    f"Cannot parse workspace config file `{workspace_file}`: {e}"
                )

        self.mounts = WorkspaceMountConfig.from_config(self.entries.get("mount"))


class WorkspaceMountConfig:
    """Represents a `[mount . "foo/bar"]` in a workspace config."""

    def __init__(self, local_path: Path, table):
        if not isinstance(table, dict):
            raise ConfigError(f"Expected table for mount: {local_path}")
        self.local_path = local_path
        self.table = table

    @staticmethod
    def from_config(config: dict | None) -> dict[str, "WorkspaceMountConfig"]:
        if not config:
            return {}
        return {
            local_path: WorkspaceMountConfig(Path(local_path), table)
            for local_path, table in config.items()
        }


class BanyanWorkspace:
    """Encapsulates a Banyan workspace within a depot."""

    def __init__(self, depot: BanyanDepot, local_path: Path):
        self.depot = depot
        self.local_path = local_path
        workspace_file = depot.git_repo.file(local_path / WORKSPACE_FILENAME)
        self.config = WorkspaceConfig(workspace_file)
        self.mounts = {
            mount_config.local_path: WorkspaceMount(self, mount_config)
            for mount_config in self.config.mounts.values()
        }

    @property
    def canonical_path(self) -> Path:
        abs_path = self.depot.canonical_path / self.local_path
        return abs_path.resolve()

    @property
    def mount_local_path_names(self) -> list[str]:
        return [str(p) for p in self.mounts.keys()]

    def checkout(self, *local_paths: Path | str):
        import banyan.commands.workspace_checkout as cmd

        cmd.checkout(self, *local_paths)


class WorkspaceMount:
    """Represents a mount of a component into the workspace."""

    def __init__(self, ws: BanyanWorkspace, config: WorkspaceMountConfig):
        self.ws = ws
        self.config = config
        self.canonical_path = ws.canonical_path / config.local_path

    @property
    def local_path(self) -> Path:
        return self.config.local_path

    @property
    def branch_name(self) -> str:
        """Name of the branch that backs this mount in this workspace."""
        full_local_path = self.ws.local_path / self.local_path
        return f"mount/default{{{full_local_path}}}"

    def is_populated(
        self, worktree_list: Optional[dict[Path, dict[str, str | None]]] = None
    ) -> bool:
        """Returns whether the mount is populated."""
        if worktree_list is None:
            worktree_list = self.ws.depot.git_repo.worktree_list()
        return self.canonical_path in worktree_list

    def __repr__(self):
        return str(self.local_path)
