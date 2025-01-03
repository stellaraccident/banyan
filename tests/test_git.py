from pathlib import Path


from banyan.support.git import GitRepo


def test_init(tmp_path: Path):
    g = GitRepo(tmp_path)
    g.init()
    assert (tmp_path / ".git").exists()

