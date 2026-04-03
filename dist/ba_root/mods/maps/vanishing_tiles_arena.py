# ba_meta require api 9
from __future__ import annotations

from typing import TYPE_CHECKING
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


class VanishingTilesMapDefs:
    points = {'spawn1': (0, 3, -5)}
    boxes  = {
        'area_of_interest_bounds': (0, 4, -5, 0, 0, 0, 16, 8, 16),
        'map_bounds':              (0, 4, -5, 0, 0, 0, 30, 14, 30),
    }


class VanishingTilesMap(bs.Map):
    defs = VanishingTilesMapDefs()
    name = 'Vanishing Tiles Arena'

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'powerupHealth'

    @classmethod
    def on_preload(cls) -> Any:
        return {
            'bgtex':  bs.gettexture('menuBG'),
            'bgmesh': bs.getmesh('thePadBG'),
        }

    def __init__(self) -> None:
        super().__init__()
        self.node = bs.newnode('terrain', attrs={
            'mesh':          self.preloaddata['bgmesh'],
            'lighting':      False,
            'background':    True,
            'color_texture': self.preloaddata['bgtex'],
        })


bs._map.register_map(VanishingTilesMap)

