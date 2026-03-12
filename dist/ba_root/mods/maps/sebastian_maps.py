# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
# Version 1.7.33
# Maps by: SEBASTIAN2059-Zacker Tz
#  - Maps:
#  - Neo Zone
#  - Big H
#  - The Limbo
#  - Platforms
#  - Powerups Factory
#  - Skull Temple
#  - Bottom Rampage
#  - Collosal Bridgit
#  - Collosal Monkey
#  - Tower Zoe
#  - The Crusade
#  - The Arena
#  - Island Mine
#  - Space Thoughts

# Rename mod: baAllMaps -> baMaps
# tanks esmothi


from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

##Complementos##


class CollideBox:
    def __init__(
        self,
        position: Sequence[float] = (0, 0, 0),
        scale: Sequence[float] = (1, 1, 1),
        color: Sequence[float] = (1, 1, 1),
        visible: bool = True,
        ice: bool = False,
        death: bool = False,
    ):
        shared = SharedObjects.get()
        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.no_physical_collide = bs.Material()
        self.no_physical_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
            ),
        )
        self.ice_material = bs.Material()
        self.ice_material.add_actions(
            actions=('modify_part_collision', 'friction', 0.01)
        )

        mats = [self._collide_with_player, shared.footing_material]
        if ice:
            mats.append(self.ice_material)
        if death:
            mats = [self.no_physical_collide, shared.death_material]

        self.region = bs.newnode(
            'region',
            attrs={
                'position': position,
                'scale': scale,
                'type': 'box',
                'materials': mats,
            },
        )
        if visible:
            locator = bs.newnode(
                'locator',
                attrs={
                    'shape': 'box',
                    'color': color,
                    'opacity': 1,
                    'drawShadow': False,
                    'draw_beauty': True,
                    'additive': False,
                },
            )
            self.region.connectattr('position', locator, 'position')
            self.region.connectattr('scale', locator, 'size')


class FadeEfect:
    def __init__(self, map_tint=(1, 1, 1)):
        gnode = bs.getactivity().globalsnode
        bs.animate_array(
            node=gnode,
            attr='tint',
            size=3,
            keys={0: (0, 0, 0), 0.5: (0, 0, 0), 1.2: map_tint},
            loop=False,
        )

        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 325),
                'text': 'Building Map...',
                'color': (1, 1, 1),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': 600,
                'shadow': 1.0,
                'flatness': 1.0,
                'scale': 2,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        bs.animate(text, 'opacity', {0: 1, 0.2: 1, 0.7: 0})
        bs.timer(1, text.delete)

        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 295),
                'text': 'Maps by Sebastian2059-ZackerTz',
                'color': (0.1, 0.0, 0.76),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': 600,
                'shadow': 1.0,
                'flatness': 1.0,
                'scale': 0.7,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        bs.animate(text, 'opacity', {0: 1, 0.2: 1, 0.7: 0})
        bs.timer(1, text.delete)


class Credits:
    """Don't delete this if you respect other people's work"""

    def __init__(self):
        t = bs.newnode(
            'text',
            attrs={
                'text': 'Maps by: SEBASTIAN2059-Zacker Tz',
                'scale': 0.6,
                'position': (0, 0),
                'opacity': 0.1,
                'shadow': 0.5,
                'flatness': 1.2,
                'color': (1, 1, 1),
                'h_align': 'center',
                'v_attach': 'bottom',
            },
        )  # :bobolu:


# Ultra secret
# NEW_OBJECTS
class CustomModel(bs.Actor):
    def __init__(
        self,
        position: Sequence[float] = (0, 0, 0),
        mesh: str = '',
        texture: str = '',
        scale: float = 1.0,
    ):
        super().__init__()

        shared = SharedObjects.get()

        self._collide_custom = bs.Material()
        self.dont_collide = bs.Material()

        self._collide_custom.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self._collide_custom.add_actions(
            conditions=('they_have_material', self.dont_collide),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self.dont_collide.add_actions(
            conditions=('they_have_material', self._collide_custom),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self.position = position
        self.node = bs.newnode(
            'prop',
            attrs={
                'body': 'puck',
                'position': self.position,
                'mesh': bs.getmesh(mesh),
                'color_texture': bs.gettexture(texture),
                'mesh_scale': scale,
                'body_scale': 1.0,
                'shadow_size': 0.0,
                'gravity_scale': 1.0,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'is_area_of_interest': False,
                'materials': [self.dont_collide],
            },
        )
        self.node.extra_acceleration = (0, 21.5, 0)
        self.region = bs.newnode(
            'region',
            attrs={
                'position': (
                    self.position[0],
                    self.position[1] - 0.6,
                    self.position[2] - 0.54,
                ),
                'scale': (3, 0.5, 0.5),
                'type': 'box',
                'materials': (self._collide_custom,),
            },
        )
        self.region1 = bs.newnode(
            'region',
            attrs={
                'position': (
                    self.position[0],
                    self.position[1] + 1,
                    self.position[2] + 0.54,
                ),
                'scale': (3, 0.5, 0.5),
                'type': 'box',
                'materials': (self._collide_custom,),
            },
        )

        def stop():
            self.node.extra_acceleration = (0, 0, 0)
            self.node.velocity = (0, 0, 0)
            self.node.gravity_scale = 0

        def move():
            bs.animate_array(
                node=self.region,
                attr='scale',
                size=3,
                keys={0: (3, 0.5, 0.5), 0.03: (3, 4, 0.5)},
                loop=False,
            )
            bs.animate_array(
                node=self.region1,
                attr='scale',
                size=3,
                keys={0: (3, 0.5, 0.5), 0.03: (3, 4, 0.5)},
                loop=False,
            )
            bs.timer(0.035, stop)

        bs.timer(0.001, move)


class CustomModelR3(bs.Actor):
    def __init__(
        self,
        position: Sequence[float] = (0, 0, 0),
        mesh: str = '',
        texture: str = '',
        scale: float = 1.0,
        rotate='right',
    ):
        super().__init__()

        shared = SharedObjects.get()

        self._collide_custom = bs.Material()
        self.dont_collide = bs.Material()

        self._collide_custom.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self._collide_custom.add_actions(
            conditions=('they_have_material', self.dont_collide),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self.dont_collide.add_actions(
            conditions=('they_have_material', self._collide_custom),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self.position = position

        x = self.position[0]
        y = self.position[1]
        z = self.position[2]

        self.mesh = bs.newnode(
            'prop',
            attrs={
                'body': 'puck',
                'position': (x, y, z),
                'mesh': bs.getmesh(mesh),
                'color_texture': bs.gettexture(texture),
                'mesh_scale': scale,
                'body_scale': 1.0,
                'shadow_size': 0.0,
                'gravity_scale': 1.0,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'is_area_of_interest': False,
                'materials': [self.dont_collide],
            },
        )
        self.mesh.extra_acceleration = (0, 21.5, 0)

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (x, y - 0.6, z - 0.54),
                'scale': (3, 0.5, 0.5),
                'type': 'box',
                'materials': (self._collide_custom,),
            },
        )
        self.r2 = bs.newnode(
            'region',
            attrs={
                'position': (x, y + 1, z + 0.54),
                'scale': (3, 0.5, 0.5),
                'type': 'box',
                'materials': (self._collide_custom,),
            },
        )

        def stop():
            # bs.screenmessage('stop')
            self.mesh.extra_acceleration = (0, 0, 0)
            self.mesh.velocity = (0, 0, 0)
            self.mesh.gravity_scale = 0

            def stop_v2():
                self.mesh.velocity = (0, 0, 0)

            bs.timer(0.1, stop_v2)

        def move3():
            self.r1.scale = (0.5, 0.5, 3)
            self.r2.scale = (0.5, 0.5, 3)
            if rotate == 'right':
                self.r1.position = (x + 0.7, y + 0.54, z)
                self.r2.position = (x - 0.7, y - 0.54, z)
            elif rotate == 'left':
                self.r1.position = (x - 0.7, y + 0.54, z)
                self.r2.position = (x + 0.7, y - 0.54, z)

            bs.animate_array(
                node=self.r1,
                attr='scale',
                size=3,
                keys={0: (0.5, 0.5, 3), 0.03: (4, 0.5, 3)},
                loop=False,
            )
            bs.animate_array(
                node=self.r2,
                attr='scale',
                size=3,
                keys={0: (0.5, 0.5, 3), 0.03: (4, 0.5, 3)},
                loop=False,
            )
            bs.timer(0.035, stop)

        def move2():
            self.r1.scale = (0.5, 3, 0.5)
            self.r2.scale = (0.5, 3, 0.5)
            if rotate == 'left':
                self.r1.position = (x + 0.54, y, z - 0.7)
                self.r2.position = (x - 0.54, y, z + 0.7)
            elif rotate == 'right':
                self.r1.position = (x + 0.54, y, z + 0.7)
                self.r2.position = (x - 0.54, y, z - 0.7)
            bs.animate_array(
                node=self.r1,
                attr='scale',
                size=3,
                keys={0: (0.5, 3, 0.5), 0.03: (0.5, 3, 4)},
                loop=False,
            )
            bs.animate_array(
                node=self.r2,
                attr='scale',
                size=3,
                keys={0: (0.5, 3, 0.5), 0.03: (0.5, 3, 4)},
                loop=False,
            )
            bs.timer(0.1, move3)

        def move():
            bs.animate_array(
                node=self.r1,
                attr='scale',
                size=3,
                keys={0: (3, 0.5, 0.5), 0.03: (3, 4, 0.5)},
                loop=False,
            )
            bs.animate_array(
                node=self.r2,
                attr='scale',
                size=3,
                keys={0: (3, 0.5, 0.5), 0.03: (3, 4, 0.5)},
                loop=False,
            )
            bs.timer(0.05, move2)

        bs.timer(0.001, move)


class CustomModelR2(bs.Actor):
    def __init__(
        self,
        position: Sequence[float] = (0, 0, 0),
        mesh: str = '',
        texture: str = '',
        scale: float = 1.0,
        rotate='right',
    ):
        super().__init__()

        shared = SharedObjects.get()

        self._collide_custom = bs.Material()
        self.dont_collide = bs.Material()

        self._collide_custom.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self._collide_custom.add_actions(
            conditions=('they_have_material', self.dont_collide),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self.dont_collide.add_actions(
            conditions=('they_have_material', self._collide_custom),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self.position = position

        x = self.position[0]
        y = self.position[1]
        z = self.position[2]

        self.mesh = bs.newnode(
            'prop',
            attrs={
                'body': 'puck',
                'position': (x, y, z),
                'mesh': bs.getmesh(mesh),
                'color_texture': bs.gettexture(texture),
                'mesh_scale': scale,
                'body_scale': 1.0,
                'shadow_size': 0.0,
                'gravity_scale': 1.0,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'is_area_of_interest': False,
                'materials': [self.dont_collide],
            },
        )
        self.mesh.extra_acceleration = (0, 21.5, 0)

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (x, y - 0.6, z - 0.54),
                'scale': (3, 0.5, 0.5),
                'type': 'box',
                'materials': (self._collide_custom,),
            },
        )
        self.r2 = bs.newnode(
            'region',
            attrs={
                'position': (x, y + 1, z + 0.54),
                'scale': (3, 0.5, 0.5),
                'type': 'box',
                'materials': (self._collide_custom,),
            },
        )

        def stop():
            # bs.screenmessage('stop')
            self.mesh.extra_acceleration = (0, 0, 0)
            self.mesh.velocity = (0, 0, 0)
            self.mesh.gravity_scale = 0

            def stop_v2():
                self.mesh.velocity = (0, 0, 0)

            bs.timer(0.1, stop_v2)

        def move2():
            self.r1.scale = (0.5, 3, 0.5)
            self.r2.scale = (0.5, 3, 0.5)
            if rotate == 'left':
                self.r1.position = (x + 0.54, y, z - 0.7)
                self.r2.position = (x - 0.54, y, z + 0.7)
            elif rotate == 'right':
                self.r1.position = (x + 0.54, y, z + 0.7)
                self.r2.position = (x - 0.54, y, z - 0.7)
            bs.animate_array(
                node=self.r1,
                attr='scale',
                size=3,
                keys={0: (0.5, 3, 0.5), 0.03: (0.5, 3, 4)},
                loop=False,
            )
            bs.animate_array(
                node=self.r2,
                attr='scale',
                size=3,
                keys={0: (0.5, 3, 0.5), 0.03: (0.5, 3, 4)},
                loop=False,
            )
            bs.timer(0.035, stop)

        def move():
            bs.animate_array(
                node=self.r1,
                attr='scale',
                size=3,
                keys={0: (3, 0.5, 0.5), 0.03: (3, 4, 0.5)},
                loop=False,
            )
            bs.animate_array(
                node=self.r2,
                attr='scale',
                size=3,
                keys={0: (3, 0.5, 0.5), 0.03: (3, 4, 0.5)},
                loop=False,
            )
            bs.timer(0.1, move2)

        bs.timer(0.001, move)


###End###


# Map by Zacker Tz
# Map #1
class neo_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)
    points['ffa_spawn1'] = (-10, 3.17, 0) + (1.0, 0.1, 1.0)
    points['ffa_spawn2'] = (10, 3.17, 0) + (1.0, 0.1, 1.0)
    points['ffa_spawn3'] = (-5.25, 3.17, -1.75) + (0.5, 0.1, 0.5)
    points['ffa_Spawn4'] = (5.25, 3.17, -1.75) + (0.5, 0.1, 0.5)
    points['spawn1'] = (-11, 3.17, 0) + (1.0, 0.1, 1.0)
    points['spawn2'] = (11, 3.17, 0) + (1.0, 0.1, 1.0)
    points['flag1'] = (-12.0, 3.3, 0) + (2.0, 0.1, 2.0)
    points['flag2'] = (12.0, 3.3, 0) + (2.0, 0.1, 2.0)
    points['flag_default'] = (0, 3.3, 1.75)
    points['powerup_spawn1'] = (-11, 4.0, -1.75)
    points['powerup_spawn2'] = (-11, 4.0, 1.75)
    points['powerup_spawn3'] = (-1.75, 4.0, 0)
    points['powerup_spawn4'] = (1.75, 4.0, 0.0)
    points['powerup_spawn5'] = (11, 4.0, -1.75)
    points['powerup_spawn6'] = (11, 4.0, 1.75)


class NeoZone(bs.Map):
    """Agent john's former workplace"""

    defs = neo_defs()
    name = 'Neo Zone'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'king_of_the_hill', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'rgbStripes'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('landMine'),
            'tex': bs.gettexture('landMine'),
            'bgtex': bs.gettexture('black'),
            'bgmesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )

        self._map_mesh = bs.getmesh('image1x1')
        self._map_mesh2 = bs.getmesh('tnt')
        self._map_tex = bs.gettexture('powerupIceBombs')
        self._map_tex1 = bs.gettexture('ouyaUButton')

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        locations = [
            (7.0, 0.0, 0),
            (5.25, 0.0, 0),
            (5.25, 0.0, -1.75),
            (3.5, 0.0, -1.75),
            (1.75, 0.0, -1.75),
            (1.75, 0.0, 0),
            (1.75, 0.0, 1.75),
            (0, 0.0, 1.75),
            (-7.0, 0.0, 0),
            (-5.25, 0.0, 0),
            (-5.25, 3.17, -1.75),
            (-3.5, 0.0, -1.75),
            (-1.75, 0.0, -1.75),
            (-1.75, 0.0, 0),
            (-1.75, 0.0, 1.75),
        ]
        num = 0

        for pos in locations:
            color = (
                (0, 1, 0)
                if num in [0, 1, 5, 8, 9, 13]
                else (
                    (0, 0, 1)
                    if num in [6, 7, 14]
                    else (
                        (1, 0, 0) if num in [2, 3, 4, 10, 11, 12] else (1, 1, 1)
                    )
                )
            )
            self.decor = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': (pos[0], 3.17, pos[2]),
                    'mesh': self._map_mesh,
                    'mesh_scale': 1.7,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex1,
                    'reflection': 'soft',
                    'reflection_scale': [0.5],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )
            self.region = bs.newnode(
                'region',
                attrs={
                    'position': (pos[0], 2.3, pos[2]),
                    'scale': (1.9, 1.9, 1.9),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'box',
                    'position': (pos[0], 2.3, pos[2]),
                    'color': color,
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [1.75, 1.75, 1.75],
                },
            )
            num += 1

        # Sides
        side_locations = [(-10.5, 2.3, 0), (10.5, 2.3, 0)]
        for pos in side_locations:
            self.big_region = bs.newnode(
                'region',
                attrs={
                    'position': pos,
                    'scale': (5.7, 1.9, 5.7),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            self.big_zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'box',
                    'position': pos,
                    'color': (0, 1, 1.5),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [5.25, 1.75, 5.25],
                },
            )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.happy_thoughts_mode = False
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()


# Map by Sebastian2059
# Map #2
class c_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)
    points['ffa_spawn1'] = (-9, 0.5, -3) + (1.0, 0.1, 5.0)
    points['ffa_spawn2'] = (9, 0.5, -3) + (1.0, 0.1, 5.0)
    points['ffa_spawn3'] = (-6, 0.5, -6.0) + (2.0, 0.1, 1.0)
    points['ffa_Spawn4'] = (6, 0.5, 0.0) + (2.0, 0.1, 1.0)
    points['ffa_spawn5'] = (6, 0.5, -6.0) + (2.0, 0.1, 1.0)
    points['ffa_Spawn6'] = (-6, 0.5, 0.0) + (2.0, 0.1, 1.0)
    points['spawn1'] = (-9, 0.5, -3) + (1.0, 0.1, 1.0)
    points['spawn2'] = (9, 0.5, -3) + (1.0, 0.1, 1.0)
    points['flag1'] = (-10.0, 0.8, -3) + (2.0, 0.1, 2.0)
    points['flag2'] = (10.0, 0.8, -3) + (2.0, 0.1, 2.0)
    points['flag_default'] = (0, 0.8, -3.0)
    points['powerup_spawn1'] = (-9, 1.0, -8)
    points['powerup_spawn2'] = (-9, 1.0, 3)
    points['powerup_spawn3'] = (-1.5, 1.0, -8.25)
    points['powerup_spawn4'] = (1.5, 1.0, -8.25)
    points['powerup_spawn5'] = (-1.5, 1.0, 2.25)
    points['powerup_spawn6'] = (1.5, 1.0, 2.25)
    points['powerup_spawn7'] = (9, 1.0, -8)
    points['powerup_spawn8'] = (9, 1.0, 3)

    points['race_mine1'] = (-1.5, 0.7, -0.7)
    points['race_mine2'] = (-1.5, 0.7, 0.7)
    points['race_mine3'] = (-4.5, 0.7, 0.0)
    points['race_mine4'] = (4.5, 0.7, 0.0)
    points['race_mine5'] = (4.5, 0.7, -6.0)
    points['race_mine6'] = (-4.5, 0.7, -6.0)
    points['race_mine7'] = (0.0, 0.7, -6.0)
    points['race_mine8'] = (-10.0, 0.7, -4.5)
    points['race_mine9'] = (10.0, 0.7, -4.5)
    points['race_mine10'] = (10.0, 0.7, -1.5)
    points['race_mine11'] = (-10.0, 0.7, -1.5)

    points['race_point1'] = (0.0, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point2'] = (3.5, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point3'] = (7.0, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point4'] = (9.0, 0.5, -2.0) + (1.5, 2.0, 0.3)
    points['race_point5'] = (9.0, 0.5, -4.0) + (1.5, 2.0, 0.3)
    points['race_point6'] = (7.0, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point7'] = (3.5, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point8'] = (0.0, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point9'] = (-3.5, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point10'] = (-7.0, 0.5, -6.0) + (0.3, 2.0, 1.5)
    points['race_point11'] = (-9.0, 0.5, -2.0) + (1.5, 2.0, 0.3)
    points['race_point12'] = (-9.0, 0.5, -4.0) + (1.5, 2.0, 0.3)
    points['race_point13'] = (-7.0, 0.5, 0.0) + (0.3, 2.0, 1.5)
    points['race_point14'] = (-3.5, 0.5, 0.0) + (0.3, 2.0, 1.5)


class CMap(bs.Map):
    """Jack Morgan used to run here"""

    defs = c_defs()
    name = 'Big H'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'king_of_the_hill', 'keep_away', 'team_flag', 'race']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bigG'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('landMine'),
            'tex': bs.gettexture('landMine'),
            'bgtex': bs.gettexture('black'),
            'bgmesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self.ice_material = bs.Material()
        self.ice_material.add_actions(
            actions=('modify_part_collision', 'friction', 0.01)
        )

        self._map_mesh = bs.getmesh('image1x1')
        self._map_mesh2 = bs.getmesh('tnt')
        self._map_tex = bs.gettexture('powerupIceBombs')
        self._map_tex1 = bs.gettexture('circleOutlineNoAlpha')
        self._map_tex2 = bs.gettexture('black')

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        posS = [(0.0, 0.05, 0)]
        for m_pos in posS:
            self.mv_center = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 35,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex2,
                    'reflection': 'soft',
                    'reflection_scale': [0],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        locations = [
            (-9, 0.0, -3.0),
            (9, 0.0, -3.0),
            (0.0, 0.0, -6.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, -3.0),
        ]
        scales = [
            [3.0, 1.0, 14.0],
            [3.0, 1.0, 14.0],
            [15.0, 1.0, 3.0],
            [15.0, 1.0, 3.0],
            [3.0, 1.0, 3.0],
        ]
        index = 0
        for pos in locations:
            #
            scale = scales[index]
            bs.newnode(
                'region',
                attrs={
                    'position': pos,
                    'scale': scale,
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            bs.newnode(
                'locator',
                attrs={
                    'shape': 'box',
                    'position': pos,
                    'color': (1, 1, 1),
                    'opacity': 1,
                    'drawShadow': False,
                    'draw_beauty': True,
                    'additive': False,
                    'size': scale,
                },
            )
            index += 1

        pos = [-3.0, 0.0, -8.25]
        for p in range(10):
            scale = [1.5, 1.0, 1.5]
            bs.newnode(
                'region',
                attrs={
                    'position': pos,
                    'scale': scale,
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            bs.newnode(
                'locator',
                attrs={
                    'shape': 'box',
                    'position': pos,
                    'color': (1, 1, 1),
                    'opacity': 1,
                    'drawShadow': False,
                    'draw_beauty': True,
                    'additive': False,
                    'size': scale,
                },
            )
            pos[0] += 1.5
            if p == 4:
                pos[0] = -3.0
                pos[2] = 2.25

        try:
            self._gamemode = bs.getactivity().name
        except Exception:
            # print('error')
            pass
        if self._gamemode == 'Race':
            #   print('Es carrera')
            ice_locations = [
                (-8, 0.0, 0),
                (8, 0.0, 0),
                (-8, 0.0, -6),
                (8, 0.0, -6),
                (-9, 0.0, -3),
                (9, 0.0, -3),
            ]

            for pos in ice_locations:
                scale = [3.0, 1.025, 3.0]
                bs.newnode(
                    'region',
                    attrs={
                        'position': pos,
                        'scale': scale,
                        'type': 'box',
                        'materials': (
                            self._collide_with_player,
                            shared.footing_material,
                            self.ice_material,
                        ),
                    },
                )
                bs.newnode(
                    'locator',
                    attrs={
                        'shape': 'box',
                        'position': pos,
                        'color': (0, 1, 1),
                        'opacity': 1,
                        'drawShadow': False,
                        'draw_beauty': True,
                        'additive': False,
                        'size': scale,
                    },
                )
        # Meme
        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 21, 0),
                'text': 'Tz = Tz \nTz = Trolleador Zaturno\nTrolleador Zaturno = Tazer\nTazer = The Game ',
                'in_world': True,
                'shadow': 1.5,
                'flatness': 0.7,
                'color': (1, 1, 1.2),
                'opacity': 1.0,
                'scale': 0.023,
                'h_align': 'center',
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.happy_thoughts_mode = False
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()


# Map by Zaker DC [Inspiration from a map of Sebastian]
# Map 3#
class factory_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)

    points['ffa_spawn1'] = (-8, 3.5, 0)
    points['ffa_spawn2'] = (8, 3.5, 0)
    points['ffa_spawn3'] = (3.4, 3.75, 3)
    points['ffa_Spawn4'] = (-3.4, -0.75, -3)

    points['spawn1'] = (-8, 3.5, 0) + (1.0, 0.1, 1.0)
    points['spawn2'] = (8, 3.5, 0) + (1.0, 0.1, 1.0)

    points['flag1'] = (-9.5, 3.5, 0) + (2.0, 0.1, 2.0)
    points['flag2'] = (9.5, 3.5, 0) + (2.0, 0.1, 2.0)
    points['flag_default'] = (0, 3.7, 0)

    points['powerup_spawn1'] = (4.8, 3.65, 3)
    points['powerup_spawn2'] = (-4.8, 3.65, -3)
    points['powerup_spawn3'] = (-4.2, 3.7, 1.4)
    points['powerup_spawn4'] = (4.1, 3.7, -1.4)


class FactoryMap(bs.Map):
    """Grambledorf former experiment room"""

    defs = factory_defs
    name = 'Powerups Factory'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'king_of_the_hill', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'zigZagLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('landMine'),
            'tex': bs.gettexture('landMine'),
            'bgtex': bs.gettexture('bg'),
            'bgmesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )

        self._map_mesh = bs.getmesh('image1x1')
        self._map_mesh2 = bs.getmesh('tnt')
        self._map_tex1 = bs.gettexture('powerupImpactBombs')
        self._map_tex2 = bs.gettexture('reflectionChar_-y')
        self._map_tex3 = bs.gettexture('flagPoleColor')

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color': (1.3, 1.3, 1.3),
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        posXD = [
            (1.5, 2.3, 0),
            (-1.5, 2.3, 0),
            (0, 2.3, 0),
            (4.0, 2.3, 1.5),
            (4.0, 2.3, -1.5),
            (4.0, 2.3, 0),
            (4.8, 2.3, 3),
            (3.4, 2.3, 3),
            (1.9, 2.3, 3),
            (-4.0, 2.3, 1.5),
            (-4.0, 2.3, -1.5),
            (-4.0, 2.3, 0),
            (-4.8, 2.3, -3),
            (-3.4, 2.3, -3),
            (-1.9, 2.3, -3),
        ]
        for m_pos in posXD:
            self.mv_center = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh2,
                    'mesh_scale': 2.2,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex1,
                    'reflection': 'soft',
                    'reflection_scale': [0.5],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        posXD = [(-3.4, 0.75, -3), (-3.4, -0.75, -3)]
        for m_pos in posXD:
            self.mc_center = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (1.5, 1.5, 1.5),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )

        for m_pos in [(0, 2.3, 0)]:
            self.mc_center = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (4.5, 1.5, 1.5),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )

        for m_pos in [(4.0, 2.3, 0), (-4.0, 2.3, 0)]:
            self.mc_center = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (1.5, 1.5, 4.5),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )

        for m_pos in [(3.4, 2.3, 3), (-3.4, 2.3, -3)]:
            self.mc_center = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (4.5, 1.5, 1.5),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )

        # Cajas Grandes Normales
        for m_pos in [
            (8.7, 1.72, 0),
            (6.10, 1.72, 0),
            (-8.7, 1.72, 0),
            (-6.10, 1.72, 0),
        ]:
            self.mv_d2 = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh2,
                    'mesh_scale': 3.8,
                    'color_texture': self._map_tex1,
                    'reflection_scale': [1.0],
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'reflection': 'soft',
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        for m_pos in [(7.45, 1.72, 0), (-7.45, 1.72, 0)]:
            self.mc_d2 = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (5.25, 2.7, 2.7),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )

        # Superficie
        pos = [
            (-1.5, 3.075, 0),
            (0, 3.075, 0),
            (1.5, 3.075, 0),
            (4.0, 3.075, 1.5),
            (4.0, 3.075, -1.5),
            (4.0, 3.075, 0),
            (-4.0, 3.075, -1.5),
            (-4.0, 3.075, 1.5),
            (-4.0, 3.075, 0),
            (-4.8, 3.075, -3),
            (-3.4, 3.075, -3),
            (-1.9, 3.075, -3),
            (4.8, 3.075, 3),
            (3.4, 3.075, 3),
            (1.9, 3.075, 3),
        ]
        for m_pos in pos:
            self.mv_centera = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'color_texture': self._map_tex3,
                    'mesh_scale': 1.5,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'reflection': 'soft',
                    'reflection_scale': [0.5],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.17)
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.8, 0.7, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()


# Map by SEBASTIAN2059
# Map 4#
class platforms_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 4, 0) + (0, 0, 0) + (50, 10, 20)
    boxes['edge_box'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (40, 2, 10)
    boxes['map_bounds'] = (0, 4, 0) + (0, 0, 0) + (28, 10, 28)
    points['ffa_spawn1'] = (-10, 3.5, 0) + (2.0, 0.1, 2.0)
    points['ffa_spawn2'] = (10, 3.5, 0) + (2.0, 0.1, 2.0)
    points['ffa_spawn3'] = (0, 3.5, 1)
    points['ffa_Spawn4'] = (0, 3.5, -1)
    points['spawn1'] = (-10, 3.5, 0) + (2.0, 0.1, 2.0)
    points['spawn2'] = (10, 3.5, 0) + (2.0, 0.1, 2.0)
    points['flag1'] = (-12, 3.5, 0) + (2.0, 0.1, 2.0)
    points['flag2'] = (12, 3.5, 0) + (2.0, 0.1, 2.0)
    points['flag_default'] = (0, 3.5, 0)
    points['powerup_spawn1'] = (-11.8, 4, -1.8)
    points['powerup_spawn2'] = (-8.2, 4, 1.8)
    points['powerup_spawn3'] = (8.2, 4, -1.8)
    points['powerup_spawn4'] = (11.8, 4, 1.8)


class PlatformsMap(bs.Map):
    """Plataforms!"""

    defs = platforms_defs
    name = 'Platforms'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'king_of_the_hill', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bridgitLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'bgtex': bs.gettexture('bg'),
            'bgmesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )

        self._map_mesh = bs.getmesh('image1x1')
        self._map_tex = bs.gettexture('powerupIceBombs')
        self._map_tex1 = bs.gettexture('powerupPunch')
        self._map_tex2 = bs.gettexture('powerupImpactBombs')

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        for m_pos in [(-10, 2.5, 0), (10, 2.5, 0)]:
            self.e_cnnt = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 0.5, 0), 'operation': 'add'},
            )
            self.mc = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (5.0, 1, 5.0),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            self.mv = bs.newnode(
                'prop',
                owner=self.mc,
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 5.0,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex,
                    'reflection': 'soft',
                    'reflection_scale': [1.0],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )
            self.mc.connectattr('position', self.e_cnnt, 'input2')
            self.e_cnnt.connectattr('output', self.mv, 'position')

        for m_pos in [(0, 2.5, 1.35), (0, 2.5, -1.35)]:
            self.c_cnnt = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 0.5, 0), 'operation': 'add'},
            )
            self.mc_center = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (2.7, 1, 2.7),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            self.mv_center = bs.newnode(
                'prop',
                owner=self.mc,
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 2.7,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex,
                    'reflection': 'soft',
                    'reflection_scale': [1.0],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )
            self.mc_center.connectattr('position', self.c_cnnt, 'input2')
            self.c_cnnt.connectattr('output', self.mv_center, 'position')

        for m_pos in [(1.1, 3.01, 0), (-1.1, 3.01, 0)]:
            self.dec = bs.newnode(
                'prop',
                owner=self.mc,
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 0.5,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex2,
                    'reflection': 'soft',
                    'reflection_scale': [1.0],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        pos = [(-5.9, 2.5, 1), (-3, 2.5, -1), (3, 2.5, 1), (5.9, 2.5, -1)]
        for m_pos in pos:
            self.m_cnnt = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 0.5, 0), 'operation': 'add'},
            )
            self.mc_a = bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (2.5, 1, 2.5),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            self.mv_a = bs.newnode(
                'prop',
                owner=self.mc,
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 2.5,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex1,
                    'reflection': 'soft',
                    'reflection_scale': [1.0],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )
            self.mc_a.connectattr('position', self.m_cnnt, 'input2')
            self.m_cnnt.connectattr('output', self.mv_a, 'position')
            if m_pos[2] == -1:
                bs.animate_array(
                    node=self.mc_a,
                    attr='position',
                    size=3,
                    keys={
                        0: m_pos,
                        2: (m_pos[0], m_pos[1], m_pos[2] + 2),
                        3: (m_pos[0], m_pos[1], m_pos[2] + 2),
                        5: m_pos,
                        6: m_pos,
                    },
                    loop=True,
                )
            else:
                bs.animate_array(
                    node=self.mc_a,
                    attr='position',
                    size=3,
                    keys={
                        0: m_pos,
                        2: (m_pos[0], m_pos[1], m_pos[2] - 2),
                        3: (m_pos[0], m_pos[1], m_pos[2] - 2),
                        5: m_pos,
                        6: m_pos,
                    },
                    loop=True,
                )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()


# Map By Zacker
# Map 5#
class darkzone_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 6, 0) + (0, 5, 0) + (17, 9, 5520)
    boxes['map_bounds'] = (0, 0, 0) + (0, 0, 0) + (20.0, 23, 7.25)
    points['flag_default'] = (0, 5.1, 0)
    points['flag1'] = (-6.5, 5.79, 0.4)
    points['spawn1'] = (-4.4, 5, 0)
    points['flag2'] = (6.5, 5.79, 0.4)
    points['spawn2'] = (4.4, 5, 0)
    points['ffa_spawn1'] = (3, 5.2, 0)
    points['ffa_spawn2'] = (-3, 5.2, 0)
    points['ffa_spawn3'] = (4, 5.2, 0)
    points['ffa_spawn4'] = (-4, 5.2, 0)
    points['ffa_spawn5'] = (0, 5.2, 0)
    points['powerup_spawn1'] = (-5.5, 7, 0)
    points['powerup_spawn2'] = (5.5, 7, 0)


class DarkZone(bs.Map):
    """Unknown city"""

    defs = darkzone_defs
    name = 'The Limbo'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'king_of_the_hill', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'shrapnel1Color'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'bottom_mesh': bs.getmesh('rampageLevelBottom'),
            'tex': bs.gettexture('rampageLevelColor'),
            'bgmesh1': bs.getmesh('rampageBG'),
            'bgtex1': bs.gettexture('rampageBGColor'),
            'bgtex': bs.gettexture('shrapnel1Color'),
            'bgmesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )

        self._map_mesh1 = bs.getmesh('image1x1')
        self._map_mesh2 = bs.getmesh('tnt')
        self._map_tex1 = bs.gettexture('black')
        self._map_tex2 = bs.gettexture('reflectionChar_-y')
        self._map_tex3 = bs.gettexture('bg')
        self._map_tex4 = bs.gettexture('circleOutlineNoAlpha')

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh1'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex1'],
            },
        )

        self.zone = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': (0, 5, 0),
                'color': (1, 1, 1),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [15.5, 0.05, 5.3],
            },
        )
        bs.animate_array(
            node=self.zone,
            attr='color',
            size=3,
            keys={
                0: (0, 0, 0),
                1.5: (0, 0, 0),
                2.00: (0, 0, 0),
                2.05: (1, 1, 1),
                2.1: (0, 0, 0),
                2.15: (1, 1, 1),
                2.2: (0, 0, 0),
                2.25: (1, 1, 1),
                2.3: (0, 0, 0),
                2.35: (1, 1, 1),
                2.4: (0, 0, 0),
                2.45: (0.7, 0.7, 0.7),
            },
            loop=False,
        )

        self.zone = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': (0, 3, 0),
                'color': (1, 1, 1),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [15.5, 0.05, 5.3],
            },
        )
        bs.animate_array(
            node=self.zone,
            attr='color',
            size=3,
            keys={
                0: (0, 0, 0),
                1.5: (0, 0, 0),
                2.00: (0, 0, 0),
                2.05: (1, 1, 1),
                2.1: (0, 0, 0),
                2.15: (1, 1, 1),
                2.2: (0, 0, 0),
                2.25: (1, 1, 1),
                2.3: (0, 0, 0),
                2.35: (1, 1, 1),
                2.4: (0, 0, 0),
                2.45: (0.7, 0.7, 0.7),
            },
            loop=False,
        )

        self.zone = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': (0, 1, 0),
                'color': (1, 1, 1),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [15.5, 0.05, 5.3],
            },
        )
        bs.animate_array(
            node=self.zone,
            attr='color',
            size=3,
            keys={
                0: (0, 0, 0),
                1.5: (0, 0, 0),
                2.00: (0, 0, 0),
                2.05: (1, 1, 1),
                2.1: (0, 0, 0),
                2.15: (1, 1, 1),
                2.2: (0, 0, 0),
                2.25: (1, 1, 1),
                2.3: (0, 0, 0),
                2.35: (1, 1, 1),
                2.4: (0, 0, 0),
                2.45: (0.7, 0.7, 0.7),
            },
            loop=False,
        )

        for m_pos1 in [(-5, 3, 0), (0, 3, 0), (5, 3, 0)]:
            self.mv_center = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos1,
                    'mesh': self._map_mesh2,
                    'mesh_scale': 7.23,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex3,
                    'reflection': 'soft',
                    'reflection_scale': [0.37],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        for m_pos1 in [(0, 3, 0)]:
            self.mc_center = bs.newnode(
                'region',
                attrs={
                    'position': m_pos1,
                    'scale': (15, 5, 5),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )

        for m_pos1 in [(-5, 5.4, 0), (0, 5.4, 0), (5, 5.4, 0)]:
            self.mv_center = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos1,
                    'mesh': self._map_mesh1,
                    'mesh_scale': 4.00,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex4,
                    'reflection': 'soft',
                    'reflection_scale': [0.0],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.2, 1.2)
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.5, -0.25, 0.5)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        FadeEfect(gnode.tint)
        Credits()


class arena_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 6, -7) + (0, 5, 0) + (17, 9, 5520)
    boxes['map_bounds'] = (0, 0, 0) + (0, 0, 0) + (20.0, 23, 20.25)
    points['flag_default'] = (0, 5.5, 0)

    points['spawn1'] = (-4.4, 5, 0)
    points['spawn2'] = (4.4, 5, 0)

    points['flag1'] = (-6, 6, 0)
    points['flag2'] = (6, 6, 0)
    points['flag3'] = (0, 6, 6)
    points['flag4'] = (0, 6, -6)
    points['flag5'] = (-4, 6, -4.4)
    points['flag6'] = (4, 6, -4.4)
    points['flag7'] = (-4.4, 6, 4)
    points['flag8'] = (4.4, 6, 4)

    points['spawn_by_flag1'] = (-6, 6, 0)
    points['spawn_by_flag2'] = (6, 6, 0)
    points['spawn_by_flag3'] = (0, 6, 6)
    points['spawn_by_flag4'] = (0, 6, -6)
    points['spawn_by_flag5'] = (-4, 6, -4.4)
    points['spawn_by_flag6'] = (4, 6, -4.4)
    points['spawn_by_flag7'] = (-4.4, 6, 4)
    points['spawn_by_flag8'] = (4.4, 6, 4)

    points['ffa_spawn1'] = (-6, 6, 0)
    points['ffa_spawn2'] = (6, 6, 0)
    points['ffa_spawn3'] = (0, 6, 6)
    points['ffa_spawn4'] = (0, 6, -6)
    points['ffa_spawn5'] = (-4, 6, -4.4)
    points['ffa_spawn6'] = (4, 6, -4.4)
    points['ffa_spawn7'] = (-4.4, 6, 4)
    points['ffa_spawn8'] = (4.4, 6, 4)

    points['powerup_spawn1'] = (-4.0, 7, 0)
    points['powerup_spawn2'] = (4.0, 7, 0)
    points['powerup_spawn3'] = (0, 7, -4.0)
    points['powerup_spawn4'] = (0, 7, 4.0)


class Tarena(bs.Map):
    """? ? ?"""

    defs = arena_defs
    name = 'The Arena'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return [
            'melee',
            'king_of_the_hill',
            'keep_away',
            'team_flag',
            'conquest',
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'natureBackgroundColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'bottom_mesh': bs.getmesh('rampageLevelBottom'),
            'tex': bs.gettexture('rampageLevelColor'),
            'bgmesh1': bs.getmesh('rampageBG'),
            'bgtex1': bs.gettexture('rampageBGColor'),
            'bgtex': bs.gettexture('black'),
            'bgmesh': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )

        self._map_mesh1 = bs.getmesh('image1x1')
        self._map_mesh2 = bs.getmesh('tnt')
        self._map_tex1 = bs.gettexture('black')
        self._map_tex2 = bs.gettexture('reflectionChar_-y')
        self._map_tex3 = bs.gettexture('bg')
        self._map_tex4 = bs.gettexture('circleOutlineNoAlpha')

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        for m_pos1 in [(0, 5.44, 0)]:
            self.mv_center = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos1,
                    'mesh': self._map_mesh1,
                    'mesh_scale': 17.23,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex3,
                    'reflection': 'soft',
                    'reflection_scale': [0.37],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        CollideBox(
            position=(0, 3, 0),
            scale=(24, 5, 24),
            color=(1, 0, 1),
            visible=False,
        )

        # Principal
        self.zone = bs.newnode(
            'locator',
            attrs={
                'shape': 'circleOutline',
                'position': (0, 5.46, 0),
                'color': (1, 1, 1),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [16.7],
            },
        )
        bs.animate_array(
            node=self.zone,
            attr='color',
            size=3,
            keys={
                0: (0, 0, 0),
                1.5: (0, 0, 0),
                2.00: (0, 0, 0),
                2.05: (1, 1, 1),
                2.1: (0, 0, 0),
                2.15: (1, 1, 1),
                2.2: (0, 0, 0),
                2.25: (1, 1, 1),
                2.3: (0, 0, 0),
                2.35: (1, 1, 1),
                2.4: (0, 0, 0),
                2.45: (1.1, 1.1, 1.1),
            },
            loop=False,
        )

        ###
        scale = 17.6
        for zone in range(10):
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circleOutline',
                    'position': (0, 5.46, 0),
                    'color': (0, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [scale],
                },
            )
            scale += 0.8

        # Meme
        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 21, 0),
                'text': 'Never gonna give you up\nNever gonna let you down\nNever gonna run around and desert you',
                'in_world': True,
                'shadow': 1.5,
                'flatness': 0.7,
                'color': (1, 1, 1.2),
                'opacity': 1.0,
                'scale': 0.023,
                'h_align': 'center',
            },
        )

        self._region_material = bs.Material()
        self._region_material.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                (
                    'call',
                    'at_connect',
                    bs.CallStrict(self._handle_collide, True),
                ),
                (
                    'call',
                    'at_disconnect',
                    bs.CallStrict(self._handle_collide, False),
                ),
            ),
        )

        # Flag region.
        scale = 7.25 + 0.1
        mats = [self._region_material, shared.region_material]
        self.kill_region = bs.newnode(
            'region',
            attrs={
                'position': (0, 5.5, 0),
                'scale': (scale, scale, scale),
                'type': 'sphere',
                'materials': mats,
            },
        )
        # bs.newnode('locator',
        # attrs={'shape':'circleOutline',
        # 'position':(0,5.46,0),
        # 'color':(1,1,0),
        # 'opacity':1,'draw_beauty':True,'additive':False,'size':[scale*2.4]})

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.2, 1.2)
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.5, 0.4, 0.5)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        FadeEfect(gnode.tint)
        Credits()

    def _handle_collide(self, collide: bool):
        try:
            node = bs.getcollision().opposingnode
            # bs.screenmessage('Collide: '+str(collide))
            # print(str(node.getnodetype()))
            if not collide:
                p1 = node.position
                p2 = self.kill_region.position
                diff = bs.Vec3(p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])
                dist = diff.length()
                # print(str(dist))
                if dist > 7.6:
                    node.handlemessage(bs.DieMessage())
        except:
            pass


class island_mine:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (
        (0, 10, -0) + (0.0, 0.0, 0.0) + (20, 20, 10)
    )
    boxes['map_bounds'] = (0, 3.5, -5) + (0.0, 0.0, 0.0) + (20, 15, 30)

    points['ffa_spawn1'] = (-4.5, 7, -8) + (1, 1, 1)
    points['ffa_spawn2'] = (4.5, 7, -8) + (1, 1, 1)
    points['ffa_spawn3'] = (3, 3.5, -0.5) + (3, 2, 2)
    points['ffa_spawn4'] = (-3, 3.5, -0.5) + (3, 2, 2)

    points['flag1'] = (-5, 6.5, -8)
    points['flag2'] = (5, 6.5, -8)
    points['flag3'] = (-5, 4.0, -0.5)
    points['flag4'] = (5, 4.0, -0.5)
    points['flag_default'] = (0, 4.0, -0.5)

    points['spawn1'] = (-4.5, 6, -8) + (1.0, 2, 1.5)
    points['spawn2'] = (4.5, 6, -8) + (1.0, 2, 1.5)
    points['spawn_by_flag1'] = (-4.5, 6, -8) + (1.0, 2, 1.5)
    points['spawn_by_flag2'] = (4.5, 6, -8) + (1.0, 2, 1.5)
    points['spawn_by_flag3'] = (-4, 3.5, -0.5) + (1.5, 1.5, 1.5)
    points['spawn_by_flag4'] = (4, 3.5, -0.5) + (1.5, 1.5, 1.5)

    points['powerup_spawn1'] = (-3, 4, -2.5)
    points['powerup_spawn2'] = (-2, 4, 1.5)
    points['powerup_spawn3'] = (3, 4, -2.5)
    points['powerup_spawn4'] = (2, 4, 1.5)


class IslandMine(bs.Map):
    """A simple square shaped map with a raised edge."""

    defs = island_mine

    name = 'Island Mine'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return [
            'melee',
            'keep_away',
            'team_flag',
            'king_of_the_hill',
            'conquest',
        ]

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'landMine'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('thePadLevel'),
            'bottom_mesh': bs.getmesh('thePadLevelBottom'),
            'collision_mesh': bs.getcollisionmesh('thePadLevelCollide'),
            'tex': bs.gettexture('thePadLevelColor'),
            'bgtex': bs.gettexture('menuBG'),
            'bgmesh': bs.getmesh('thePadBG'),
            'railing_collision_mesh': bs.getcollisionmesh('thePadLevelBumper'),
            'vr_fill_mound_mesh': bs.getmesh('thePadVRFillMound'),
            'vr_fill_mound_tex': bs.gettexture('vrFillMound'),
        }
        # fixme should chop this into vr/non-vr sections for efficiency
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self.ice_material = bs.Material()
        self.ice_material.add_actions(
            actions=('modify_part_collision', 'friction', 0.0)
        )
        self.plataform_material = bs.Material()
        self.plataform_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        self.r0 = bs.newnode(
            'region',
            attrs={
                'position': (0, 6, -8.0),
                'scale': [6, 0.1, 2.5 - 0.1],
                'type': 'box',
                'materials': (self.plataform_material, self.ice_material),
            },
        )

        self.r01 = bs.newnode(
            'region',
            attrs={
                'position': (0, 6.25, -8.0 - 1.25 + 0.05),
                'scale': [6, 1, 0.01],
                'type': 'box',
                'materials': (self.plataform_material, self.ice_material),
            },
        )

        self.r02 = bs.newnode(
            'region',
            attrs={
                'position': (0, 6.25, -8.0 + 1.25 - 0.05),
                'scale': [6, 1, 0.01],
                'type': 'box',
                'materials': (self.plataform_material, self.ice_material),
            },
        )

        self.mine = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (0, 6.5, -8.0),
                'velocity': (2, 0, 0),
                'color_texture': bs.gettexture('landMine'),
                'mesh': bs.getmesh('landMine'),
                #'light_mesh': bs.getmesh('powerupSimple'),
                'mesh_scale': 3.3,
                'body': 'landMine',
                'body_scale': 3.3,
                'density': 1,
                'gravity_scale': 0.2,
                'reflection': 'soft',
                'reflection_scale': [0.25],
                'shadow_size': 0.0,
                'max_speed': 1.5,
                'materials': [shared.footing_material],
            },
        )

        # print(str(dir(self.mine)))

        map_ref = weakref.ref(self)

        def move_platform(value, time):
            def _safe_setattr(attr, val):
                map_obj = map_ref()
                if map_obj is None:
                    return
                node = map_obj.mine
                if node and node.exists():
                    setattr(node, attr, val)

            def repeat_move():
                map_obj = map_ref()
                if map_obj is None:
                    return
                bs.timer(
                    0.001,
                    bs.CallStrict(
                        _safe_setattr, 'velocity', (-value / 3, 0, 0)
                    ),
                )
                bs.timer(
                    0.001,
                    bs.CallStrict(
                        _safe_setattr,
                        'extra_acceleration',
                        (-value / 1.5, 0, 0),
                    ),
                )
                bs.timer(
                    time + 0.3,
                    bs.CallStrict(
                        _safe_setattr, 'velocity', (value / 3, 0, 0)
                    ),
                )
                bs.timer(
                    time + 0.3,
                    bs.CallStrict(
                        _safe_setattr,
                        'extra_acceleration',
                        (value / 1.5, 0, 0),
                    ),
                )
                bs.timer(time * 2 + 0.3, bs.CallStrict(repeat_move))

            bs.timer(
                0.001,
                bs.CallStrict(_safe_setattr, 'velocity', (value / 3, 0, 0)),
            )
            bs.timer(
                0.001,
                bs.CallStrict(
                    _safe_setattr,
                    'extra_acceleration',
                    (value / 1.5, 0, 0),
                ),
            )
            bs.timer(time / 2, bs.CallStrict(repeat_move))

        move_platform(1, 3)

        self.r = bs.newnode(
            'region',
            attrs={
                'position': (0, 2, -0.5),
                'scale': [12, 3, 6],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (-3, 0.4, -0.5),
                'velocity': (0, 0, 0),
                'color_texture': bs.gettexture('flagColor'),
                'mesh': bs.getmesh('powerupSimple'),
                'mesh_scale': 10.6,
                'body': 'puck',
                'body_scale': 3,
                'density': 1,
                'gravity_scale': 0,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'shadow_size': 0.0,
                'materials': [self.dont_collide],
            },
        )

        bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (3, 0.4, -0.5),
                'velocity': (0, 0, 0),
                'color_texture': bs.gettexture('flagColor'),
                'mesh': bs.getmesh('powerupSimple'),
                'mesh_scale': 10.6,
                'body': 'puck',
                'body_scale': 3,
                'density': 1,
                'gravity_scale': 0,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'shadow_size': 0.0,
                'materials': [self.dont_collide],
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (4.5, 5, -5 - 4 + 1),
                'scale': [3, 3, 3],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        p = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (0, 6.5, -8.0),
                'velocity': (2, 0, 0),
                'color_texture': bs.gettexture('flagColor'),
                'mesh': bs.getmesh('powerupSimple'),
                'mesh_scale': 5.3,
                'body': 'puck',
                'body_scale': 1,
                'density': 1,
                'gravity_scale': 0.2,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'shadow_size': 0.0,
                'max_speed': 1.5,
                'materials': [self.dont_collide],
            },
        )
        self.r1.connectattr('position', p, 'position')

        self.r2 = bs.newnode(
            'region',
            attrs={
                'position': (-4.5, 5, -5 - 4 + 1),
                'scale': [3, 3, 3],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        p2 = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (0, 6.5, -8.0),
                'velocity': (2, 0, 0),
                'color_texture': bs.gettexture('flagColor'),
                'mesh': bs.getmesh('powerupSimple'),
                'mesh_scale': 5.3,
                'body': 'puck',
                'body_scale': 1,
                'density': 1,
                'gravity_scale': 0.2,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'shadow_size': 0.0,
                'max_speed': 1.5,
                'materials': [self.dont_collide],
            },
        )
        self.r2.connectattr('position', p2, 'position')

        self.r3 = bs.newnode(
            'region',
            attrs={
                'position': (-4.5, 2, -5),
                'scale': [3, 3, 3],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        p3 = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (0, 6.5, -8.0),
                'velocity': (2, 0, 0),
                'color_texture': bs.gettexture('powerupLandMines'),
                'mesh': bs.getmesh('powerupSimple'),
                'mesh_scale': 5.3,
                'body': 'puck',
                'body_scale': 1,
                'density': 1,
                'gravity_scale': 0.2,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'shadow_size': 0.0,
                'max_speed': 1.5,
                'materials': [self.dont_collide],
            },
        )
        self.r3.connectattr('position', p3, 'position')

        self.r4 = bs.newnode(
            'region',
            attrs={
                'position': (4.5, 5, -5),
                'scale': [3, 3, 3],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        p4 = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (0, 6.5, -8.0),
                'velocity': (2, 0, 0),
                'color_texture': bs.gettexture('powerupLandMines'),
                'mesh': bs.getmesh('powerupSimple'),
                'mesh_scale': 5.3,
                'body': 'puck',
                'body_scale': 1,
                'density': 1,
                'gravity_scale': 0.2,
                'reflection': 'soft',
                'reflection_scale': [0.0],
                'shadow_size': 0.0,
                'max_speed': 1.5,
                'materials': [self.dont_collide],
            },
        )
        self.r4.connectattr('position', p4, 'position')

        bs.animate_array(
            node=self.r3,
            attr='position',
            size=3,
            keys={
                0: (-5, 2, -5),
                1: (-5, 2, -5),
                4: (-5, 5, -5),
                5: (-5, 5, -5),
                8: (-5, 2, -5),
            },
            loop=True,
        )
        bs.animate_array(
            node=self.r4,
            attr='position',
            size=3,
            keys={
                0: (5, 5, -5),
                1: (5, 5, -5),
                4: (5, 2, -5),
                5: (5, 2, -5),
                8: (5, 5, -5),
            },
            loop=True,
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.1, 1.0)
        gnode.ambient_color = (1.1, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()


#################################
class spaz_defs:
    points = {}
    boxes = {}
    points['flag_default'] = (0.3, 4.2, -3)
    points['flag1'] = (-7.7, 5.7, -10) + (1.0, 0.1, 1.0)
    points['flag2'] = (8.4, 5.7, 3.5) + (1.0, 0.1, 1.0)
    points['flag3'] = (8.5, 5.7, -9.7) + (1.0, 0.1, 1.0)
    points['flag4'] = (-7.5, 5.7, 3.1) + (1.0, 0.1, 1.0)
    points['flag5'] = (0.3, 4.3, -2.9) + (1.0, 0.1, 1.0)

    points['spawn_by_flag1'] = (-7.7, 5.7, -10) + (1.0, 0.1, 1.0)
    points['spawn_by_flag2'] = (8.4, 5.7, 3.5) + (1.0, 0.1, 1.0)
    points['spawn_by_flag3'] = (8.5, 5.7, -9.7) + (1.0, 0.1, 1.0)
    points['spawn_by_flag4'] = (-7.5, 5.7, 3.1) + (1.0, 0.1, 1.0)
    points['spawn_by_flag5'] = (0.3, 4.3, -2.9) + (1.0, 0.1, 1.0)

    boxes['area_of_interest_bounds'] = (
        (0, 5, -1) + (0.0, 0.0, 0.0) + (40, 20, 25)
    )
    boxes['map_bounds'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (30, 15, 30)

    points['ffa_spawn1'] = (-5, 4.2, -3) + (0.5, 0.1, 1.5)
    points['ffa_spawn2'] = (5.2, 4.2, -3) + (0.5, 0.1, 1.5)
    points['ffa_spawn3'] = (8.40, 5.77, 2.77)
    points['ffa_spawn4'] = (8.40, 5.77, -8.04)
    points['ffa_spawn5'] = (-7.68, 5.77, -8.94)
    points['ffa_spawn6'] = (-7.68, 5.77, 2.80)

    points['spawn1'] = (-7.7, 5.7, -9) + (1.7, 0.1, 1.2)
    points['spawn2'] = (8.4, 5.7, 2.5) + (1.7, 0.1, 1.2)

    points['powerup_spawn1'] = (-3.8, 4.5, -3)
    points['powerup_spawn2'] = (4, 4.5, -3)
    points['powerup_spawn3'] = (-5.7, 6.5, -10.3)
    points['powerup_spawn4'] = (6.6, 6.5, 3.5)
    points['powerup_spawn5'] = (-9.5, 6.5, -10.3)
    points['powerup_spawn6'] = (10.5, 6.5, 3.5)

    points['powerup_spawn7'] = (-5.7, 6.5, 3.5)
    points['powerup_spawn8'] = (6.6, 6.5, -10.3)
    points['powerup_spawn9'] = (-9.5, 6.5, 3.5)
    points['powerup_spawn10'] = (10.5, 6.5, -10.3)

    points['shadow_lower_bottom'] = (0, 4.0, 2)
    points['shadow_lower_top'] = (0, 5, 2)
    points['shadow_upper_bottom'] = (0, 6, 2)
    points['shadow_upper_top'] = (0, 7, 2)


class SpazMap(bs.Map):
    defs = spaz_defs()
    name = 'Skull Temple'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'team_flag', 'keep_away', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bonesColor'

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

        self._map_tex2 = bs.gettexture('tnt')
        self._map_mesh = bs.getmesh('powerupSimple')

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self.ice_material = bs.Material()
        self.ice_material.add_actions(
            actions=(('modify_part_collision', 'friction', 0.01))
        )

        self.node = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color': (0, 1, 1),
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        ########Rampage###
        pos = (0, 4, -3)
        pos_extra = 6.5
        self.r4 = bs.newnode(
            'region',
            attrs={
                'position': (0, 3.57, -3),
                'scale': [16, 1, 4.3],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        ####
        bs.newnode(
            'region',
            attrs={
                'position': (-7.8, pos[1] + 0.95, 2.6),
                'scale': [4.75, 1.0, 3.4],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (-7.7, pos[1] + 0.95, -2.6 * 3.5),
                'scale': [4.75, 1.0, 3.4],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (-7.725, pos[1] + 0.95, -3.2),
                'scale': [1.35, 1.0, 8.2],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        ####
        bs.newnode(
            'region',
            attrs={
                'position': (7.8 + 0.8, pos[1] + 0.95, 2.6),
                'scale': [4.75, 1.0, 3.4],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (7.7 + 0.8, pos[1] + 0.95, -2.6 * 3.5),
                'scale': [4.75, 1.0, 3.4],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (7.725 + 0.8, pos[1] + 0.95, -3.2),
                'scale': [1.35, 1.0, 8.2],
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        ####
        for x in [-6.5, 7.3]:
            m_pos = (x, pos[1] + 0.3, -3.5)
            bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (1.0, 1.0, 1.0),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 1.635,
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'damping': 0,
                    'color_texture': self._map_tex2,
                    'reflection': 'soft',
                    'reflection_scale': [0.0],
                    'is_area_of_interest': False,
                    'materials': [self.dont_collide],
                },
            )
            m_pos = (x, pos[1] + 0.3, -2.5)
            bs.newnode(
                'region',
                attrs={
                    'position': m_pos,
                    'scale': (1.0, 1.0, 1.0),
                    'type': 'box',
                    'materials': (
                        self._collide_with_player,
                        shared.footing_material,
                    ),
                },
            )
            bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 1.635,
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'damping': 0,
                    'color_texture': self._map_tex2,
                    'reflection': 'soft',
                    'reflection_scale': [0.0],
                    'is_area_of_interest': False,
                    'materials': [self.dont_collide],
                },
            )

        ####################################
        # Rampage
        a = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (0.4, 2, 0.5),
                'highlight': (0.4, 2, 0.5),
                'color_texture': bs.gettexture('rampageLevelColor'),
                'color_mask_texture': bs.gettexture('bonesColorMask'),
                'head_mesh': bs.getmesh('rampageLevel'),
                'style': 'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            },
        )
        a.is_area_of_interest = False
        #
        b = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (1, 1, 1),
                'highlight': (1, 1, 1),
                'color_texture': bs.gettexture('rampageLevelColor'),
                'color_mask_texture': bs.gettexture('bonesColorMask'),
                'head_mesh': bs.getmesh('rampageLevelBottom'),
                'style': 'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            },
        )
        b.is_area_of_interest = False
        ###Bridgit
        c = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (0, 2, 3),
                'highlight': (0, 2, 3),
                'color_texture': bs.gettexture('bridgitLevelColor'),
                'color_mask_texture': bs.gettexture('bonesColorMask'),
                'head_mesh': bs.getmesh('bridgitLevelTop'),
                'style': 'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            },
        )
        c.is_area_of_interest = False
        d = bs.newnode(
            type='spaz',
            delegate=self,
            attrs={
                'color': (0, 2, 3),
                'highlight': (0, 2, 3),
                'color_texture': bs.gettexture('bridgitLevelColor'),
                'color_mask_texture': bs.gettexture('bonesColorMask'),
                'head_mesh': bs.getmesh('bridgitLevelTop'),
                'style': 'bones',
                'materials': [self.dont_collide],
                'roller_materials': [self.dont_collide],
                'extras_material': [self.dont_collide],
                'punch_materials': [self.dont_collide],
                'pickup_materials': [self.dont_collide],
            },
        )
        d.is_area_of_interest = False

        def p():
            if a:
                a.handlemessage(
                    'stand', pos[0], pos[1] - pos_extra, pos[2] + 4.25, 0
                )
                a.handlemessage('knockout', 500.0)
            if b:
                b.handlemessage(
                    'stand', pos[0], pos[1] - pos_extra, pos[2] + 4.25, 0
                )
                b.handlemessage('knockout', 500.0)
            if c:
                c.handlemessage(
                    'stand',
                    pos[0] - 6.2,
                    pos[1] - pos_extra + 2.7,
                    pos[2] + 4.25 - 4.8,
                    90,
                )
                c.handlemessage('knockout', 500.0)
            if d:
                d.handlemessage(
                    'stand',
                    pos[0] + 7,
                    pos[1] - pos_extra + 2.75,
                    pos[2] + 4.25 - 3.7 - 0.5,
                    -90,
                )
                d.handlemessage('knockout', 500.0)

        bs.timer(0.001, p, repeat=True)
        # print(str(dir(a)))
        # Meme
        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 21, 0),
                'text': 'GOATSTIAN GOATSTIAN GOATSTIAN\nGOATSTIAN GOATSTIAN GOATSTIAN ',
                'in_world': True,
                'shadow': 1.5,
                'flatness': 0.7,
                'color': (1, 1, 1.2),
                'opacity': 1.0,
                'scale': 0.023,
                'h_align': 'center',
            },
        )
        CustomModel(
            position=(0.4, 1.5, -1.4),
            mesh='bonesHead',
            texture='bonesColor',
            scale=6.7,
        )

        ####################################
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
        FadeEfect(gnode.tint)
        Credits()


# Rombo
class ram_defs:
    points = {}
    boxes = {}
    points['flag_default'] = (0.0, 4.2, -5)
    points['flag1'] = (4.5, 4.2, -4) + (0.5, 0.1, 1.5)
    points['flag2'] = (-4.5, 4.2, -4) + (0.5, 0.1, 1.5)

    boxes['area_of_interest_bounds'] = (
        (0, 5, -1) + (0.0, 0.0, 0.0) + (40, 20, 25)
    )
    boxes['map_bounds'] = (0, 4, 0) + (0.0, 0.0, 0.0) + (30, 15, 30)

    points['ffa_spawn1'] = (-4, 4.2, -5) + (0.5, 0.1, 1.5)
    points['ffa_spawn2'] = (4.2, 4.2, -5) + (0.5, 0.1, 1.5)
    points['ffa_spawn3'] = (0, 4.2, -10) + (0.5, 0.1, 1.5)
    points['ffa_spawn4'] = (0, 4.2, 1) + (0.5, 0.1, 1.5)

    points['spawn1'] = (4.2, 4.2, -4) + (0.5, 0.1, 1.5)
    points['spawn2'] = (-4, 4.2, -4) + (0.5, 0.1, 1.5)

    points['powerup_spawn1'] = (3, 4.5, -5)
    points['powerup_spawn2'] = (-3, 4.5, -5)

    points['shadow_lower_bottom'] = (0, 4.0, 2)
    points['shadow_lower_top'] = (0, 5, 2)
    points['shadow_upper_bottom'] = (0, 6, 2)
    points['shadow_upper_top'] = (0, 7, 2)


###################
class RampageMod(bs.Map):
    """Wee little map with ramps on the sides."""

    defs = ram_defs()
    name = 'Botton Rampage'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'rampageLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('rampageLevel'),
            'bottom_mesh': bs.getmesh('rampageLevelBottom'),
            'collision_mesh': bs.getcollisionmesh('rampageLevelCollide'),
            'tex': bs.gettexture('rampageLevelColor'),
            'bgtex': bs.gettexture('shrapnel1Color'),
            'bgtex2': bs.gettexture('shrapnel1Color'),
            'bgmesh': bs.getmesh('rampageBG'),
            'bgmesh2': bs.getmesh('rampageBG2'),
            'vr_fill_mesh': bs.getmesh('rampageVRFill'),
            'railing_collision_mesh': bs.getcollisionmesh('rampageBumper'),
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 0, 2))
        shared = SharedObjects.get()
        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )

        # self.node = bs.newnode(
        # 'terrain',
        # delegate=self,
        # attrs={
        # 'collision_mesh': self.preloaddata['collision_mesh'],
        # 'mesh': self.preloaddata['mesh'],
        # 'color_texture': self.preloaddata['tex'],
        # 'materials': [shared.footing_material]
        # })

        # self.bottom = bs.newnode('terrain',
        # attrs={
        # 'mesh': self.preloaddata['bottom_mesh'],
        # 'lighting': False,
        # 'color_texture': self.preloaddata['tex']
        # })
        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh2'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )
        # self.railing = bs.newnode(
        # 'terrain',
        # attrs={
        # 'collision_mesh': self.preloaddata['railing_collision_mesh'],
        # 'materials': [shared.railing_material],
        # 'bumper': True
        # })

        bs.newnode(
            'region',
            attrs={
                'position': (0, 3, -4.5),
                'scale': (2.7, 2, 16.7),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (2.0, 3, -4.6),
                'scale': (1.3, 2, 12.9),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (-2.0, 3, -4.6),
                'scale': (1.3, 2, 12.9),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (3.3, 3, -4.5),
                'scale': (1.3, 2, 9.5),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (-3.3, 3, -4.5),
                'scale': (1.3, 2, 9.5),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (4.7, 3, -4.4),
                'scale': (1.3, 2, 6.4),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (-4.7, 3, -4.8),
                'scale': (1.3, 2, 6.3),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (6.2, 3, -4.5),
                'scale': (1.3, 2, 3.2),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        bs.newnode(
            'region',
            attrs={
                'position': (-6.2, 3, -4.7),
                'scale': (1.3, 2, 3.2),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.zone = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': (0, 3.93, -4.65),
                'color': (1, 1, 1),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [14, 0.1, 2.9],
            },
        )
        bs.animate_array(
            node=self.zone,
            attr='color',
            size=3,
            keys={
                0: (0, 0, 0),
                0.0: (0, 0, 0),
                0.50: (0, 0, 0),
                0.55: (1, 1, 1),
                0.6: (0, 0, 0),
                0.65: (1, 1, 1),
                0.7: (0, 0, 0),
                0.75: (1, 1, 1),
                0.8: (0, 0, 0),
                0.85: (1, 1, 1),
                0.9: (0, 0, 0),
                0.95: (1.2, 0.0, 0.0),
            },
            loop=False,
        )

        # r.connectattr('position',l,'position')
        # r.connectattr('scale',l,'size')

        CustomModelR3(
            position=(4.95, 6, -4.3),
            mesh='rampageLevelBottom',
            texture='rampageLevelColor',
            rotate='right',
        )
        CustomModelR3(
            position=(-4.95, 6, -5),
            mesh='rampageLevelBottom',
            texture='rampageLevelColor',
            rotate='left',
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.2, 1.2)
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.3, -0.1, 0.5)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        FadeEfect(gnode.tint)
        Credits()

    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        box_position = self.defs.boxes['edge_box'][0:3]
        box_scale = self.defs.boxes['edge_box'][6:9]
        xpos = (point.x - box_position[0]) / box_scale[0]
        zpos = (point.z - box_position[2]) / box_scale[2]
        return xpos < -0.5 or xpos > 0.5 or zpos < -0.5 or zpos > 0.5


#########################TESTTTTTT###
class collosal_bridgit:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (
        (
            -0.2457963347 * 2.5 + 1,
            3.828181068 * 2.5 - 28,
            -1.528362695 * 2.5 - 25,
        )
        + (0.0, 0.0, 0.0)
        + (19.14849937 * 2.0, 7.312788846 * 1.25, 8.436232726 * 1.25)
    )
    points['ffa_spawn1'] = (
        -5.869295124 * 2.5 + 1,
        3.715437928 * 2.5 - 46,
        -1.617274877 * 2.5 - 50,
    ) + (0.9410329222 * 2.5, 1.0, 1.818908238 * 2.5)
    points['ffa_spawn2'] = (
        5.160809653 * 2.5 + 1,
        3.761793434 * 2.5 - 46,
        -1.443012115 * 2.5 - 50,
    ) + (0.7729807005 * 2.5, 1.0, 1.818908238 * 2.5)
    points['ffa_spawn3'] = (
        -0.4266381164 * 2.5 + 1,
        3.761793434 * 2.5 - 46,
        -1.555562653 * 2.5 - 50,
    ) + (4.034151421 * 2.5, 1.0, 0.2731725824 * 2.5)
    points['flag1'] = (
        -7.354603923 * 2.5 + 1,
        3.770769731 * 2.5 - 46,
        -1.617274877 * 2.5 - 50,
    )
    points['flag2'] = (
        6.885846926 * 2.5 + 1,
        3.770685211 * 2.5 - 46,
        -1.443012115 * 2.5 - 50,
    )
    points['flag_default'] = (
        -0.2227795102 * 2.5 + 1,
        3.802429326 * 2.5 - 46,
        -1.562586233 * 2.5 - 50,
    )
    boxes['map_bounds'] = (
        (
            -0.1916036665 * 2.5 + 1,
            7.481446847 * 2.5 - 46,
            -1.311948055 * 2.5 - 50,
        )
        + (0.0, 0.0, 0.0)
        + (27.41996888 * 2.5, 18.47258973 * 2.5, 19.52220249 * 2.5)
    )
    points['powerup_spawn1'] = (
        6.82849491 * 2.5 + 1,
        4.658454461 * 2.5 - 46,
        0.1938139802 * 2.5 - 50,
    )
    points['powerup_spawn2'] = (
        -7.253381358 * 2.5 + 1,
        4.728692078 * 2.5 - 46,
        0.252121017 * 2.5 - 50,
    )
    points['powerup_spawn3'] = (
        6.82849491 * 2.5 + 1,
        4.658454461 * 2.5 - 46,
        -3.461765427 * 2.5 - 50,
    )
    points['powerup_spawn4'] = (
        -7.253381358 * 2.5 + 1,
        4.728692078 * 2.5 - 46,
        -3.40345839 * 2.5 - 50,
    )
    points['shadow_lower_bottom'] = (-0.2227795102, 2.83188898, 2.680075641)
    points['shadow_lower_top'] = (-0.2227795102, 3.498267184, 2.680075641)
    points['shadow_upper_bottom'] = (-0.2227795102, 6.305086402, 2.680075641)
    points['shadow_upper_top'] = (-0.2227795102, 9.470923628, 2.680075641)
    points['spawn1'] = (
        -5.869295124 * 2.5 + 1,
        3.715437928 * 2.5 - 46,
        -1.617274877 * 2.5 - 50,
    ) + (0.9410329222 * 2.5, 1.0, 1.818908238 * 2.5)
    points['spawn2'] = (
        5.160809653 * 2.5 + 1,
        3.761793434 * 2.5 - 46,
        -1.443012115 * 2.5 - 50,
    ) + (0.7729807005 * 2.5, 1.0, 1.818908238 * 2.5)


class BridgitC(bs.Map):
    """Map with a narrow bridge in the middle."""

    defs = collosal_bridgit()

    name = 'Collosal Bridgit'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        # print('getting playtypes', cls._getdata()['play_types'])
        return ['melee', 'team_flag', 'keep_away']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bridgitLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh_top': bs.getmesh('bridgitLevelTop'),
            'mesh_bottom': bs.getmesh('bridgitLevelBottom'),
            'mesh_bg': bs.getmesh('natureBackground'),
            'bg_vr_fill_mesh': bs.getmesh('natureBackgroundVRFill'),
            'collision_mesh': bs.getcollisionmesh('bridgitLevelCollide'),
            'tex': bs.gettexture('bridgitLevelColor'),
            'mesh_bg_tex': bs.gettexture('natureBackgroundColor'),
            'collide_bg': bs.getcollisionmesh('natureBackgroundCollide'),
            'railing_collision_mesh': (
                bs.getcollisionmesh('bridgitLevelRailingCollide')
            ),
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )

        m = 10
        CustomModel(
            position=(0 + 1, -4.6 * m - 0.2, -5 * m),
            mesh='bridgitLevelTop',
            texture='bridgitLevelColor',
            scale=1.0 * 2.5,
        )
        CustomModel(
            position=(0 + 1, -4.6 * m - 0.2, -5 * m),
            mesh='bridgitLevelBottom',
            texture='bridgitLevelColor',
            scale=1.0 * 2.5,
        )

        CustomModel(
            position=(0, -4.6 * m - 0.2, -5 * m),
            mesh='natureBackground',
            texture='natureBackgroundColor',
            scale=1.0 * 2.5,
        )

        ###NEW###
        pos = ((0.35 - 0.75) * 2.5 + 1, 3.1 * 2.5 - 46, -1.5 * 2.5 - 50)
        bs.newnode(
            'region',
            attrs={
                'position': pos,
                'scale': (8.25 * 2.5, 1.2 * 2.5, 1.37 * 2.5),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        # l = bs.newnode('locator',attrs={'shape':'box','position':pos,
        # 'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':[8.25*2.5,1.2*2.5,1.37*2.5]})

        pos = (-6.15 * 2.5 + 1, 2.7 * 2.5 - 46, -1.6 * 2.5 - 50)
        bs.newnode(
            'region',
            attrs={
                'position': pos,
                'scale': (3.4 * 2.5, 2 * 2.5, 4.75 * 2.5),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        # l = bs.newnode('locator',attrs={'shape':'box','position':pos,
        # 'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':[3.4*2.5,2*2.5,4.75*2.5]})

        pos = (5.5 * 2.5 + 1, 2.7 * 2.5 - 46, -1.5 * 2.5 - 50)
        bs.newnode(
            'region',
            attrs={
                'position': pos,
                'scale': (3.5 * 2.5, 2 * 2.5, 5 * 2.5),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        # l = bs.newnode('locator',attrs={'shape':'box','position':pos,
        # 'color':(1,1,1),'opacity':1, 'drawShadow':False,'draw_beauty':True,'additive':False,'size':[3.5*2.5,2*2.5,5*2.5]})

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)
        FadeEfect(gnode.tint)
        Credits()


#########################TESTTTTTT###
class tcrus:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (
        (0.35, 5.61, -2.06) + (0.0, 0.0, 0.0) + (19.90, 10.34, 8.16)
    )
    # boxes['area_of_interest_bounds'] = (0, 10, -14) + (0.0, 0.0, 0.0) + (40, 20, 25)
    boxes['edge_box'] = (
        (0.3544110667, 5.438284793, -4.100357672)
        + (0.0, 0.0, 0.0)
        + (12.57718032, 4.645176013, 3.605557343)
    )
    points['ffa_spawn1'] = (0.50, 5.05, -5.79) + (6.62, 1.0, 0.34)
    points['ffa_spawn2'] = (0.50, 5.05, -2.43) + (6.62, 1.0, 0.34)
    points['ffa_spawn3'] = (0.20, 5.49, 1.51)
    points['ffa_spawn4'] = (0.20, 5.49, -9.51)
    points['ffa_spawn5'] = (4.80, 5.49, -9.56)
    points['ffa_spawn6'] = (-4.50, 5.49, 1.25)
    points['ffa_spawn7'] = (3.50, 5.49, 1.25)

    points['flag1'] = (-5.885814199, 5.112162255, -4.251754911)
    points['flag2'] = (6.700855451, 5.10270501, -4.259912982)
    points['flag3'] = (-4.2, 5.49, -10.41)
    points['flag4'] = (4.92, 5.49, -9.76)
    points['flag5'] = (4.76, 5.49, 1.44)
    points['flag6'] = (-4.44, 5.49, 1.68)
    points['flag_default'] = (0.3196701116, 5.49, -4.292515158)

    points['spawn_by_flag1'] = (-5.885814199, 5.112162255, -4.251754911)
    points['spawn_by_flag2'] = (6.700855451, 5.10270501, -4.259912982)
    points['spawn_by_flag3'] = (-4.2, 5.49, -10.41)
    points['spawn_by_flag4'] = (4.92, 5.49, -9.76)
    points['spawn_by_flag5'] = (4.76, 5.49, 1.44)
    points['spawn_by_flag6'] = (-4.44, 5.49, 1.68)

    boxes['map_bounds'] = (
        (0.45, 4.89, -0.54) + (0.0, 0.0, 0.0) + (23.54, 14.19, 23.08)
    )

    points['powerup_spawn1'] = (-2.64, 6.42, -4.22)
    points['powerup_spawn2'] = (3.54, 6.54, -4.19)
    points['powerup_spawn3'] = (-2.03, 5.49, -10.15)
    points['powerup_spawn4'] = (2.39, 5.49, -10.1)
    points['powerup_spawn5'] = (2.39, 5.49, 1.6)
    points['powerup_spawn6'] = (-1.94, 5.54, 1.70)

    points['shadow_lower_bottom'] = (5.580073911, 3.136491026, 5.341226521)
    points['shadow_lower_top'] = (5.580073911, 4.321758709, 5.341226521)
    points['shadow_upper_bottom'] = (5.274539479, 8.425373402, 5.341226521)
    points['shadow_upper_top'] = (5.274539479, 11.93458162, 5.341226521)
    points['spawn1'] = (-4.75, 5.05, -4.24) + (0.91, 1.0, 0.51)
    points['spawn2'] = (5.83, 5.05, -4.25) + (0.91, 1.0, 0.51)


#  points['spawn2'] = (5.83, 5.05,-4.25)


class thec(bs.Map):
    """Wee little map with ramps on the sides."""

    defs = tcrus()
    name = 'The Crusade'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'crossOut'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('rampageLevel'),
            'bottom_mesh': bs.getmesh('rampageLevelBottom'),
            'collision_mesh': bs.getcollisionmesh('rampageLevelCollide'),
            'tex': bs.gettexture('rampageLevelColor'),
            'bgtex': bs.gettexture('shrapnel1Color'),
            'bgtex2': bs.gettexture('shrapnel1Color'),
            'bgmesh': bs.getmesh('rampageBG'),
            'bgmesh2': bs.getmesh('rampageBG2'),
            'vr_fill_mesh': bs.getmesh('rampageVRFill'),
            'railing_collision_mesh': bs.getcollisionmesh('rampageBumper'),
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 0, 2))
        shared = SharedObjects.get()

        self._collide_custom = bs.Material()
        self.dont_collide = bs.Material()

        self._collide_custom.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self._collide_custom.add_actions(
            conditions=('they_have_material', self.dont_collide),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )

        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['meshes'],
                'color_texture': self.preloaddata['tex'],
                'color': (0.9, 0.4, 1),
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bottom_mesh'],
                'lighting': False,
                'color': (0, 1.2, 0),
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh2'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0, 0, 1),
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )

        # iz
        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-4.35, 4.6, -4.3),
                'scale': (1.47, 1.2, 8.7),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        # centro
        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (0.25, 4.6, -4.3),
                'scale': (1.47, 1.2, 8.7),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        # der
        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (4.65, 4.6, -4.3),
                'scale': (1.47, 1.2, 8.7),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (0.25, 4.6, -10.2),
                'scale': (14.0, 1.2, 3.4),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (0.25, 4.6, 1.5),
                'scale': (14.0, 1.2, 3.6),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        CustomModelR2(
            position=(-5.80, 1.6, -4.1),
            mesh='bridgitLevelTop',
            texture='bridgitLevelColor',
            scale=1,
            rotate='left',
        )
        CustomModelR2(
            position=(-1.25, 1.58, -4.1),
            mesh='bridgitLevelTop',
            texture='bridgitLevelColor',
            scale=1,
            rotate='left',
        )
        CustomModelR2(
            position=(3.20, 1.6, -4.1),
            mesh='bridgitLevelTop',
            texture='bridgitLevelColor',
            scale=1,
            rotate='left',
        )
        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 21, 0),
                'text': 'Tz: Se me paso por la mente crear esto\n por mas raro que haya sido \n el resultado jaja',
                'in_world': True,
                'shadow': 1.5,
                'flatness': 0.7,
                'color': (1, 1, 1.2),
                'opacity': 1.0,
                'scale': 0.023,
                'h_align': 'center',
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.2, 1.2)
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.4, -0.4, 0.4)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        FadeEfect(gnode.tint)
        Credits()


class collosal_monkey:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (
        (
            -0.2457963347 * 2.5 + 1,
            1.028181068 * 2.5 - 28,
            -4.98362695 * 2.5 - 25,
        )
        + (0.0, 0.0, 0.0)
        + (19.14849937 * 2.0, 0.312788846 * 1.25, 8.436232726 * 1.25)
    )
    boxes['map_bounds'] = (
        (
            -0.1916036665 * 2.5 + 1,
            7.481446847 * 2.5 - 46,
            -1.311948055 * 2.5 - 50,
        )
        + (0.0, 0.0, 0.0)
        + (27.41996888 * 2.5, 18.47258973 * 2.5, 19.52220249 * 2.5)
    )
    points['ffa_spawn1'] = (-3.40, -37.65, -55.85)
    points['ffa_spawn2'] = (-3.40, -37.65, -64.85)
    points['ffa_spawn3'] = (12.20, -37.65, -57.05)
    points['ffa_spawn4'] = (-18.56, -37.65, -56.72)
    points['ffa_spawn5'] = (-11.66, -37.65, -44.24)
    points['ffa_spawn6'] = (5.66, -37.65, -44.24)
    points['ffa_spawn7'] = (7.66, -37.65, -66.54)
    points['ffa_spawn8'] = (-14.66, -37.65, -66.54)
    points['spawn1'] = (
        -8.026373566 * 2.5 + 1,
        3.349937889 * 2.5 - 46,
        -2.542088202 * 2.5 - 50,
    ) + (0.9450583628 * 2.5, 0.9450583628, 1.181509268 * 2.5)
    points['spawn2'] = (
        4.73470012 * 2.5 + 1,
        3.308679998 * 2.5 - 46,
        -2.757871588 * 2.5 - 50,
    ) + (0.9335931003 * 2.5, 1.0, 1.217352295 * 2.5)

    points['flag1'] = (
        -8.968414135 * 2.5 + 1,
        3.35709348 * 2.5 - 46,
        -2.804123917 * 2.5 - 50,
    )
    points['flag2'] = (
        5.945128279 * 2.5 + 1,
        3.354825248 * 2.5 - 46,
        -2.663635497 * 2.5 - 50,
    )
    points['flag3'] = (
        -1.688166134 * 2.5 + 1,
        3.392387172 * 2.5 - 46,
        -2.238613943 * 2.5 - 50,
    )
    points['flag4'] = (-11.86, 3.392387172 * 2.5 - 46, -49.41)
    points['flag5'] = (5.4, 3.392387172 * 2.5 - 46, -49.47)
    points['flag6'] = (-3.2, 3.392387172 * 2.5 - 46, -65.52)

    points['spawn_by_flag1'] = (
        -8.968414135 * 2.5 + 1,
        3.35709348 * 2.5 - 46,
        -2.804123917 * 2.5 - 50,
    )
    points['spawn_by_flag2'] = (
        5.945128279 * 2.5 + 1,
        3.354825248 * 2.5 - 46,
        -2.663635497 * 2.5 - 50,
    )
    points['spawn_by_flag3'] = (
        -1.688166134 * 2.5 + 1,
        3.392387172 * 2.5 - 46,
        -2.238613943 * 2.5 - 50,
    )
    points['spawn_by_flag4'] = (-11.86, 3.392387172 * 2.5 - 46, -49.41)
    points['spawn_by_flag5'] = (5.4, 3.392387172 * 2.5 - 46, -49.47)
    points['spawn_by_flag6'] = (-3.2, 3.392387172 * 2.5 - 46, -65.52)

    points['flag_default'] = (
        -1.688166134 * 2.5 + 1,
        3.392387172 * 2.5 - 46,
        -2.238613943 * 2.5 - 50,
    )

    points['powerup_spawn1'] = (-18.50, -37.55, -58.50)
    points['powerup_spawn2'] = (-16.50, -37.55, -66.40)
    points['powerup_spawn3'] = (9.3, -37.55, -66.50)
    points['powerup_spawn4'] = (13.0, -37.55, -59.22)
    points['powerup_spawn5'] = (5.0, -37.55, -43.32)
    points['powerup_spawn6'] = (-12.0, -37.55, -43.22)

    points['shadow_lower_bottom'] = (-0.2227795102, 2.83188898, 2.680075641)
    points['shadow_lower_top'] = (-0.2227795102, 3.498267184, 2.680075641)
    points['shadow_upper_bottom'] = (-0.2227795102, 6.305086402, 2.680075641)
    points['shadow_upper_top'] = (-0.2227795102, 9.470923628, 2.680075641)


class collosal_monkey(bs.Map):
    """Map with a narrow bridge in the middle."""

    defs = collosal_monkey()

    name = 'Collosal Monkey'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        # print('getting playtypes', cls._getdata()['play_types'])
        return ['melee', 'team_flag', 'keep_away', 'conquest']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'monkeyFaceLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'el_flipante_mono_que_es_el_mapa_de_cara_de_mono_pero_mas_grande': bs.getmesh(
                'monkeyFaceLevel'
            ),
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )

        m = 10
        CustomModel(
            position=(0 + 1, -4.6 * m - 0.2, -5 * m),
            mesh='monkeyFaceLevel',
            texture='monkeyFaceLevelColor',
            scale=1.0 * 2.5,
        )
        CustomModel(
            position=(0 + 1, -4.6 * m - 0.2, -5 * m),
            mesh='monkeyFaceLevelBottom',
            texture='monkeyFaceLevelColor',
            scale=1.0 * 2.5,
        )

        CustomModel(
            position=(0, -4.6 * m - 0.2, -5 * m),
            mesh='natureBackground',
            texture='natureBackgroundColor',
            scale=1.0 * 2.5,
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-18.10, -39.9, -56.37),
                'scale': (9.00, 3.90, 8.10),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (11.8, -39.9, -57.00),
                'scale': (9.75, 3.90, 7.85),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-3.0, -39.9, -55.30),
                'scale': (21.55, 3.90, 4.4),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-3.39, -39.9, -60.30),
                'scale': (6.2, 3.90, 15.37),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-3.39, -39.9, -66.35),
                'scale': (27.25, 3.90, 3.085),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-3.39, -39.9, -44.0),
                'scale': (21.0, 3.90, 4.2),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (5.39, -39.9, -50.30),
                'scale': (3.3, 3.90, 9.37),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-11.93, -39.9, -50.30),
                'scale': (3.5, 3.90, 9.6),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-15.39, -39.9, -60.30),
                'scale': (3.5, 3.90, 9.4),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (8.6, -39.9, -60.30),
                'scale': (3.44, 3.90, 9.4),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )
        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 21, 0),
                'text': 'El Gran mono',
                'in_world': True,
                'shadow': 1.5,
                'flatness': 0.7,
                'color': (1, 1, 1.2),
                'opacity': 1.0,
                'scale': 0.023,
                'h_align': 'center',
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)
        FadeEfect(gnode.tint)
        Credits()


# Tower Zoe by Zacker con ayudita de sebastian :v
# Tower Zoe by Zacker con ayudita de sebastian :v
class bazinga_defs:
    points = {}
    boxes = {}
    points['flag_default'] = (0.52, 7.93, -4.09)
    points['flag1'] = (8.2, 7.93, -2.53)
    points['flag2'] = (-7.5, 7.93, -6)

    boxes['area_of_interest_bounds'] = (
        (0, 10, -14) + (0.0, 0.0, 0.0) + (40, 20, 25)
    )
    boxes['map_bounds'] = (0, 12.5 - 5, 0) + (0.0, 0.0, 0.0) + (30, 15, 30)

    points['ffa_spawn1'] = (-7.2, 7.93, -6)
    points['ffa_spawn2'] = (8.2, 7.93, -2.53)
    points['ffa_spawn3'] = (1.54, 7.93, -2.48)
    points['ffa_spawn4'] = (-0.24, 7.93, -5.77)

    points['spawn1'] = (8.2, 7.93, -2.53)
    points['spawn2'] = (-7.2, 7.93, -6)

    points['powerup_spawn1'] = (8.99, 7.97, -3.10)
    points['powerup_spawn2'] = (0.16, 7.94, -1.79)
    points['powerup_spawn3'] = (1.2, 7.94, -6.79)
    points['powerup_spawn4'] = (-8.4, 8.07, -3.10)

    points['shadow_lower_bottom'] = (0, 4.0, 2)
    points['shadow_lower_top'] = (0, 5, 2)
    points['shadow_upper_bottom'] = (0, 6, 2)
    points['shadow_upper_top'] = (0, 7, 2)


class tZoe(bs.Map):
    """Wide stepped map good for CTF or Assault."""

    defs = bazinga_defs()
    name = 'Tower Zoe'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'zoeIcon'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('stepRightUpLevel'),
            'mesh_bottom': bs.getmesh('stepRightUpLevelBottom'),
            'collision_mesh': bs.getcollisionmesh('stepRightUpLevelCollide'),
            'tex': bs.gettexture('stepRightUpLevelColor'),
            'bgtex': bs.gettexture('shrapnel1Color'),
            'bgmesh': bs.getmesh('thePadBG'),
            'vr_fill_mound_mesh': bs.getmesh('stepRightUpVRFillMound'),
            'vr_fill_mound_tex': bs.gettexture('vrFillMound'),
        }
        # fixme should chop this into vr/non-vr chunks
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -1, 2))
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['meshes'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )

        self._collide_custom = bs.Material()
        self.dont_collide = bs.Material()
        self._death = bs.Material()

        self._death.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
            ),
        )

        self._collide_custom.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self._collide_custom.add_actions(
            conditions=('they_have_material', self.dont_collide),
            actions=(('modify_part_collision', 'collide', True)),
        )

        self._collide_with_player = bs.Material()
        self._collide_with_player.add_actions(
            conditions=('we_are_older_than', 1),
            actions=(('modify_part_collision', 'collide', True)),
        )
        self.dont_collide = bs.Material()
        self.dont_collide.add_actions(
            conditions=('they_are_different_node_than_us',),
            actions=(('modify_part_collision', 'collide', False)),
        )

        self._map_mesh = bs.getmesh('image1x1')
        self._map_tex = bs.gettexture('powerupIceBombs')
        self._map_tex2 = bs.gettexture('shrapnel1Color')

        self.node_bottom = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mound_mesh'],
                'lighting': False,
                'vr_only': True,
                'color': (0.53, 0.57, 0.5),
                'background': True,
                'color_texture': self.preloaddata['vr_fill_mound_tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        # death region
        bs.newnode(
            'region',
            attrs={
                'position': (0, 6.5, -5),
                'scale': (30, 0.1, 30),
                'type': 'box',
                'materials': (shared.death_material, self._death),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (0.5, 7.18, -4.3),
                'scale': (2.3, 0.9, 6.3),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (8.07, 7.18, -2.58),
                'scale': (2.27, 0.90, 3.27),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-7.07, 7.18, -6),
                'scale': (2.27, 0.90, 3.10),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (-3.4, 7.18, -5.86),
                'scale': (6.0, 0.90, 1),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        self.r1 = bs.newnode(
            'region',
            attrs={
                'position': (4.4, 7.18, -2.59),
                'scale': (6.0, 0.90, 1),
                'type': 'box',
                'materials': (
                    self._collide_with_player,
                    shared.footing_material,
                ),
            },
        )

        posS = [(0.0, 6.5, -7)]
        for m_pos in posS:
            self.mv_center = bs.newnode(
                'prop',
                attrs={
                    'body': 'puck',
                    'position': m_pos,
                    'mesh': self._map_mesh,
                    'mesh_scale': 120,
                    'body_scale': 0.1,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'color_texture': self._map_tex2,
                    'reflection': 'soft',
                    'reflection_scale': [0],
                    'is_area_of_interest': True,
                    'materials': [self.dont_collide],
                },
            )

        CustomModel(
            position=(-3.1, 5.135, -4.9),
            mesh='bridgitLevelTop',
            texture='bridgitLevelColor',
            scale=0.65,
        )
        CustomModel(
            position=(4.5, 5.135, -1.6),
            mesh='bridgitLevelTop',
            texture='bridgitLevelColor',
            scale=0.65,
        )
        CustomModel(
            position=(2.4, 2.12, -6.6),
            mesh='zigZagLevelBottom',
            texture='zigZagLevelColor',
            scale=0.8,
        )
        CustomModel(
            position=(2.4, 2.2, -6.6),
            mesh='zigZagLevel',
            texture='zigZagLevelColor',
            scale=0.8,
        )
        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 21, 0),
                'text': ':Bear_wave: :Bear_wave: :Bear_wave:',
                'in_world': True,
                'shadow': 1.5,
                'flatness': 0.7,
                'color': (1, 1, 1.2),
                'opacity': 1.0,
                'scale': 0.023,
                'h_align': 'center',
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.1, 1.0)
        gnode.ambient_color = (1.2, 1.1, 1.0)
        gnode.vignette_outer = (0.7, 0.65, 0.75)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        FadeEfect(gnode.tint)
        Credits()


class Thoughts_d:
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (
        (-1.045859963, 12.67722855, -5.401537075)
        + (0.0, 0.0, 0.0)
        + (34.46156851, 20.94044653, 0.6931564611)
    )
    boxes['map_bounds'] = (
        (-0.8748348681, 10.212941713, -5.729538885)
        + (0.0, 0.0, 0.0)
        + (36.09666006, 21.19950145, 7.89541168)
    )

    points['ffa_spawn1'] = (-12.44, 10.29, -5.46) + (1.55, 1.45, 0.11)
    points['ffa_spawn2'] = (9.64, 10.29, -5.46) + (1.55, 1.45, 0.04)
    points['ffa_spawn3'] = (3.86, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['ffa_spawn4'] = (-6.42, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['ffa_spawn5'] = (-6.42, 4.04, -5.46) + (1.33, 1.45, 0.04)
    points['ffa_spawn6'] = (3.67, 4.04, -5.46) + (1.87, 1.45, 0.04)

    points['powerup_spawn1'] = (-8.07, 17.04, 5.46)
    points['powerup_spawn2'] = (5.50, 17.04, -5.46)
    points['powerup_spawn3'] = (5.50, 4.36, -5.46)
    points['powerup_spawn4'] = (-8.07, 4.35, 5.46)

    points['spawn1'] = (-12.44, 10.29, -5.46) + (1.55, 1.45, 0.11)
    points['spawn2'] = (9.64, 10.29, -5.46) + (1.55, 1.45, 0.04)

    points['flag_default'] = (-1.42, 12.80, -5.46)

    points['flag1'] = (-13.86, 10.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag2'] = (11.29, 10.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag3'] = (3.86, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag4'] = (-6.42, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag5'] = (-6.42, 4.04, -5.46) + (1.33, 1.45, 0.04)
    points['flag6'] = (3.67, 4.04, -5.46) + (1.87, 1.45, 0.04)

    points['spawn_by_flag1'] = (-13.86, 10.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag2'] = (11.29, 10.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag3'] = (3.86, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag4'] = (-6.42, 17.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag5'] = (-6.42, 4.04, -5.46) + (1.33, 1.45, 0.04)
    points['spawn_by_flag6'] = (3.67, 4.04, -5.46) + (1.87, 1.45, 0.04)


class rT(bs.Map):
    """Flying map."""

    defs = Thoughts_d
    name = 'Space Thoughts'

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
        return 'alwaysLandLevelColor'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': bs.getmesh('alwaysLandLevel'),
            'bottom_mesh': bs.getmesh('alwaysLandLevelBottom'),
            'bgmesh': bs.getmesh('alwaysLandBG'),
            'collision_mesh': bs.getcollisionmesh('alwaysLandLevelCollide'),
            'tex': bs.gettexture('alwaysLandLevelColor'),
            'bgtex': bs.gettexture('alwaysLandBGColor'),
            'vr_fill_mound_mesh': bs.getmesh('alwaysLandVRFillMound'),
            'vr_fill_mound_tex': bs.gettexture('vrFillMound'),
        }
        return data

    @classmethod
    def get_music_type(cls) -> bs.MusicType:
        return bs.MusicType.FLYING

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -3.7, 2.5))
        shared = SharedObjects.get()

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'color': (0.4, 0.2, 0.7),
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )

        # throw out some tips on flying
        txt = bs.newnode(
            'text',
            attrs={
                'text': bs.Lstr(resource='pressJumpToFlyText'),
                'scale': 1.2,
                'maxwidth': 800,
                'position': (0, 200),
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'center',
                'v_attach': 'bottom',
            },
        )
        cmb = bs.newnode(
            'combine',
            owner=txt,
            attrs={'size': 4, 'input0': 0.3, 'input1': 0.9, 'input2': 0.0},
        )
        bs.animate(cmb, 'input3', {3.0: 0, 4.0: 1, 9.0: 1, 10.0: 0})
        cmb.connectattr('output', txt, 'color')
        bs.timer(10.0, txt.delete)

        self.zone = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': (-0.8748348681, 10.212941713, -5.729538885),
                'color': (-1, -1, -1),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [36.09666006, 21.19950145, 0.07],
            },
        )

        CollideBox(
            position=(11 + -1.3, 9, -5.5),
            scale=(5, 2, 0.5),
            color=(1, 1, 1),
            visible=True,
        )  # 1
        CollideBox(
            position=(-11 + -1.3, 9, -5.5),
            scale=(5, 2, 0.5),
            color=(1, 1, 1),
            visible=True,
        )  # 2
        CollideBox(
            position=(0 + -1.3, 10, -5.5),
            scale=(1.5, 5, 0.5),
            color=(1, 1, 1),
            visible=True,
        )  # 3
        CollideBox(
            position=(5 + -1.3, 3, -5.5),
            scale=(5, 1.5, 0.5),
            color=(1, 1, 1),
            visible=True,
        )  # 4
        CollideBox(
            position=(-5 + -1.3, 3, -5.5),
            scale=(5, 1.5, 0.5),
            color=(1, 1, 1),
            visible=True,
        )  # 5
        CollideBox(
            position=(5 + -1.3, 16, -5.5),
            scale=(5, 1.5, 0.5),
            color=(1, 1, 1),
            visible=True,
        )  # 6
        CollideBox(
            position=(-5 + -1.3, 16, -5.5),
            scale=(5, 1.5, 0.5),
            color=(1, 1, 1),
            visible=True,
        )  # 7
        text = bs.newnode(
            'text',
            attrs={
                'position': (0, 32, 0),
                'text': 'Not Easter Egg Lol',
                'in_world': True,
                'shadow': 1.5,
                'flatness': 0.7,
                'color': (1, 1, 1.2),
                'opacity': 1.0,
                'scale': 0.023,
                'h_align': 'center',
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.3, 1.23, 1.0)
        gnode.ambient_color = (1.3, 1.23, 1.0)
        gnode.vignette_outer = (0.64, 0.59, 0.69)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True
        FadeEfect(gnode.tint)
        Credits()


# List Maps
zk2059 = [
    SpazMap,
    RampageMod,
    BridgitC,
    thec,
    collosal_monkey,
    tZoe,
    rT,  # ULTIMATE UPDATE
    Tarena,
    IslandMine,  # v3 UPDATE
    FactoryMap,
    PlatformsMap,
    DarkZone,  # v2
    NeoZone,
    CMap,  # v1
]


def register_maps():
    for new_map in zk2059:
        _map.register_map(new_map)


# Crown 
register_maps()
