# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


class _MazeRaceMapDefs:
    points: dict = {}
    boxes: dict = {
        'area_of_interest_bounds': (
            0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 60.0, 20.0, 60.0
        ),
        'map_bounds': (
            0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 120.0, 60.0, 120.0
        ),
    }

    def __init__(self, spawn_pts: list[tuple] | None = None):
        self.points = dict(_MazeRaceMapDefs.points)
        self.boxes = dict(_MazeRaceMapDefs.boxes)
        if spawn_pts:
            for i, pt in enumerate(spawn_pts):
                self.points[f'spawn{i + 1}'] = pt
                self.points[f'ffa_spawn{i + 1}'] = pt


class MazeRaceMap(bs.Map):
    defs = _MazeRaceMapDefs()
    name = 'Maze Meltdown Arena'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee', 'race']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'black'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        return {
            'bg_mesh': bs.getmesh('thePadBG'),
            'bg_tex': bs.gettexture('black'),
        }

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.collision_mat = bs.Material()
        self.collision_mat.add_actions(
            actions=('modify_part_collision', 'collide', True)
        )
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['bg_mesh'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bg_tex'],
            },
        )
        self.background = self.node
        self.floor_region = bs.newnode(
            'region',
            attrs={
                'position': (0, 0, 0),
                'scale': (60, 1.0, 60),
                'type': 'box',
                'materials': [self.collision_mat, shared.footing_material],
            },
        )
        self.death_region = bs.newnode(
            'region',
            attrs={
                'position': (0, -10, 0),
                'scale': (120, 2, 120),
                'type': 'box',
                'materials': [shared.death_material],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.85, 0.85, 1.0)
        gnode.ambient_color = (0.7, 0.7, 0.9)
        gnode.vignette_outer = (0.45, 0.45, 0.6)
        gnode.vignette_inner = (0.95, 0.95, 0.99)
        gnode.shadow_ortho = True

    def set_floor_size(
        self,
        width: float,
        depth: float,
        maze_y: float = 0.0,
        maze_z: float = 0.0,
    ) -> None:
        if self.floor_region:
            self.floor_region.position = (0.0, maze_y, maze_z)
            self.floor_region.scale = (width + 4.0, 1.0, depth + 4.0)
        if self.death_region:
            self.death_region.position = (0.0, maze_y - 10, maze_z)

    def update_defs(
        self,
        spawn_positions: list[tuple[float, float, float]],
        bounds_w: float,
        bounds_d: float,
        cam_y: float = 0.0,
        cam_z: float = 0.0,
        maze_y: float = 0.0,
        maze_z: float = 0.0,
    ) -> None:
        new_defs = _MazeRaceMapDefs()
        for i, pos in enumerate(spawn_positions):
            pt = (pos[0], pos[1], pos[2], 0.5, 1.0, 0.5)
            new_defs.points[f'spawn{i + 1}'] = pt
            new_defs.points[f'ffa_spawn{i + 1}'] = pt

        # Initial AOI — _update_camera overrides this dynamically.
        aoi_w = min(bounds_w + 2.0, 18.0)
        aoi_d = min(bounds_d + 2.0, 18.0)
        new_defs.boxes['area_of_interest_bounds'] = (
            0.0,
            maze_y + 2.0 + cam_y,
            maze_z + cam_z,
            0.0,
            0.0,
            0.0,
            aoi_w,
            6.0,
            aoi_d,
        )
        new_defs.boxes['map_bounds'] = (
            0.0,
            maze_y + 2.0,
            maze_z,
            0.0,
            0.0,
            0.0,
            bounds_w + 30,
            60.0,
            bounds_d + 30,
        )
        self.__class__.defs = new_defs
        self.spawn_points = self.get_def_points('spawn') or [(0, 0, 0, 0, 0, 0)]
        self.ffa_spawn_points = self.get_def_points('ffa_spawn') or [(0, 0, 0, 0, 0, 0)]


bs.register_map(MazeRaceMap)
