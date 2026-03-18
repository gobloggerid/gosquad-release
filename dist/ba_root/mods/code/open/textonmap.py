# Released under the MIT License. See LICENSE for details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs

if TYPE_CHECKING:
    pass


class TextOnMap:
    def __init__(self):
        print(
            'enable me in dist/ba_root/mods/data/live/configs/setting.json '
            'and edit me in dist/ba_root/mods/code/open/textonmap.py '
            'to have additional Text on Map in your game activity'
        )

    @property
    def activity(self) -> bs.Activity:
        return bs.getactivity()
