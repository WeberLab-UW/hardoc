import pytest
from hardoc.utils.github_utils import clone_repository, fetch_repo_info

def test_fetch_repo_info():
    repo_info = fetch_repo_info("owner/repo")
    assert isinstance(repo_info, dict)
    assert 'name' in repo_info

@pytest.mark.integration
def test_clone_repository(tmp_path):
    repo_path = clone_repository(
        "https://github.com/owner/repo",
        str(tmp_path)
    )
    assert repo_path.exists()
