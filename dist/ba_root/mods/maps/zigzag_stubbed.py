# Porting made easier by baport.(https://github.com/bombsquad-community/baport)

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


class ZigZagStubbed(bs.Map):
    """A very long zig-zaggy map"""

    from bascenev1lib.mapdata import zig_zag as defs

    name = 'Zigzag Stubbed'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return [
            'melee',
            'keep_away',
            'team_flag',
            'conquest',
            'king_of_the_hill',
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'zigzagPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': bs.getmesh('zigZagLevel'),
            'mesh_bottom': bs.getmesh('zigZagLevelBottom'),
            'mesh_bg': bs.getmesh('natureBackground'),
            'bg_vr_fill_mesh': bs.getmesh('natureBackgroundVRFill'),
            'collision_mesh': bs.getcollisionmesh('zigZagLevelCollide'),
            'tex': bs.gettexture('zigZagLevelColor'),
            'mesh_bg_tex': bs.gettexture('eggTex1'),
            'collide_bg': bs.getcollisionmesh('natureBackgroundCollide'),
            'railing_collision_mesh': bs.getcollisionmesh('zigZagLevelBumper'),
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['bg_material'],
                    shared.death_material,
                ],
            },
        )

        self._real_wall_material = bs.Material()

        self._real_wall_material.add_actions(
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            )
        )
        self._prop_material = bs.Material()

        self._prop_material.add_actions(
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False),
            )
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.0, 1.15, 1.15)
        gnode.ambient_color = (1.0, 1.15, 1.15)
        gnode.vignette_outer = (0.57, 0.59, 0.63)
        gnode.vignette_inner = (0.97, 0.95, 0.93)
        gnode.vr_camera_offset = (-1.5, 0, 0)

        self.create_ramp(-4.5, -2.4)
        self.create_ramp(-4.5, 0)

        self.create_ramp(-1.4, -4.7)
        self.create_ramp(-1.4, -2.3)

        self.create_ramp(1.5, -2.4)
        self.create_ramp(1.5, 0)

    def create_ramp(self, x, z):
        shared = SharedObjects.get()
        self.ud_1_r = bs.newnode(
            'region',
            attrs={
                'position': (x, 2.45, z),
                'scale': (2, 1, 2.5),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    self._real_wall_material,
                ],
            },
        )

        self.floor = bs.newnode(
            'prop',
            owner=self.ud_1_r,
            attrs={
                'mesh': bs.getmesh('image1x1'),
                'light_mesh': bs.getmesh('powerupSimple'),
                'position': (2, 7, 2),
                'body': 'puck',
                'shadow_size': 0.0,
                'velocity': (0, 0, 0),
                'color_texture': bs.gettexture('tnt'),
                'mesh_scale': 2.45,
                'reflection_scale': [0.5],
                'materials': [self._prop_material],
                'density': 9000000000,
            },
        )
        mnode = bs.newnode(
            'math',
            owner=self.ud_1_r,
            attrs={'input1': (0, 0.6, 0), 'operation': 'add'},
        )

        self.ud_1_r.connectattr('position', mnode, 'input2')
        mnode.connectattr('output', self.floor, 'position')


bs._map.register_map(ZigZagStubbed)
