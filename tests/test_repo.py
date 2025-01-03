from pathlib import Path

import pytest

from banyan.support.errors import ConfigError
from banyan.support.git import GitRepo
from banyan.repo import BanyanRepo


@pytest.fixture
def empty_git_repo(tmp_path: Path) -> GitRepo:
    gr = GitRepo(tmp_path)
    gr.init()
    return gr


def test_missing_depot_config(empty_git_repo: GitRepo):
    gr = empty_git_repo
    with pytest.raises(ConfigError):
        br = BanyanRepo(gr)


def test_depot_config_error(empty_git_repo: GitRepo):
    gr = empty_git_repo
    gr.file("BANYAN_DEPOT.toml").path.write_text("asdsa")
    with pytest.raises(ConfigError, match="Cannot parse config file"):
        br = BanyanRepo(gr)

def test_depot_config(empty_git_repo: GitRepo):
    gr = empty_git_repo
    f = gr.file("BANYAN_DEPOT.toml")
    f.path.write_text("")
    gr.add(f)
    gr.commit(allow_empty_message=True, quiet=True)
    br = BanyanRepo(gr)
