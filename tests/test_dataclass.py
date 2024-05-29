import logging
import os

from kloch_kiche._dataclass import KicheLauncher


def test__KicheLauncher__execute(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    launcher = KicheLauncher(
        requirements=["click==7.1.2"],
        python_version="3.10",
        environ=os.environ.copy(),
        cwd=tmp_path,
        command=[
            "-c",
            "import sys\nprint(sys.version_info)\nimport click\nprint(click.__path__)",
        ],
    )
    returncode = launcher.execute(tmpdir=tmp_path)
    assert not returncode
