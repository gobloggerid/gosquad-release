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
            'edit me on dist/ba_root/mods/code/open/textonmap.py '
            'to have additional text/message in your game activity'
        )

    @property
    def activity(self) -> bs.Activity:
        return bs.getactivity()
