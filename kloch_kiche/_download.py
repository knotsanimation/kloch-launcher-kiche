import contextlib
import hashlib
import logging
import tarfile
import time
import urllib.request
from pathlib import Path
from typing import Callable

from ._github_dl import get_system_python_release_url
from pythonning.web import download_file
from pythonning.progress import ProgressBar

LOGGER = logging.getLogger(__name__)


class DownloadProgressBar(ProgressBar):
    """
    A progress bar for download, expressed in MB units.
    """

    byte_to_MB = 9.5367e-7

    def __init__(self):
        super().__init__(
            prefix="downloading",
            suffix="[{bar_index:<2.1f}MB/{bar_max:.1f}MB] elapsed {elapsed_time:.2f}s",
        )

    def show_progress(self, block_number, block_size, total_size):
        """
        To be used as callback during a download operation.

        Args:
            block_number: current block being downloaded, variable over time.
            block_size: size of each download block, static over time.
            total_size:
                total size of all the block to download, static over time.
                might not be provided which correspond to a value < 1.
        """
        if total_size < 1:
            self.update()
        else:
            downloaded = block_number * block_size
            self.set_progress(
                total_progress=downloaded * self.byte_to_MB,
                new_maximum=total_size * self.byte_to_MB,
            )


@contextlib.contextmanager
def catch_progress():
    progress_bar = DownloadProgressBar()
    progress_bar.start()
    try:
        yield progress_bar
    finally:
        progress_bar.end()


@contextlib.contextmanager
def timeit(message: str, stream: Callable[[str], None]):
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        stream(f"{message}{end - start:.2f}s")


def _read_shad256(sha256_url: str) -> str:
    response = urllib.request.urlopen(sha256_url)
    return response.read().decode()


def _validate_checksum(sha256_url: str, downloaded_file: Path) -> bool:
    checksum = hashlib.sha256(downloaded_file.read_bytes()).hexdigest()
    expected_checksum = _read_shad256(sha256_url).rstrip("\n")
    return expected_checksum == checksum


def download_python(python_version: str, target_dir: Path) -> Path:
    """

    Args:
        python_version: a full or partial python version. Example "3.9" or "3.9.19"
        target_dir: filesystem path to an existing empty directory

    Returns:
        path to the python interpreter file located in the ``target_dir``
    """
    release_url = get_system_python_release_url(python_version=python_version)
    target_file = target_dir / release_url.basename
    LOGGER.info(f"downloading '{release_url.url}' to '{target_file}'")
    with timeit("download_file took ", LOGGER.debug):
        with catch_progress() as progress_bar:
            download_file(
                url=release_url.url,
                target_file=target_file,
                step_callback=progress_bar.show_progress,
            )

    with timeit("_validate_checksum took ", LOGGER.debug):
        successfull = _validate_checksum(release_url.url_sha256, target_file)

    if not successfull:
        target_file.unlink(missing_ok=True)
        raise RuntimeError(
            f"Failed to validate checksum for downloaded release '{release_url}'"
        )

    LOGGER.debug(f"extracting '{target_file}'")
    with timeit("tarfile.open took ", LOGGER.debug):
        with tarfile.open(target_file, mode="r:gz") as tar:
            tar.extractall(target_dir)

    target_file.unlink()

    # extracted archives have different structure depending on which system they were made for
    if release_url.platform == "windows":
        python_bin_path = target_dir / "python" / "python.exe"
    else:
        python_bin_path = target_dir / "python" / "bin" / "python3"

    assert python_bin_path.exists(), python_bin_path
    return python_bin_path
