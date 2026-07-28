# Released under the MIT License. See LICENSE for details.
#
"""Music related bits."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import _bascenev1

if TYPE_CHECKING:
    pass


class MusicType(Enum):
    """Types of music available to play in-game.

    These do not correspond to specific pieces of music, but rather to
    'situations'. The actual music played for each type can be overridden
    by the game or by the user.
    """

    MENU = 'Menu'
    LMS1 = 'A grave soul (now run)'
    LMS2 = 'Plead'
    LMS3 = 'Creation of Hatred'
    LMS4 = 'You and I, Forever.'
    LMS5 = 'Blood Stained Ears'
    LOBBY = 'lobby'
    

def setmusic(musictype: MusicType | None, continuous: bool = False) -> None:
    """Set the app to play (or stop playing) a certain type of music.

    This function will handle loading and playing sound assets as
    necessary, and also supports custom user soundtracks on specific
    platforms so the user can override particular game music with their
    own.

    Pass ``None`` to stop music.

    if ``continuous`` is True and musictype is the same as what is
    already playing, the playing track will not be restarted.
    """

    # All we do here now is set a few music attrs on the current globals
    # node. The foreground globals' current playing music then gets fed to
    # the do_play_music call in our music controller. This way we can
    # seamlessly support custom soundtracks in replays/etc since we're being
    # driven purely by node data.
    gnode = _bascenev1.getactivity().globalsnode
    gnode.music_continuous = continuous
    gnode.music = '' if musictype is None else musictype.value
    gnode.music_count += 1
