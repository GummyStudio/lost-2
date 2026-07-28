# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to co-op campaigns."""
from __future__ import annotations

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from typing import Any
    import bascenev1


def register_campaign(campaign: bascenev1.Campaign) -> None:
    """Register a new campaign."""
    assert babase.app.classic is not None
    babase.app.classic.campaigns[campaign.name] = campaign


class Campaign:
    """Represents a unique set of :class:`~bascenev1.Level` instances."""

    def __init__(
        self,
        name: str,
        sequential: bool = True,
        levels: list[bascenev1.Level] | None = None,
    ):
        self._name = name
        self._sequential = sequential
        self._levels: list[bascenev1.Level] = []
        if levels is not None:
            for level in levels:
                self.addlevel(level)

    @property
    def name(self) -> str:
        """The name of the campaign."""
        return self._name

    @property
    def sequential(self) -> bool:
        """Whether this campaign's levels must be played in sequence."""
        return self._sequential

    def addlevel(
        self, level: bascenev1.Level, index: int | None = None
    ) -> None:
        """Add a level to the campaign."""
        if level.campaign is not None:
            raise RuntimeError('Level already belongs to a campaign.')
        level.set_campaign(self, len(self._levels))
        if index is None:
            self._levels.append(level)
        else:
            self._levels.insert(index, level)

    @property
    def levels(self) -> list[bascenev1.Level]:
        """The list of levels in the campaign."""
        return self._levels

    def getlevel(self, name: str) -> bascenev1.Level:
        """Return a contained level by name."""

        for level in self._levels:
            if level.name == name:
                return level
        raise babase.NotFoundError(
            "Level '" + name + "' not found in campaign '" + self.name + "'"
        )

    def reset(self) -> None:
        """Reset state for the campaign."""
        babase.app.config.setdefault('Campaigns', {})[self._name] = {}

    # FIXME: should these give/take baclassic.Level instances instead of
    #  level names?..
    def set_selected_level(self, levelname: str) -> None:
        """Set the Level currently selected in the UI (by name)."""
        self.configdict['Selection'] = levelname
        babase.app.config.commit()

    def get_selected_level(self) -> str:
        """Return the name of the Level currently selected in the UI."""
        val = self.configdict.get('Selection', self._levels[0].name)
        assert isinstance(val, str)
        return val

    @property
    def configdict(self) -> dict[str, Any]:
        """Return the live config dict for this campaign."""
        val: dict[str, Any] = babase.app.config.setdefault(
            'Campaigns', {}
        ).setdefault(self._name, {})
        assert isinstance(val, dict)
        return val


def init_campaigns() -> None:
    """Fill out initial default Campaigns."""
    # pylint: disable=cyclic-import
    