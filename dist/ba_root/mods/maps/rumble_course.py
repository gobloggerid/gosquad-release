# Released under the MIT License. See LICENSE for details.
#
# RUMBLE RUSH — A chaotic obstacle-course race for BombSquad.
#
# Navigate a grid of mystery tiles: some are safe, some will
# betray you. Bounce pads launch you skyward, icy tiles send
# you sliding, rumbling tiles shake and fall, and false tiles
# vanish the instant you touch them. First to the finish wins!

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations
from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


# ────────────────────────────────────────────────────────────
#  MAP
# ────────────────────────────────────────────────────────────

class RumbleRushMap(bs.Map):
    """A dark, compact arena for the Rumble Rush obstacle course."""

    name = 'Rumble Course'

    class defs:
        """Inline map definition data (no external mapdata module)."""
        points: dict[str, tuple] = {}
        boxes: dict[str, tuple] = {}

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['rumble_rush']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str | None:
        return 'rampagePreview'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        return {
            'bgmesh': bs.getmesh('thePadBG'),
            'bgtex': bs.gettexture('black'),
        }

    def __init__(self) -> None:
        cls = type(self)

        # Tight camera bounds centered on the grid.
        cls.defs.boxes['area_of_interest_bounds'] = (
            (0.0, 3.5, 0.0) + (0.0, 0.0, 0.0) + (28.0, 10.0, 14.0)
        )
        cls.defs.boxes['map_bounds'] = (
            (0.0, 3.5, 0.0) + (0.0, 0.0, 0.0) + (36.0, 20.0, 20.0)
        )

        # Shadow planes.
        cls.defs.points['shadow_lower_bottom'] = (0.0, 0.0, 0.0)
        cls.defs.points['shadow_lower_top'] = (0.0, 1.5, 0.0)
        cls.defs.points['shadow_upper_bottom'] = (0.0, 5.0, 0.0)
        cls.defs.points['shadow_upper_top'] = (0.0, 9.0, 0.0)

        # Spawn points (actual positioning handled by RumbleRushGame).
        for key in ('spawn1', 'spawn2'):
            cls.defs.points[key] = (-15, 5, -1 if '1' in key else 1) + (
                0.8, 0.5, 0.5,
            )
        for i, z in enumerate([-1.5, 0.0, 1.5, 0.0]):
            cls.defs.points[f'ffa_spawn{i + 1}'] = (-15, 5, z) + (
                0.5, 0.5, 0.3,
            )
        cls.defs.points['flag_default'] = (0.0, 5.0, 0.0)

        super().__init__()
        shared = SharedObjects.get()

        # Black background.
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        # Dark atmosphere.
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.6, 0.6, 0.675)
        gnode.ambient_color = (0.675, 0.675, 0.75)
        gnode.vignette_outer = (0.3, 0.3, 0.375)
        gnode.vignette_inner = (0.95, 0.95, 0.97)
        gnode.vr_camera_offset = (0, -1.0, -1.5)

        # Death region below platforms.
        self.death_region = bs.newnode(
            'region',
            attrs={
                'position': (0.0, 0.0, 0.0),
                'scale': (40.0, 2.0, 16.0),
                'type': 'box',
                'materials': [shared.death_material],
            },
        )
        self.node = self.background


bs.register_map(RumbleRushMap)
