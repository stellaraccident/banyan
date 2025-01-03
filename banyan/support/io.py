from typing import TypeVar
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomlkit as tomllib


from .errors import ConfigError

_T = TypeVar("_T")


class File:
    """Encapsulates a file accessible at some path.

    We use a custom class for this so that we can manage uptodate checks and
    have subclasses that are more sophisticated (i.e. git backed, etc).
    """

    def __init__(self, path: Path):
        self.path = path

    def exists(self) -> bool:
        return self.path.exists()

    def require_exists(self: _T) -> _T:
        if not self.exists():
            raise ConfigError(f"The config file {self.path} does not exist")
        return self

