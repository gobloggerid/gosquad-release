# ba_meta require api 9

# Started: 7 June 2025
# Continued: 8 July 2025

from __future__ import annotations

from typing import TypedDict

import babase
import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.playerspaz import PlayerSpaz


class mapdefs:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (0.0, 1.185751251, 0.4326226188) + (
        0.0, 0.0, 0.0) + (29.8180273, 11.57249038, 18.89134176)
    boxes['edge_box'] = (-0.103873591, 0.4133341891, 0.4294651013) + (
        0.0, 0.0, 0.0) + (22.48295719, 1.290242794, 8.990252454)
    boxes['map_bounds'] = (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (
        42.09506485, 22.81173179, 29.76723155)
    points['powerup_spawn1'] = (5.414681236, 0.9515026107, -5.037912441)
    points['powerup_spawn2'] = (-5.555402285, 0.9515026107, -5.037912441)
    points['powerup_spawn3'] = (5.414681236, 0.9515026107, 5.148223181)
    points['powerup_spawn4'] = (-5.737266365, 0.9515026107, 5.148223181)
    points['spawn1'] = (-12.03866341, 0.02275111462, 0.0) + (0.5, 1.0, 4.0)
    points['spawn2'] = (12.823107149, 0.01092306765, 0.0) + (0.5, 1.0, 4.0)
    points['tnt1'] = (-0.08421587483, 0.9515026107, -0.7762602271)

class PreloadDataObjects(TypedDict):
    mesh_bg: bs.Mesh
    bg_vr_fill_mesh: bs.Mesh
    bg_tex: bs.Texture
    player_ground_material: bs.Material
    shared: SharedObjects

class StrikeBallMap(bs.Map):
    defs = mapdefs
    name = 'Strike Map'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'achievementWall'

    @classmethod
    def on_preload(cls) -> PreloadDataObjects:
        shared = SharedObjects.get()

        data = PreloadDataObjects(
            mesh_bg = bs.getmesh('doomShroomBG'),
            bg_vr_fill_mesh = bs.getmesh('natureBackgroundVRFill'),
            bg_tex = bs.gettexture('doomShroomBGColor'),
            player_ground_material=bs.Material(),
            shared=SharedObjects.get()
        )

        # Player ground material
        data['player_ground_material'].add_actions(
            actions=(('modify_part_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True)
            )
        )

        return data

    def __init__(self) -> None:
        super().__init__()
        self.preloaddata: PreloadDataObjects

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bg_tex']
            })

        bs.newnode('terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['bg_tex']
            })

        gnode = self.activity.globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5

    def player_ground(self, position: tuple[float, float, float]):
        shared = self.preloaddata['shared']

        # For our player to stand
        spaz_collide = bs.Material()
        spaz_collide.add_actions(
            conditions=(('they_are_different_node_than_us', ),
                        'and',
                        ('they_have_material', shared.player_material)),
            actions=(('modify_part_collision', 'physical', True),
                     ('modify_part_collision', 'collide', True))
        )
        ud_1_r = bs.newnode('region',
            attrs={
                'position': position,
                'scale': (1.5, 0.1, 1.5),
                'type': 'box',
                'materials': [spaz_collide, shared.footing_material] # We need footing material, so spaz could properly stand on it
            }
        )

        beauty_mat = bs.Material()
        beauty_mat.add_actions(
            actions=(('modify_part_collision', 'physical', False),
                     ('modify_part_collision', 'collide', False))
        )
        # For the beauty
        node =  bs.newnode('prop',
            owner=ud_1_r,
            attrs={
                'mesh': bs.getmesh('image1x1'),
                'light_mesh': bs.getmesh('powerupSimple'),
                'color_texture': bs.gettexture('ouyaUButton'),
                'position': position,
                'body':'puck',
                'shadow_size':0,
                'velocity':(0, 0, 0),
                'mesh_scale':1.85,
                'reflection_scale':[0],
                'materials':[beauty_mat],
                'density': 1
            }
        )

        mnode = bs.newnode('math',
            owner=ud_1_r,
            attrs={
                'input1': (0, 0, 0),
                'operation': 'add'
            }
        )
        ud_1_r.connectattr('position', mnode, 'input2')
        mnode.connectattr('output', node, 'position')

    def ground(self):
        scale = 5
        region_material = bs.Material()
        shared = self.preloaddata['shared']
        region_material.add_actions(
            conditions=(('they_are_different_node_than_us', ),
                        'and',
                        ('they_have_material', self.activity.ball_material)), # type: ignore
            actions=(('modify_part_collision', 'physical', True),
                        ('modify_part_collision', 'collide', True))
        )
        region_material.add_actions(
            conditions=(('they_are_different_node_than_us', ),
                        'and',
                        ('they_have_material', shared.player_material)), # type: ignore
            actions=(('modify_part_collision', 'physical', True),
                        ('modify_part_collision', 'collide', True))
        )
        for z_pos in -5, 0, 5:
            # For our player to stand
            region = bs.newnode('region',
                attrs={
                    'position': (0, 0, z_pos),
                    'scale': (scale, 0.1, scale),
                    'type': 'box',
                    'materials': [region_material, shared.footing_material]
                }
            )

            beauty_mat = bs.Material()
            beauty_mat.add_actions(
                actions=(('modify_part_collision', 'physical', False),
                        ('modify_part_collision', 'collide', False))
            )
            # For the beauty
            beauty =  bs.newnode('prop',
                owner=region,
                attrs={
                    'mesh': bs.getmesh('image1x1'),
                    'light_mesh': bs.getmesh('powerupSimple'),
                    'color_texture': bs.gettexture('flagColor'),
                    'position': (0, 0, z_pos),
                    'body': 'puck',
                    'shadow_size': 0,
                    'velocity': (0, 0, 0),
                    'mesh_scale': scale,
                    'reflection_scale': [1.5],
                    'materials': [beauty_mat],
                    'density': 1
                }
            )

            # For make it semi-ground (gravity-free)
            math = bs.newnode('math',
                owner=region,
                attrs={
                    'input1': (0, 0, 0),
                    'operation': 'add'
                }
            )
            region.connectattr('position', math, 'input2')
            math.connectattr('output', beauty, 'position')

    def walls_x(self):
        z_bound = 7.5
        z_min, z_max = -z_bound, z_bound
        x_bound = self.activity.wall_x_bound # type: ignore

        for x in -x_bound, x_bound:
            z = z_min
            while z < z_max:
                bs.newnode('locator', attrs={
                    'shape': 'circle',
                    'position': (x, -0.1, z),
                    'color': (0, 0.75, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.2, 0, 0.3],
                })
                z += 0.15


bs.register_map(StrikeBallMap)
