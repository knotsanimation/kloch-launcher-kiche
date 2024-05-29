import logging
import subprocess

from kloch_kiche._download import download_python


def test__download_python(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    python_path = download_python(python_version="3.10", target_dir=tmp_path)
    assert str(tmp_path) in str(python_path)
    assert python_path.exists()

    test_version = subprocess.check_output([str(python_path), "-V"], text=True)
    assert test_version.strip("Python ").startswith("3.10")
