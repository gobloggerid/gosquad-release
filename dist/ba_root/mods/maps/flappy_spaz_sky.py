# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


PLAY_Z = -6.0
PLAY_Z_DEPTH = 6.0

PLAY_X_MIN = -12.0
PLAY_X_MAX = 12.0
PLAY_Y_MIN = 1.0
PLAY_Y_MAX = 14.0

PIPE_SPAWN_X = PLAY_X_MAX + 3.0
PIPE_DELETE_X = PLAY_X_MIN - 3.0

UPDATE_INTERVAL = 1.0 / 30.0

NUM_CHANNELS = 8
CHANNEL_WIDTH = 1.0
WALL_THICKNESS = 0.15

# The lowest internal pipe speed (3.0) is displayed as "1.0".
SPEED_OFFSET = 2.0


# ---------------------------------------------------------------------------
#  Map
# ---------------------------------------------------------------------------


class FlappySpazMap(bs.Map):
    """Sky-only map using the Rampage background."""

    name = 'Flappy Spaz Sky'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee', 'keep_away', 'team_flag']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'rampagePreview'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        return {
            'bgmesh': bs.getmesh('rampageBG'),
            'bgtex': bs.gettexture('rampageBGColor'),
            'bgmesh2': bs.getmesh('rampageBG2'),
            'bgtex2': bs.gettexture('rampageBGColor2'),
            'vr_fill_mesh': bs.getmesh('rampageVRFill'),
        }

    @classmethod
    def get_def_points(cls, point_name: str) -> list:
        cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
        cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0
        z = PLAY_Z
        lanes = [(cx - i, cy, z) for i in range(NUM_CHANNELS)]
        if point_name == 'spawn':
            return [(x, y, z, 0, 0, 0) for x, y, z in lanes[:2]]
        if point_name == 'ffa_spawn':
            return [(x, y, z, 0, 0, 0) for x, y, z in lanes]
        if point_name == 'flag':
            return [lanes[0]]
        if point_name == 'spawn_by_flag':
            return [(x, y, z, 0, 0, 0) for x, y, z in lanes[:2]]
        return []

    @classmethod
    def get_def_point(cls, point_name: str) -> tuple | None:
        cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
        cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0
        if point_name == 'flag_default':
            return (cx, cy, PLAY_Z)
        return None

    @classmethod
    def get_def_bound_box(cls, box_name: str) -> tuple | None:
        if box_name == 'area_of_interest_bounds':
            return (
                PLAY_X_MIN, PLAY_Y_MIN, PLAY_Z - 0.5,
                PLAY_X_MAX, PLAY_Y_MAX, PLAY_Z + 0.5,
            )
        if box_name == 'map_bounds':
            return (
                PLAY_X_MIN - 10, PLAY_Y_MIN - 10, PLAY_Z - 10,
                PLAY_X_MAX + 10, PLAY_Y_MAX + 15, PLAY_Z + 10,
            )
        return None

    def __init__(self) -> None:
        super().__init__()

        # Rampage background layers.
        self.background = bs.newnode('terrain', attrs={
            'mesh': self.preloaddata['bgmesh'],
            'lighting': False,
            'background': True,
            'color_texture': self.preloaddata['bgtex'],
        })
        self.bg2 = bs.newnode('terrain', attrs={
            'mesh': self.preloaddata['bgmesh2'],
            'lighting': False,
            'background': True,
            'color_texture': self.preloaddata['bgtex2'],
        })
        bs.newnode('terrain', attrs={
            'mesh': self.preloaddata['vr_fill_mesh'],
            'lighting': False,
            'vr_only': True,
            'background': True,
            'color_texture': self.preloaddata['bgtex2'],
        })
        self.node = self.background

        # Globals.
        gnode = bs.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.2, 1.1, 0.97)
        gnode.ambient_color = (1.3, 1.2, 1.03)
        gnode.vignette_outer = (0.62, 0.64, 0.69)
        gnode.vignette_inner = (0.97, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True


bs.register_map(FlappySpazMap)
