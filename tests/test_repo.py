from pathlib import Path

import pytest


from banyan.support.errors import ConfigError
from banyan.support.git import GitRepo
from banyan.repo import BanyanDepot


@pytest.fixture
def empty_git_repo(tmp_path: Path) -> GitRepo:
    gr = GitRepo(tmp_path)
    gr.init(quiet=True)
    return gr


def test_missing_depot_config(empty_git_repo: GitRepo):
    gr = empty_git_repo
    with pytest.raises(ConfigError):
        br = BanyanDepot(gr)


def test_depot_config_error(empty_git_repo: GitRepo):
    gr = empty_git_repo
    gr.file("BANYAN_DEPOT.toml").path.write_text("asdsa")
    with pytest.raises(ConfigError, match="Cannot parse config file"):
        br = BanyanDepot(gr)


def test_trivial_config(empty_git_repo: GitRepo):
    gr = empty_git_repo
    gr.add_text_file("BANYAN_DEPOT.toml", "")
    gr.add_text_file("BANYAN_WORKSPACE.toml", "")
    gr.commit(allow_empty_message=True, quiet=True)
    depot = BanyanDepot(gr)
    ws = depot.workspace(".")
    with pytest.raises(ConfigError, match="does not exist"):
        depot.workspace("not-exists")


def test_scratch_checkout(empty_git_repo: GitRepo):
    gr = empty_git_repo
    gr.add_text_file("BANYAN_DEPOT.toml", "")
    gr.add_text_file(
        "BANYAN_WORKSPACE.toml",
        """\
        [mount . "scratch/pad1"]
        """,
        dedent=True,
    )
    gr.commit(allow_empty_message=True, quiet=True)
    depot = BanyanDepot(gr)
    ws = depot.workspace(".")
    ws.checkout()
