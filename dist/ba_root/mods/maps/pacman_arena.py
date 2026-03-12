# Released under the MIT License. See LICENSE for details.
#
# Updated to API9 with Claude Opus 4.6
"""Pac-Man Arena map for BombSquad."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import Any, override

import bascenev1 as bs

from bascenev1lib.gameutils import SharedObjects


# ═══════════════════════════════════════════════════════════════════
# MAP DEFS
# ═══════════════════════════════════════════════════════════════════

class _PacManMapDefs:
    """Minimal map-definition data so the base Map class is happy."""

    points = {}
    boxes = {
        'area_of_interest_bounds': (
            # center x, y, z  +  rotation (unused)  +  size x, y, z
            0.0, 2.0, 0.0,  0.0, 0.0, 0.0,  30.0, 10.0, 30.0
        ),
        'map_bounds': (
            0.0, 5.0, 0.0,  0.0, 0.0, 0.0,  100.0, 60.0, 100.0
        ),
    }

    def __init__(self, spawn_pts: list[tuple] | None = None):
        # We copy so each instance is independent.
        self.points = dict(_PacManMapDefs.points)
        self.boxes = dict(_PacManMapDefs.boxes)
        if spawn_pts:
            for i, pt in enumerate(spawn_pts):
                self.points[f'spawn{i + 1}'] = pt
                self.points[f'ffa_spawn{i + 1}'] = pt


# ═══════════════════════════════════════════════════════════════════
# MAP
# ═══════════════════════════════════════════════════════════════════

class PacManMap(bs.Map):
    """Minimal map: BG mesh + a large floor region for footing."""

    # Provide default defs so the base class doesn't warn.
    defs = _PacManMapDefs()

    name = 'Pac-Man Arena'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'black'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'bg_mesh': bs.getmesh('thePadBG'),
            'bg_tex': bs.gettexture('black'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        # Region nodes are non-physical by default; force collisions on.
        self.collision_material = bs.Material()
        self.collision_material.add_actions(
            actions=('modify_part_collision', 'collide', True),
        )

        # Background: ThePad BG model with black texture.
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

        # Floor: one big region node with collision + footing material.
        self.floor_region = bs.newnode(
            'region',
            attrs={
                'position': (0, 0, 0),
                'scale': (40, 1.0, 40),
                'type': 'box',
                'materials': [self.collision_material, shared.footing_material],
            },
        )

        # Death region below.
        self.death_region = bs.newnode(
            'region',
            attrs={
                'position': (0, -10, 0),
                'scale': (80, 2, 80),
                'type': 'box',
                'materials': [shared.death_material],
            },
        )

        # Globals: dark tint, dark ambient for arcade style.
        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.75, 0.75, 0.9)
        gnode.ambient_color = (0.6, 0.6, 0.8)
        gnode.vignette_outer = (0.4, 0.4, 0.55)
        gnode.vignette_inner = (0.95, 0.95, 0.99)
        gnode.shadow_ortho = True
        gnode.shadow_offset = (0, 0, 0)

    def set_floor_size(
        self,
        width: float,
        depth: float,
        offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Called by the game mode to match floor to maze size."""
        if self.floor_region:
            self.floor_region.position = (offset[0], offset[1], offset[2])
            self.floor_region.scale = (width + 2.0, 1.0, depth + 2.0)
        if self.death_region:
            self.death_region.position = (offset[0], offset[1] - 10.0, offset[2])

    def update_defs_for_spawns(
        self, spawn_positions: list[tuple[float, float, float]]
    ) -> None:
        """Update the map's spawn points based on level data."""
        new_defs = _PacManMapDefs()
        for i, pos in enumerate(spawn_positions):
            # Spawn format: (x, y, z, x_range, y_range, z_range)
            pt = (pos[0], pos[1], pos[2], 0.5, 1.0, 0.5)
            new_defs.points[f'spawn{i + 1}'] = pt
            new_defs.points[f'ffa_spawn{i + 1}'] = pt
        self.__class__.defs = new_defs
        self.spawn_points = self.get_def_points('spawn') or [(0, 0, 0, 0, 0, 0)]
        self.ffa_spawn_points = self.get_def_points('ffa_spawn') or [
            (0, 0, 0, 0, 0, 0)
        ]


# Register the map so the engine knows about it.
bs.register_map(PacManMap)
