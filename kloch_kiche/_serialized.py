import dataclasses
import logging
from typing import Dict
from typing import List

import yaml

from kloch.launchers import BaseLauncherSerialized
from kloch.launchers import BaseLauncherFields
from ._dataclass import PipxRunLauncher

LOGGER = logging.getLogger(__name__)


# noinspection PyTypeChecker
@dataclasses.dataclass(frozen=True)
class PipxRunLauncherFields(BaseLauncherFields):
    requires: Dict[str, str] = dataclasses.field(
        default="requires",
        metadata={
            "description": "mapping of rez `package name`: `package version`",
            "required": False,
        },
    )


class PipxRunLauncherSerialized(BaseLauncherSerialized):
    source = PipxRunLauncher

    identifier = PipxRunLauncher.name

    fields = PipxRunLauncherFields

    summary = (
        "Run an application in a temporary python virtual environment managed by pipx."
    )
    description = (
        "We generate a temporary virtual environment using pipx.\n"
        "pipx take care of resolving and installing the dependencies specified."
    )

    def validate(self):
        super().validate()

        requires = self.fields.requires
        if requires in self:
            assert isinstance(self[requires], dict), f"'{requires}': must be a dict."
            for key, value in self[requires].items():
                assert isinstance(key, str), f"'{requires}': key '{key}' must be a str."
                assert isinstance(
                    value, str
                ), f"'{requires}': value '{value}' must be a str."

    # we override for type-hint
    def unserialize(self) -> PipxRunLauncher:
        # noinspection PyTypeChecker
        return super().unserialize()
