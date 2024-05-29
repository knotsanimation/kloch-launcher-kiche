# MIT License
#
# Copyright (c) 2023 Tushar Sadhwani
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
This is a modified copy of https://github.com/tusharsadhwani/yen/blob/main/src/yen/github.py
"""

from __future__ import annotations

import json
import logging
import platform
import urllib.error
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from urllib.request import urlopen

LOGGER = logging.getLogger(__name__)

THISDIR = Path(__file__).parent

MACHINE_RELEASE_SUFFIX = {
    "Darwin": {
        "arm64": "aarch64-apple-darwin-install_only.tar.gz",
        "x86_64": "x86_64-apple-darwin-install_only.tar.gz",
    },
    "Linux": {
        "aarch64": {
            "glibc": "aarch64-unknown-linux-gnu-install_only.tar.gz",
            # musl doesn't exist
        },
        "x86_64": {
            "glibc": "x86_64_v3-unknown-linux-gnu-install_only.tar.gz",
            "musl": "x86_64_v3-unknown-linux-musl-install_only.tar.gz",
        },
    },
    "Windows": {
        "AMD64": "x86_64-pc-windows-msvc-shared-install_only.tar.gz",
    },
}


class PythonReleaseUrl:
    """
    Parse a github release url retrieved from the indygreg/python-build-standalone repo.

    Examples:
    - https://github.com/indygreg/python-build-standalone/releases/download/20240107/cpython-3.10.13%2B20240107-aarch64-apple-darwin-debug-full.tar.zst
    - https://github.com/indygreg/python-build-standalone/releases/download/20240107/cpython-3.10.13%2B20240107-x86_64-unknown-linux-musl-install_only.tar.gz.sha256
    - https://github.com/indygreg/python-build-standalone/releases/download/20240107/cpython-3.10.13%2B20240107-x86_64-pc-windows-msvc-static-noopt-full.tar.zst
    """

    GITHUB_API_URL = (
        "https://api.github.com/repos/indygreg/python-build-standalone/releases/latest"
    )

    def __init__(self, url: str):
        self.url: str = url
        """
        github download url to a file
        """

        self.url_sha256: str = url + ".sha256"
        """
        url providing a sha256 cheksum hash for the base url
        """

        self.basename: str = url.split("/")[-1]

        _, python, context = self.basename.split("-", 2)

        self.python_version: str = python.split("%")[0]  # ex: 3.10.13

        arch, distrib, platform_, variant = context.split("-", 3)
        variant, extension = variant.split(".", 1)

        self.extension: str = "." + extension  # ex: .tar.gz.sha256
        self.arch: str = arch  # ex: x86_64
        self.distrib: str = distrib  # ex: unknown
        self.platform: str = platform_  # ex: linux
        self.variant: str = variant  # ex: musl-install_only

    def __repr__(self):
        return f"{self.__class__.__name__}({self.url})"

    def __lt__(self, other: "PythonReleaseUrl") -> bool:
        # sort by instance by python version
        def _comparable(_instance):
            # we need to convert to int because else "3.13" < "3.9" in str comparison
            return [int(k) for k in _instance.python_version.split(".")]

        return _comparable(self) < _comparable(other)


def read_fallback_release_data() -> Dict[str, Any]:
    """
    Returns the fallback release data, for when GitHub API gives an error.
    """
    data_file = THISDIR / "_github_dl.fallback.json"
    LOGGER.debug(f"reading '{data_file}'")
    with open(data_file) as data:
        return json.load(data)


def query_release_urls() -> List[PythonReleaseUrl]:
    """
    Query the GitHub API to find the latest Python releases download links.
    """
    try:
        with urlopen(PythonReleaseUrl.GITHUB_API_URL) as response:
            release_data = json.load(response)
    except urllib.error.URLError as error:
        LOGGER.warning(
            f"cannot connect to GitHub API; using fallback json data: {error}"
        )
        release_data = read_fallback_release_data()

    return [
        PythonReleaseUrl(url=asset["browser_download_url"])
        for asset in release_data["assets"]
        if not asset["browser_download_url"].endswith("SHA256SUMS")
    ]


def get_system_release_urls(system, machine) -> List[PythonReleaseUrl]:
    """
    Returns available python release urls for the given system.
    """
    release_suffix = MACHINE_RELEASE_SUFFIX[system][machine]
    # linux suffixes are nested under glibc or musl builds
    if system == "Linux":
        # fallback to musl if libc version is not found
        libc_version = platform.libc_ver()[0] or "musl"
        release_suffix = release_suffix[libc_version]

    python_releases = query_release_urls()
    python_releases = [
        release for release in python_releases if release.url.endswith(release_suffix)
    ]
    python_releases.sort()
    return python_releases


def get_system_python_release_url(python_version: Optional[str]) -> PythonReleaseUrl:
    """
    Args:
        python_version:
            a full or partial python version.
            Example "3.9" or "3.9.19"

    Returns:
        GitHub release URL for the corresponding python version.
    """

    system, machine = platform.system(), platform.machine()
    releases = get_system_release_urls(system, machine)

    if python_version is None:
        release = releases[-1]
        return release

    matching_releases = [
        release
        for release in releases
        if release.python_version.startswith(python_version)
    ]
    if not matching_releases:
        raise ValueError(
            f"No python release found for version '{python_version}' "
            f"among '{len(releases)}' releases: {[r.basename for r in releases]}"
        )

    release = matching_releases[-1]
    return release
