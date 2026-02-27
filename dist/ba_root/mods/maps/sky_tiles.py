# ba_meta require api 9
from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


class MGdefs:
    points = {}
    boxes = {}
    boxes['area_of_interest_bounds'] = (
        (0.3544110667, 4.493562578, -2.518391331)
        + (0.0, 0.0, 0.0)
        + (16.64754831, 8.06138989, 18.5029888)
    )
    boxes['map_bounds'] = (
        (0.2608783669, 4.899663734, -3.543675157)
        + (0.0, 0.0, 0.0)
        + (29.23565494, 14.19991443, 29.92689344)
    )


class SkyTiles(bs.Map):
    defs = MGdefs()
    name = 'Sky Tiles'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'achievementOffYouGo'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'bgtex': bs.gettexture('menuBG'),
            'bgmesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.0, 1.0, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5


bs._map.register_map(SkyTiles)
