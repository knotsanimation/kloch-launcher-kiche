import dataclasses
import logging
from typing import List

from kloch.launchers import BaseLauncherSerialized
from kloch.launchers import BaseLauncherFields
from ._dataclass import KicheLauncher

LOGGER = logging.getLogger(__name__)


# noinspection PyTypeChecker
@dataclasses.dataclass(frozen=True)
class KicheLauncherFields(BaseLauncherFields):
    requirements: List[str] = dataclasses.field(
        default="requirements",
        metadata={
            "description": "A list of python package requirements as supported by uv, which itself supports pip conventions.",
            "required": True,
        },
    )
    python_version: str = dataclasses.field(
        default="python_version",
        metadata={
            "description": 'Full or partial version of the python interpreter to download and use.\n\nExample: "3.9" or "3.9.12"',
            "required": True,
        },
    )


class KicheLauncherSerialized(BaseLauncherSerialized):
    source = KicheLauncher

    identifier = KicheLauncher.name

    fields = KicheLauncherFields

    summary = "Install python and packages dependencies at a temporary location."
    description = (
        "kiche create a full python environment from scratch that is discarded on exit."
        "it implies:\n"
        "- download a standalone python interpreter\n"
        "- create a temporary virtual environement\n"
        "- install the specified dependencies in the venv\n"
    )

    def validate(self):
        super().validate()

        requirements = self.fields.requirements

        assert requirements in self, f"'{requirements}': missing key"
        assert isinstance(
            self[requirements], list
        ), f"'{requirements}': must be a list."
        for value in self[requirements]:
            assert isinstance(
                value, str
            ), f"'{requirements}': item '{value}' must be a str."

        python_version = self.fields.python_version
        assert python_version in self, f"'{python_version}': missing key"
        assert isinstance(
            self[python_version], str
        ), f"'{python_version}': must be a str."

    # we override for type-hint
    def unserialize(self) -> KicheLauncher:
        # noinspection PyTypeChecker
        return super().unserialize()
