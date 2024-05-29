import dataclasses
import logging
import os
import subprocess
from pathlib import Path
from typing import List
from typing import Optional

import uv
from kloch.launchers import BaseLauncher

from ._download import download_python
from ._download import timeit


LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class KicheLauncher(BaseLauncher):
    """
    A launcher that install python and download depencies at a temporary location.
    """

    requirements: List[str] = dataclasses.field(default_factory=list)
    """
    A list of package requirement as supported by uv, which itself supports pip conventions.
    """

    python_version: str = ""
    """
    Full or partial version of the python interpreter to download and use.
    
    Example: "3.9" or "3.9.12"
    """

    name = "kiche"

    required_fields = ["python", "requirements"]

    def execute(self, tmpdir: Path, command: Optional[List[str]] = None):
        """
        Execute a python command while ensuring the installation of its dependencies and a python interpreter.

        Python and the dependencies are installed at a temporary location discarded on exit.
        """
        python_download_dir = tmpdir
        with timeit("downloaded python in ", LOGGER.info):
            # TODO see to add a cache option
            python_bin_path = download_python(
                python_version=self.python_version,
                target_dir=python_download_dir,
            )

        requirements_in_path = tmpdir / "requirements.in"
        LOGGER.debug(f"writing requirements to '{requirements_in_path}'")
        requirements_in_path.write_text("\n".join(self.requirements), encoding="utf-8")

        uv_path = uv.find_uv_bin()
        requirements_out_path = tmpdir / "requirements.txt"

        LOGGER.debug(f"using uv to compile requirements to '{requirements_out_path}'")
        subprocess.run(
            [
                uv_path,
                "pip",
                "compile",
                str(requirements_in_path),
                "-o",
                str(requirements_out_path),
                "--python",
                python_bin_path,
                "--verbose",
            ],
            env=None,
            cwd=tmpdir,
            check=True,
        )

        venv_path = tmpdir / ".venv"

        LOGGER.debug(f"using uv to create virtual environment at '{venv_path}'")
        subprocess.run(
            [
                uv_path,
                "venv",
                "--verbose",
                "--python",
                str(python_bin_path),
                str(venv_path),
            ],
            env=None,
            cwd=tmpdir,
            check=True,
        )

        environ = os.environ.copy()
        environ["VIRTUAL_ENV"] = str(venv_path)

        LOGGER.debug(f"using uv to install requirements to venv")
        subprocess.run(
            [
                uv_path,
                "pip",
                "install",
                "-r",
                str(requirements_out_path),
                "--python",
                str(python_bin_path),
                "--verbose",
            ],
            env=environ,
            cwd=tmpdir,
            check=True,
        )

        _command = self.command + (command or [])
        _command = [str(python_bin_path)] + _command

        environ = self.environ.copy()
        # manually activate the venv
        environ["VIRTUAL_ENV"] = str(venv_path)
        environ["PATH"] = str(venv_path / "Scripts") + os.pathsep + environ["PATH"]

        LOGGER.debug(f"executing command={_command}; environ={environ}; cwd={self.cwd}")
        result = subprocess.run(_command, env=environ, cwd=self.cwd)
        return result.returncode
