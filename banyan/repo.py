"""Encapsulates a banyan repository."""

from pathlib import Path

from banyan.support.errors import ConfigError
from banyan.support.git import GitRepo
from banyan.support.io import File, tomllib

DEPOT_FILENAME = "BANYAN_DEPOT.toml"


class BanyanRepo:
    """Encapsulates a Banyan repository backed by a local git repository."""

    def __init__(self, git_repo: GitRepo):
        self.git_repo = git_repo
        depot_file = git_repo.file(DEPOT_FILENAME)
        self.depot_config = DepotConfig(depot_file)


class DepotConfig:
    def __init__(self, depot_file: File):
        depot_file.require_exists()
        with open(depot_file.path, "rb") as f:
            try:
                self.entries = tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                raise ConfigError(f"Cannot parse config file `{depot_file.path}`: {e}")
