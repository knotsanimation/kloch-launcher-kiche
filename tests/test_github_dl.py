import pytest

from kloch_kiche._github_dl import get_system_python_release_url


def test__get_system_python_release_url():
    release_url = get_system_python_release_url(python_version="3.10")
    assert "cpython-3.10" in release_url.url

    with pytest.raises(ValueError):
        release_url = get_system_python_release_url(python_version="3.1256")
