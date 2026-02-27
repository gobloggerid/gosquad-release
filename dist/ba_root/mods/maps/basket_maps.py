# Released under the MIT License. See LICENSE for details.
# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib import maps
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    pass


class BasketMap(maps.FootballStadium):
    name = 'BasketBall Stadium'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return []

    def __init__(self) -> None:
        super().__init__()

        gnode = bs.getactivity().globalsnode
        gnode.tint = [(0.806, 0.8, 1.0476), (1.3, 1.2, 1.0)][0]
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5


class BasketMapV2(maps.HockeyStadium):
    name = 'BasketBall Stadium V2'

    def __init__(self) -> None:
        super().__init__()

        shared = SharedObjects.get()
        self.node.materials = [shared.footing_material]
        self.node.collision_mesh = bs.getcollisionmesh('footballStadiumCollide')
        self.node.mesh = None
        self.stands.mesh = None
        self.floor.reflection = 'soft'
        self.floor.reflection_scale = [1.6]
        self.floor.color = (1.1, 0.05, 0.8)

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': bs.getmesh('thePadBG'),
                'lighting': False,
                'background': True,
                'color': (1.0, 0.2, 1.0),
                'color_texture': bs.gettexture('menuBG'),
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.floor_reflection = True
        gnode.debris_friction = 0.3
        gnode.debris_kill_height = -0.3
        gnode.tint = [(1.2, 1.3, 1.33), (0.7, 0.9, 1.0)][1]
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.66, 0.67, 0.73)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
        self.is_hockey = False

        ##################
        self.collision = bs.Material()
        self.collision.add_actions(
            actions=(('modify_part_collision', 'collide', True))
        )

        self.regions: list[bs.Node] = [
            bs.newnode(
                'region',
                attrs={
                    'position': (
                        12.676897048950195,
                        0.2997918128967285,
                        5.583303928375244,
                    ),
                    'scale': (1.01, 12, 28),
                    'type': 'box',
                    'materials': [self.collision],
                },
            ),
            bs.newnode(
                'region',
                attrs={
                    'position': (
                        11.871315956115723,
                        0.29975247383117676,
                        5.711406707763672,
                    ),
                    'scale': (50, 12, 0.9),
                    'type': 'box',
                    'materials': [self.collision],
                },
            ),
            bs.newnode(
                'region',
                attrs={
                    'position': (
                        -12.776557922363281,
                        0.30036890506744385,
                        4.96237850189209,
                    ),
                    'scale': (1.01, 12, 28),
                    'type': 'box',
                    'materials': [self.collision],
                },
            ),
        ]


bs._map.register_map(BasketMap)
bs._map.register_map(BasketMapV2)
