# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


class Pointzz:
    points, boxes = {}, {}
    points['spawn1'] = (-8.03866, 0.02275, 0.0) + (0.5, 0.05, 4.0)
    points['spawn2'] = (8.82311, 0.01092, 0.0) + (0.5, 0.05, 4.0)
    boxes['area_of_interest_bounds'] = (
        (0.0, 1.18575, 0.43262) + (0, 0, 0) + (29.81803, 11.57249, 18.89134)
    )
    boxes['map_bounds'] = (
        (0.0, 1.185751251, 0.4326226188)
        + (0.0, 0.0, 0.0)
        + (42.09506485, 22.81173179, 29.76723155)
    )


class PointzzforH:
    points, boxes = {}, {}
    boxes['area_of_interest_bounds'] = (
        (0.0, 0.7956858119, 0.0)
        + (0.0, 0.0, 0.0)
        + (30.80223883, 0.5961646365, 13.88431707)
    )
    boxes['map_bounds'] = (
        (0.0, 0.7956858119, -0.4689020853)
        + (0.0, 0.0, 0.0)
        + (35.16182389, 12.18696164, 21.52869693)
    )
    points['spawn1'] = (-6.835352227, 0.02305323209, 0.0) + (1.0, 1.0, 3.0)
    points['spawn2'] = (6.857415055, 0.03938567998, 0.0) + (1.0, 1.0, 3.0)


class VolleyBallMap(bs.Map):
    defs = Pointzz()
    name = 'Open Field'

    @classmethod
    def get_play_types(cls) -> list[str]:
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'footballStadiumPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': bs.getmesh('footballStadium'),
            'vr_fill_mesh': bs.getmesh('footballStadiumVRFill'),
            'collision_mesh': bs.getcollisionmesh('footballStadiumCollide'),
            'tex': bs.gettexture('footballStadium'),
        }
        return data

    def __init__(self):
        super().__init__()
        shared = SharedObjects.get()
        x = -5
        while x < 5:
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0.25, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0.5, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0.75, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 1, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            x = x + 0.5

        y = -1
        while y > -11:
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (y, 0.01, 4),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (y, 0.01, -4),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-y, 0.01, 4),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-y, 0.01, -4),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            y -= 1

        z = 0
        while z < 5:
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (11, 0.01, z),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (11, 0.01, -z),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-11, 0.01, z),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-11, 0.01, -z),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            z += 1

        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh'],
                'collision_mesh': self.preloaddata['collision_mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['tex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5


class VolleyBallMapH(bs.Map):
    defs = PointzzforH()
    name = 'Closed Arena'

    @classmethod
    def get_play_types(cls) -> list[str]:
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'hockeyStadiumPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshs': (
                bs.getmesh('hockeyStadiumOuter'),
                bs.getmesh('hockeyStadiumInner'),
            ),
            'vr_fill_mesh': bs.getmesh('footballStadiumVRFill'),
            'collision_mesh': bs.getcollisionmesh('hockeyStadiumCollide'),
            'tex': bs.gettexture('hockeyStadium'),
        }
        mat = bs.Material()
        mat.add_actions(actions=('modify_part_collision', 'friction', 0.01))
        data['ice_material'] = mat
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        x = -5
        while x < 5:
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0.25, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0.5, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 0.75, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (0, 1, x),
                    'color': (1, 1, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            x = x + 0.5

        y = -1
        while y > -11:
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (y, 0.01, 4),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (y, 0.01, -4),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-y, 0.01, 4),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-y, 0.01, -4),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            y -= 1

        z = 0
        while z < 5:
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (11, 0.01, z),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (11, 0.01, -z),
                    'color': (1, 0, 0),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-11, 0.01, z),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            self.zone = bs.newnode(
                'locator',
                attrs={
                    'shape': 'circle',
                    'position': (-11, 0.01, -z),
                    'color': (0, 0, 1),
                    'opacity': 1,
                    'draw_beauty': True,
                    'additive': False,
                    'size': [0.40],
                },
            )
            z += 1

        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': None,
                'collision_mesh':
                # we dont want Goalposts...
                bs.getcollisionmesh('footballStadiumCollide'),
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'vr_only': True,
                'lighting': False,
                'background': True,
            },
        )
        mats = [shared.footing_material]
        self.floor = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['meshs'][1],
                'color_texture': self.preloaddata['tex'],
                'opacity': 0.92,
                'opacity_in_low_or_medium_quality': 1.0,
                'materials': mats,
                'color': (0.4, 0.9, 0),
            },
        )

        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': bs.getmesh('natureBackground'),
                'lighting': False,
                'background': True,
                'color': (0.5, 0.30, 0.4),
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.floor_reflection = True
        gnode.debris_friction = 0.3
        gnode.debris_kill_height = -0.3
        gnode.tint = (1.2, 1.3, 1.33)
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.66, 0.67, 0.73)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
        # self.is_hockey = True


_map.register_map(VolleyBallMap)
_map.register_map(VolleyBallMapH)
