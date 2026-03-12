# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import Any, override

import bascenev1 as bs


class _TileLandsDefs:
    points = {}
    boxes = {}
    boxes['area_of_interest_bounds'] = (1.9921737, 5.0407114, 6.479611) + (
        0.0, 0.0, 0.0) + (19.3005465, 3.77249038, 18.206831)
    boxes['map_bounds'] = (2.290418, 2.592015, 5.994555) + (
        0.0, 0.0, 0.0) + (23.05, 8.49613838, 21.11503)


class TileLandsMap(bs.Map):
    """A flat tile-based map for UFO Attack."""

    defs = _TileLandsDefs()
    name = 'Tile Lands'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        return []

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str | None:
        return 'achievementCrossHair'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'bg_tex': bs.gettexture('rampageBGColor'),
            'bg_tex_2': bs.gettexture('rampageBGColor2'),
            'bg_mesh': bs.getmesh('rampageBG'),
            'bg_mesh_2': bs.getmesh('rampageBG2'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        self.bg1 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_mesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bg_tex_2'],
            },
        )
        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_mesh_2'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bg_tex_2'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.1, 0.97)
        gnode.ambient_color = (1.3, 1.2, 1.03)
        gnode.vignette_outer = (0.62, 0.64, 0.69)
        gnode.vignette_inner = (0.97, 0.95, 0.93)


class TileLandsNightMap(bs.Map):
    """A night variant of the tile-based map for UFO Attack."""

    defs = _TileLandsDefs()
    name = 'Tile Lands Night'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        return []

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str | None:
        return 'achievementCrossHair'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'bg_tex': bs.gettexture('menuBG'),
            'bg_mesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        self.bg1 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_mesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bg_tex'],
            },
        )
        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_mesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bg_tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.5, 0.7, 1.27)
        gnode.ambient_color = (2.5, 2.5, 2.5)
        gnode.vignette_outer = (0.62, 0.64, 0.69)
        gnode.vignette_inner = (0.97, 0.95, 0.93)


bs.register_map(TileLandsMap)
bs.register_map(TileLandsNightMap)
