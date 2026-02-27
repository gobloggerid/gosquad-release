# ba_meta require api 9


from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    pass


class FootballStadiumV2MapData:
    points = {}
    boxes = {}

    boxes['area_of_interest_bounds'] = (
        (0.0, 1.185751251, 0.4326226188)
        + (0.0, 0.0, 0.0)
        + (29.8180273, 11.57249038, 18.89134176)
    )
    boxes['edge_box'] = (
        (-0.103873591, 0.4133341891, 0.4294651013)
        + (0.0, 0.0, 0.0)
        + (22.48295719, 1.290242794, 8.990252454)
    )
    points['ffa_spawn1'] = (-0.08015551329, 0.02275111462, -4.373674593) + (
        8.895057015,
        1.0,
        0.444350722,
    )
    points['ffa_spawn2'] = (-0.08015551329, 0.02275111462, 4.076288941) + (
        8.895057015,
        1.0,
        0.444350722,
    )
    boxes['map_bounds'] = (
        (0.0, 1.185751251, 0.4326226188)
        + (0.0, 0.0, 0.0)
        + (42.09506485, 22.81173179, 29.76723155)
    )
    points['flag1'] = (-11.21689747, 0.09527878981, -0.07659307272)
    points['flag2'] = (11.08204909, 0.04119542459, -0.07659307272)
    points['flag_default'] = (-0.1001374046, 0.04180340146, 0.1095578275)
    points['puck'] = (0, -10, 0)
    boxes['goal1'] = (8.8, 1.0, 0.0) + (0.0, 0.0, 0.0) + (0.2, 1.6, 3.0)
    boxes['goal2'] = (-8.8, 1.0, 0.0) + (0.0, 0.0, 0.0) + (0.2, 1.6, 3.0)
    points['powerup_spawn1'] = (5.414681236, 0.9515026107, -5.037912441)
    points['powerup_spawn2'] = (-5.555402285, 0.9515026107, -5.037912441)
    points['powerup_spawn3'] = (5.414681236, 0.9515026107, 5.148223181)
    points['powerup_spawn4'] = (-5.737266365, 0.9515026107, 5.148223181)
    points['spawn1'] = (-6.835352227, 0.02305323209, 0.0) + (1.0, 1.0, 3.0)
    points['spawn2'] = (6.857415055, 0.03938567998, 0.0) + (1.0, 1.0, 3.0)
    points['tnt1'] = (-0.05791962398, 1.080990833, -4.765886164)
    points['box1'] = (-5.08421587483, 0.9515026107, -2.7762602271)


class FootballStadiumV2Map(bs.Map):
    defs = FootballStadiumV2MapData()
    name = 'Soccer Stadium Original'

    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee', 'keep_away', 'hockey', 'epic_soccer']

    @classmethod
    def get_preview_texture_name(cls) -> list[str]:
        return 'footballStadiumPreview'

    @classmethod
    def on_preload(cls) -> any:
        data: dict[str, any] = {
            'mesh': bs.getmesh('footballStadium'),
            'mesh3': bs.getmesh('hockeyStadiumOuter'),
            'tex3': bs.gettexture('hockeyStadium'),
            'collision_mesh3': bs.getcollisionmesh('hockeyStadiumCollide'),
            'tex': bs.gettexture('footballStadium'),
            'collision_mesh': bs.getcollisionmesh('footballStadiumCollide'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'collision_mesh': self.preloaddata['collision_mesh'],
                'materials': [shared.footing_material],
            },
        )
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh3'],
                'color_texture': self.preloaddata['tex3'],
                'collision_mesh': self.preloaddata['collision_mesh3'],
                'materials': [shared.footing_material],
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.shadow_ortho = False
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        self.is_hockey = False

    def is_point_near_edge(self, point: bs.Vec3, running: bool = False) -> bool:
        xpos = point.x
        zpos = point.z
        x_adj = xpos * 0.125
        z_adj = (zpos + 3.7) * 0.2
        if running:
            x_adj *= 1.4
            z_adj *= 1.4
        return x_adj * x_adj + z_adj * z_adj > 1.0


_map.register_map(FootballStadiumV2Map)
