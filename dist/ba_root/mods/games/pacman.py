# Released under the MIT License. See LICENSE for details.
#
# Updated to API9 with Claude Opus 4.6
"""Pac-Man style dot-collection game for BombSquad."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import importlib
import random
import weakref
from typing import TYPE_CHECKING, override
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

import bascenev1 as bs
import babase

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.respawnicon import RespawnIcon
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence

MIN_SPHERE_SIZE = 0.01

# Ensure the Pac-Man Arena map module is imported so it can register itself.
_PACMAN_ARENA_IMPORT_OK = False
for _module_name in ('maps.pacman_arena', 'pacman_arena'):
    try:
        importlib.import_module(_module_name)
    except ImportError:
        continue
    except Exception:
        babase.applog.exception(
            f'Error importing Pac-Man map module: {_module_name}'
        )
    else:
        _PACMAN_ARENA_IMPORT_OK = True
        break

if not _PACMAN_ARENA_IMPORT_OK:
    class _PacManMapDefs:
        points = {}
        boxes = {
            'area_of_interest_bounds': (
                0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 30.0, 10.0, 30.0
            ),
            'map_bounds': (
                0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 100.0, 60.0, 100.0
            ),
        }

        def __init__(self) -> None:
            self.points = dict(_PacManMapDefs.points)
            self.boxes = dict(_PacManMapDefs.boxes)

    class _PacManMapFallback(bs.Map):
        """Fallback map used when external pacman_arena cannot import."""

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
        def on_preload(cls) -> dict[str, object]:
            return {
                'bg_mesh': bs.getmesh('thePadBG'),
                'bg_tex': bs.gettexture('black'),
            }

        def __init__(self) -> None:
            super().__init__()
            shared = SharedObjects.get()
            self.collision_material = bs.Material()
            self.collision_material.add_actions(
                actions=('modify_part_collision', 'collide', True),
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
                    'scale': (40, 1.0, 40),
                    'type': 'box',
                    'materials': [self.collision_material, shared.footing_material],
                },
            )
            self.death_region = bs.newnode(
                'region',
                attrs={
                    'position': (0, -10, 0),
                    'scale': (80, 2, 80),
                    'type': 'box',
                    'materials': [shared.death_material],
                },
            )

        def set_floor_size(
            self,
            width: float,
            depth: float,
            offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
        ) -> None:
            if self.floor_region:
                self.floor_region.position = (offset[0], offset[1], offset[2])
                self.floor_region.scale = (width + 2.0, 1.0, depth + 2.0)
            if self.death_region:
                self.death_region.position = (
                    offset[0], offset[1] - 10.0, offset[2]
                )

        def update_defs_for_spawns(
            self, spawn_positions: list[tuple[float, float, float]]
        ) -> None:
            new_defs = _PacManMapDefs()
            for i, pos in enumerate(spawn_positions):
                pt = (pos[0], pos[1], pos[2], 0.5, 1.0, 0.5)
                new_defs.points[f'spawn{i + 1}'] = pt
                new_defs.points[f'ffa_spawn{i + 1}'] = pt
            self.__class__.defs = new_defs
            self.spawn_points = self.get_def_points('spawn') or [
                (0, 0, 0, 0, 0, 0)
            ]
            self.ffa_spawn_points = self.get_def_points('ffa_spawn') or [
                (0, 0, 0, 0, 0, 0)
            ]

    bs.register_map(_PacManMapFallback)
    babase.print_error(
        'Using fallback Pac-Man map from pacman.py '
        '(external pacman_arena import failed).'
    )


# ═══════════════════════════════════════════════════════════════════
# GRID CELL TYPES
# ═══════════════════════════════════════════════════════════════════

WALL = '#'
DOT = '.'
POWER_PELLET = 'O'
EMPTY = ' '
PLAYER_SPAWN = 'P'
GHOST_SPAWN = 'G'
GHOST_DOOR = '-'
VOID = 'X'  # Non-walkable, no visual. Outside the maze.
TUNNEL_PORTAL = 'T'  # Tunnel exit — portal is placed here.


# ═══════════════════════════════════════════════════════════════════
# LEVEL LAYOUTS
# ═══════════════════════════════════════════════════════════════════

CLASSIC_LAYOUT = [
    # Compact 20x21 classic layout - single-thick walls.
    '####################',  # 0
    '#.O......##......O.#',  # 1
    '#.##.###.##.###.##.#',  # 2
    '#..................#',  # 3
    '#.##.#.######.#.##.#',  # 4
    '#....#...##...#....#',  # 5
    '####.###....###.####',  # 6
    '   #............#   ',  # 7
    '####.####--####.####',  # 8
    'T......#    #......T',  # 9
    '####.#.######.#.####',  # 10
    '   #.#........#.#   ',  # 11
    '####.#.######.#.####',  # 12
    '#........##........#',  # 13
    '#.##.###.##.###.##.#',  # 14
    '#..#.....P .....#..#',  # 15
    '##.#.#.######.#.#.##',  # 16
    '#....#...##...#....#',  # 17
    '#.######.##.######.#',  # 18
    '#.O..............O.#',  # 19
    '####################',  # 20
]


# ═══════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class WallBlock:
    """Merged wall block: one region for collision,
    plus individual 1x1 cube locators for each cell."""
    region_node: bs.Node
    locator_nodes: list[bs.Node] = field(default_factory=list)


@dataclass
class DotActor:
    """A collectible dot in the maze."""
    locator_node: bs.Node
    region_node: bs.Node
    grid_x: int
    grid_y: int
    is_power_pellet: bool = False
    collected: bool = False


@dataclass
class LevelData:
    """All parsed data from a generated level."""
    walls: list[WallBlock] = field(default_factory=list)
    dots: list[DotActor] = field(default_factory=list)
    player_spawns: list[tuple[float, float, float]] = field(
        default_factory=list
    )
    width: int = 0
    height: int = 0
    cell_size: float = 1.0
    total_dot_count: int = 0
    # Grid data for runtime path lookups.
    grid: list[str] = field(default_factory=list)
    grid_width: int = 0
    grid_height: int = 0
    origin_offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    # Pairs of (left_cell, right_cell) for horizontal tunnel exits.
    tunnel_pairs: list[tuple[tuple[int, int], tuple[int, int]]] = field(
        default_factory=list
    )


# ═══════════════════════════════════════════════════════════════════
# LEVEL BUILDER
# ═══════════════════════════════════════════════════════════════════

class PacManLevelBuilder:
    """Builds a Pac-Man maze from a 2D text grid.

    Each wall cell becomes:
      - A 'region' node (box) with footing_material for collision
      - A 'locator' node (box shape) for the wireframe visual

    Dots become:
      - A 'locator' node (circle shape, draw_beauty=True)
      - A 'region' node for player-touch detection
    """

    def __init__(
        self,
        layout: list[str] | None = None,
        cell_size: float = 1.0,
        wall_height: float = 2.4,
        wall_color: tuple[float, float, float] = (0.15, 0.25, 0.9),
        wall_opacity: float = 0.7,
        dot_color: tuple[float, float, float] = (1.0, 1.0, 0.8),
        power_pellet_color: tuple[float, float, float] = (1.0, 0.6, 0.2),
        floor_y: float = 0.0,
        origin_offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
        dot_material: bs.Material | None = None,
        optimized_wireframe: bool = False,
        wall_style: int = 0,
        path_color: tuple[float, float, float] | None = None,
    ) -> None:
        self._layout = layout or CLASSIC_LAYOUT
        self._cell_size = cell_size
        self._wall_height = wall_height
        self._wall_color = wall_color
        self._wall_opacity = wall_opacity
        self._dot_color = dot_color
        self._pp_color = power_pellet_color
        self._floor_y = floor_y
        self._origin_offset = origin_offset
        self._dot_material = dot_material
        self._optimized_wireframe = optimized_wireframe
        self._wall_style = wall_style  # 0=Regular, 1=Flat, 2=Invisible
        self._path_color = path_color  # None = no path tiles rendered

        self._grid_height = len(self._layout)
        self._grid_width = (
            max(len(row) for row in self._layout) if self._layout else 0
        )
        # Pad rows to uniform width.
        self._layout = [row.ljust(self._grid_width) for row in self._layout]

    # ── Coordinate Conversion ──

    def _grid_to_world(
        self, gx: float, gy: float
    ) -> tuple[float, float, float]:
        """Grid (col, row) → world (x, y, z). Centered on origin."""
        cs = self._cell_size
        offset_x = -(self._grid_width * cs) / 2.0 + cs / 2.0
        offset_z = -(self._grid_height * cs) / 2.0 + cs / 2.0

        wx = gx * cs + offset_x + self._origin_offset[0]
        wy = self._floor_y + self._origin_offset[1]
        wz = gy * cs + offset_z + self._origin_offset[2]
        return (wx, wy, wz)

    def _get_cell(self, gx: int, gy: int) -> str:
        if 0 <= gy < self._grid_height and 0 <= gx < self._grid_width:
            return self._layout[gy][gx]
        return ' '

    def _is_wall(self, gx: int, gy: int) -> bool:
        return self._get_cell(gx, gy) == WALL

    # ── Wall Merging (Performance) ──

    def _merge_walls_2d(self) -> list[tuple[int, int, int, int]]:
        """Two-pass merge: horizontal runs, then vertical stacking.
        Returns list of (gx_start, gy_start, width, height)."""
        # Pass 1: Horizontal runs per row.
        h_runs: list[tuple[int, int, int, int]] = []
        for gy in range(self._grid_height):
            gx = 0
            while gx < self._grid_width:
                if self._is_wall(gx, gy):
                    start = gx
                    while gx < self._grid_width and self._is_wall(gx, gy):
                        gx += 1
                    h_runs.append((start, gy, gx - start, 1))
                else:
                    gx += 1

        # Pass 2: Merge vertically adjacent runs with same x-start & width.
        h_runs.sort(key=lambda r: (r[0], r[2], r[1]))
        merged: list[tuple[int, int, int, int]] = []
        used: set[int] = set()

        for i, (gx, gy, w, h) in enumerate(h_runs):
            if i in used:
                continue
            cur_h = h
            cur_gy_end = gy + h
            for j in range(i + 1, len(h_runs)):
                if j in used:
                    continue
                ogx, ogy, ow, _ = h_runs[j]
                if ogx == gx and ow == w and ogy == cur_gy_end:
                    cur_h += 1
                    cur_gy_end += 1
                    used.add(j)
                elif ogx == gx and ow == w and ogy > cur_gy_end:
                    break
            used.add(i)
            merged.append((gx, gy, w, cur_h))

        return merged

    # ── Main Generation ──

    def generate(self) -> LevelData:
        """Parse layout, create wall + dot nodes. Returns LevelData."""
        shared = SharedObjects.get()
        cs = self._cell_size
        level = LevelData(
            width=self._grid_width,
            height=self._grid_height,
            cell_size=cs,
            grid=list(self._layout),
            grid_width=self._grid_width,
            grid_height=self._grid_height,
            origin_offset=self._origin_offset,
        )

        # Region nodes are non-physical by default — this material
        # forces them to be solid so characters collide with them.
        collision_mat = bs.Material()
        collision_mat.add_actions(
            actions=('modify_part_collision', 'collide', True),
        )

        # Wall cube visual height matches cell_size for true cubes.
        cube_size = cs

        # Floor region is centered at y=0 with scale 1.0, so the
        # top surface is at y=0.5. Everything sits on top of that.
        floor_top = 0.5 + self._origin_offset[1]

        # Flat walls: visual is a thin tile on the floor surface.
        # Invisible: skip wall visuals entirely (collision still exists).
        if self._wall_style == 1:  # Flat
            vis_h = cube_size * 0.15
        else:
            vis_h = cube_size

        # Wall cube locators: base on floor top, center at half vis up.
        cube_cy = floor_top + vis_h / 2.0

        # Wall collision regions: taller than visual cubes so players
        # can't jump over. Base on floor top.
        wall_cy = floor_top + self._wall_height / 2.0

        # ── Wall visuals (skipped when invisible) ──
        if self._wall_style != 2:  # Not Invisible
            if self._optimized_wireframe:
                # One locator per merged rectangle.
                for gx, gy, w, h in self._merge_walls_2d():
                    center_gx = gx + (w - 1) / 2.0
                    center_gy = gy + (h - 1) / 2.0
                    cx, _, cz = self._grid_to_world(center_gx, center_gy)
                    sx = w * cs
                    sz = h * cs
                    bs.newnode(
                        'locator',
                        attrs={
                            'shape': 'box',
                            'position': (cx, cube_cy, cz),
                            'size': (sx, vis_h, sz),
                            'color': self._wall_color,
                            'opacity': self._wall_opacity,
                            'draw_beauty': True,
                            'additive': True,
                        },
                    )
            else:
                # One cube locator per wall cell.
                for gy in range(self._grid_height):
                    for gx in range(self._grid_width):
                        if self._is_wall(gx, gy):
                            wx, _, wz = self._grid_to_world(gx, gy)
                            bs.newnode(
                                'locator',
                                attrs={
                                    'shape': 'box',
                                    'position': (wx, cube_cy, wz),
                                    'size': (cube_size, vis_h, cube_size),
                                    'color': self._wall_color,
                                    'opacity': self._wall_opacity,
                                    'draw_beauty': True,
                                    'additive': True,
                                },
                            )

        # ── Path tile visuals (optional floor colour overlay) ──
        if self._path_color is not None:
            path_tile_y = floor_top + 0.01  # Flush on the floor surface.
            path_tile_size = cs * 0.98       # Slight gap between tiles.
            for gy in range(self._grid_height):
                for gx in range(self._grid_width):
                    cell = self._get_cell(gx, gy)
                    # Render on every walkable, non-void cell.
                    if cell not in (WALL, VOID):
                        wx, _, wz = self._grid_to_world(gx, gy)
                        bs.newnode(
                            'locator',
                            attrs={
                                'shape': 'box',
                                'position': (wx, path_tile_y, wz),
                                'size': (path_tile_size, 0.02,
                                         path_tile_size),
                                'color': self._path_color,
                                'opacity': 0.9,
                                'draw_beauty': True,
                                'additive': False,
                            },
                        )

        # ── Wall collision (merged for efficiency) ──
        for gx, gy, w, h in self._merge_walls_2d():
            center_gx = gx + (w - 1) / 2.0
            center_gy = gy + (h - 1) / 2.0
            cx, _, cz = self._grid_to_world(center_gx, center_gy)
            sx = w * cs
            sz = h * cs

            region = bs.newnode(
                'region',
                attrs={
                    'position': (cx, wall_cy, cz),
                    'scale': (sx, self._wall_height, sz),
                    'type': 'box',
                    'materials': [collision_mat,
                                  shared.footing_material],
                },
            )
            level.walls.append(WallBlock(region_node=region))

        # ── Parse non-wall cells: dots, spawns ──
        dot_count = 0
        # Dots hover just above floor top.
        dot_y = floor_top + 0.15

        # Pre-load assets for 3D prop dots.
        dot_ghost_mat = bs.Material()
        dot_ghost_mat.add_actions(
            actions=('modify_part_collision', 'collide', False),
        )
        dot_mesh = bs.getmesh('frostyPelvis')
        dot_tex = bs.gettexture('tokens1')
        pp_tex = bs.gettexture('tokens1')

        for gy in range(self._grid_height):
            for gx in range(self._grid_width):
                cell = self._get_cell(gx, gy)
                wx, _, wz = self._grid_to_world(gx, gy)

                if cell == DOT or cell == POWER_PELLET:
                    is_pp = cell == POWER_PELLET

                    # 3D prop dot: frostyPelvis mesh + tokens1 texture.
                    # Ultra-light: microscopic physics body, no
                    # gravity, no collisions, no shadow.
                    # Vertically centered with wall cubes.
                    mesh_scale = 0.7 if is_pp else 0.35
                    loc = bs.newnode(
                        'prop',
                        attrs={
                            'position': (wx, cube_cy, wz),
                            'velocity': (0, 0, 0),
                            'body': 'sphere',
                            'body_scale': 0.01,
                            'mesh': dot_mesh,
                            'mesh_scale': mesh_scale,
                            'color_texture': pp_tex if is_pp else dot_tex,
                            'reflection': 'soft',
                            'reflection_scale': [0.3],
                            'gravity_scale': 0.0,
                            'damping': 1.0,
                            'max_speed': 0.0,
                            'shadow_size': 0.0,
                            'materials': [dot_ghost_mat],
                        },
                    )

                    # Pulsing animation for power pellets.
                    if is_pp:
                        bs.animate(
                            loc,
                            'mesh_scale',
                            {0: mesh_scale, 0.5: mesh_scale * 0.6,
                             1.0: mesh_scale},
                            loop=True,
                        )

                    # Collection region
                    mats = [shared.region_material]
                    if self._dot_material:
                        mats.append(self._dot_material)

                    rgn = bs.newnode(
                        'region',
                        attrs={
                            'position': (wx, dot_y, wz),
                            'scale': (cs * 0.6, 1.5, cs * 0.6),
                            'type': 'box',
                            'materials': mats,
                        },
                    )

                    dot = DotActor(
                        locator_node=loc,
                        region_node=rgn,
                        grid_x=gx,
                        grid_y=gy,
                        is_power_pellet=is_pp,
                    )
                    level.dots.append(dot)
                    dot_count += 1

                elif cell == PLAYER_SPAWN:
                    # Spawn well above the floor top so character
                    # drops down and lands on the footing region.
                    spawn_y = floor_top + 1.5
                    level.player_spawns.append((wx, spawn_y, wz))

        level.total_dot_count = dot_count

        # ── Detect tunnel portal pairs via 'T' markers ──
        # Scan every row for TUNNEL_PORTAL ('T') cells.
        # Pair the leftmost T with the rightmost T on the same row.
        for gy in range(self._grid_height):
            t_cells = [
                (gx, gy)
                for gx in range(self._grid_width)
                if self._get_cell(gx, gy) == TUNNEL_PORTAL
            ]
            if len(t_cells) >= 2:
                # Left-most and right-most T on this row form a pair.
                level.tunnel_pairs.append((t_cells[0], t_cells[-1]))

        # If no explicit player spawns found, add a center one.
        if not level.player_spawns:
            cx, _, cz = self._grid_to_world(
                self._grid_width // 2, self._grid_height // 2
            )
            level.player_spawns.append(
                (cx, floor_top + 1.5, cz)
            )

        return level

    def get_map_bounds(
        self,
    ) -> tuple[float, float, float, float, float, float]:
        """(min_x, min_y, min_z, max_x, max_y, max_z) for map bounds."""
        cs = self._cell_size
        tw = self._grid_width * cs
        th = self._grid_height * cs
        cx = self._origin_offset[0]
        cy = 5.0 + self._origin_offset[1]
        cz = self._origin_offset[2]
        hw, hh, hd = (tw + 8.0) / 2, 10.0, (th + 8.0) / 2
        return (cx - hw, cy - hh, cz - hd, cx + hw, cy + hh, cz + hd)

    def get_area_of_interest(
        self,
    ) -> tuple[float, float, float, float, float, float]:
        """(min_x, min_y, min_z, max_x, max_y, max_z)."""
        cs = self._cell_size
        tw = self._grid_width * cs
        th = self._grid_height * cs
        cx = self._origin_offset[0]
        cy = 2.0 + self._origin_offset[1]
        cz = self._origin_offset[2]
        hw, hh, hd = (tw + 2.0) / 2, 4.0, (th + 2.0) / 2
        return (cx - hw, cy - hh, cz - hd, cx + hw, cy + hh, cz + hd)


# Map implementation now lives in mods/maps/pacman_arena.py.


# ═══════════════════════════════════════════════════════════════════
# PLAYER / TEAM
# ═══════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════
# GHOST SYSTEM
# ═══════════════════════════════════════════════════════════════════


class GhostState(Enum):
    """Ghost AI states matching classic Pac-Man."""
    IN_HOUSE = 'in_house'     # Waiting inside ghost house
    EXITING = 'exiting'       # Moving up through the door
    CHASE = 'chase'           # Unique targeting per ghost type
    SCATTER = 'scatter'       # Retreat to assigned corner
    FRIGHTENED = 'frightened' # After power pellet — vulnerable
    EATEN = 'eaten'           # Eyes returning to ghost house


class GhostType(Enum):
    """The four classic ghosts."""
    BLINKY = 'blinky'  # Red — direct chaser
    PINKY = 'pinky'    # Pink — ambusher (4 ahead)
    INKY = 'inky'      # Cyan — fickle (vector from Blinky)
    CLYDE = 'clyde'    # Orange — shy (scatters when close)


# Per-type configuration: color, character, scatter corner, exit delay,
# and egg texture for the ghost's prop body.
GHOST_CONFIG: dict[GhostType, dict] = {
    GhostType.BLINKY: {
        'color': (3.0, 0.05, 0.05),     # Red
        'highlight': (3.0, 0.2, 0.2),
        'character': 'Kronk',
        'scatter_corner': 'top_right',
        'house_exit_delay': 0.0,
    },
    GhostType.PINKY: {
        'color': (3.0, 0.15, 2.6),      # Magenta-pink
        'highlight': (3.0, 0.2, 2.8),
        'character': 'Zoe',
        'scatter_corner': 'top_left',
        'house_exit_delay': 3.0,
    },
    GhostType.INKY: {
        'color': (0.05, 1.8, 3.0),      # Cyan
        'highlight': (0.1, 2.2, 3.0),
        'character': 'Snake Shadow',
        'scatter_corner': 'bottom_right',
        'house_exit_delay': 7.0,
    },
    GhostType.CLYDE: {
        'color': (3.0, 1.3, 0.0),       # Orange
        'highlight': (3.0, 1.8, 0.1),
        'character': 'Mel',
        'scatter_corner': 'bottom_left',
        'house_exit_delay': 11.0,
    },
}

# Frightened appearance.
_FRIGHT_COLOR = (0.05, 0.05, 3.0)      # Deep blue
_FRIGHT_HIGHLIGHT = (0.1, 0.1, 3.0)
_FRIGHT_FLASH_COLOR = (3.0, 3.0, 3.0)  # White flash when about to end
_FRIGHT_FLASH_HIGHLIGHT = (3.0, 3.0, 3.0)
_EATEN_COLOR = (0.5, 0.5, 0.5)         # Dim grey eyes

# Classic Pac-Man scatter/chase wave durations (seconds).
_WAVE_PATTERN: list[tuple[GhostState, float]] = [
    (GhostState.SCATTER, 7.0),
    (GhostState.CHASE, 20.0),
    (GhostState.SCATTER, 7.0),
    (GhostState.CHASE, 20.0),
    (GhostState.SCATTER, 5.0),
    (GhostState.CHASE, 20.0),
    (GhostState.SCATTER, 5.0),
    (GhostState.CHASE, 999.0),  # Permanent chase
]

_FRIGHTENED_DURATION = 8.0
_FRIGHTENED_FLASH_TIME = 3.0  # Flash for last N seconds


# ── BFS Pathfinding ──

def _bfs_path(
    grid: list[str],
    start: tuple[int, int],
    goal: tuple[int, int],
    gw: int,
    gh: int,
    allow_door: bool = False,
) -> list[tuple[int, int]]:
    """BFS on the grid. Returns the full shortest path from *start*
    to *goal* as a list of (gx, gz) cells (including start and goal).

    Returns an empty list if no path exists.
    Walls ('#', 'X') block movement.
    Ghost door ('-') blocks unless *allow_door* is True.
    """
    if start == goal:
        return [start]

    # Clamp goal to grid bounds.
    gx_goal = max(0, min(gw - 1, goal[0]))
    gy_goal = max(0, min(gh - 1, goal[1]))
    goal = (gx_goal, gy_goal)

    visited: set[tuple[int, int]] = {start}
    # Queue entries: (current_cell, path_so_far)
    queue: deque[tuple[tuple[int, int], list[tuple[int, int]]]] = deque()

    for dx, dz in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        nx, nz = start[0] + dx, start[1] + dz
        # Tunnel wrap.
        if nx < 0:
            nx = gw - 1
        elif nx >= gw:
            nx = 0
        if nz < 0 or nz >= gh:
            continue
        cell = grid[nz][nx] if nx < len(grid[nz]) else 'X'
        if cell in ('#', 'X'):
            continue
        if cell == '-' and not allow_door:
            continue
        visited.add((nx, nz))
        queue.append(((nx, nz), [start, (nx, nz)]))

    while queue:
        (cx, cz), path = queue.popleft()
        if (cx, cz) == goal:
            return path
        for dx, dz in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, nz = cx + dx, cz + dz
            if nx < 0:
                nx = gw - 1
            elif nx >= gw:
                nx = 0
            if nz < 0 or nz >= gh:
                continue
            if (nx, nz) in visited:
                continue
            cell = grid[nz][nx] if nx < len(grid[nz]) else 'X'
            if cell in ('#', 'X'):
                continue
            if cell == '-' and not allow_door:
                continue
            visited.add((nx, nz))
            queue.append(((nx, nz), path + [(nx, nz)]))

    return []  # No path found.


def _bfs_distance(
    grid: list[str],
    start: tuple[int, int],
    goal: tuple[int, int],
    gw: int,
    gh: int,
) -> int:
    """BFS shortest path distance (cell count) between two points."""
    if start == goal:
        return 0
    visited: set[tuple[int, int]] = {start}
    queue: deque[tuple[tuple[int, int], int]] = deque()
    for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nx, nz = start[0] + dx, start[1] + dz
        if nx < 0:
            nx = gw - 1
        elif nx >= gw:
            nx = 0
        if nz < 0 or nz >= gh:
            continue
        cell = grid[nz][nx] if nx < len(grid[nz]) else 'X'
        if cell in ('#', 'X', '-'):
            continue
        visited.add((nx, nz))
        queue.append(((nx, nz), 1))
    while queue:
        (cx, cz), dist = queue.popleft()
        if (cx, cz) == goal:
            return dist
        for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, nz = cx + dx, cz + dz
            if nx < 0:
                nx = gw - 1
            elif nx >= gw:
                nx = 0
            if nz < 0 or nz >= gh:
                continue
            if (nx, nz) in visited:
                continue
            cell = grid[nz][nx] if nx < len(grid[nz]) else 'X'
            if cell in ('#', 'X', '-'):
                continue
            visited.add((nx, nz))
            queue.append(((nx, nz), dist + 1))
    return 9999


# ── Ghost Mover (path-following grid movement) ──

class GhostMover:
    """Grid-based movement for a ghost Spaz.

    The ghost asks its AI for a target cell, BFS computes the
    full shortest path, and the mover walks the ghost along it
    one cell at a time.  The ghost's immediate target is always
    just "the next tile on the route."

    The path is re-computed every *repath_interval* seconds or
    whenever the ghost reaches its next waypoint.
    """

    def __init__(
        self,
        spaz: Spaz,
        game: 'PacManGame',
        move_speed: float = 0.8,
        repath_interval: float = 0.4,
    ) -> None:
        self._spaz_ref: weakref.ref[Spaz] = weakref.ref(spaz)
        self._game_ref: weakref.ref['PacManGame'] = weakref.ref(game)
        self._move_speed = move_speed
        self._max_correction = 0.15
        self._repath_interval = repath_interval

        # Current path: list of grid cells from ghost to target.
        self._path: list[tuple[int, int]] = []
        # Index into _path of the cell we're walking toward.
        self._path_index: int = 0
        # Last cell we confirmed we were at (to avoid re-triggering).
        self._current_cell: tuple[int, int] = (-1, -1)
        # Timer for periodic repath.
        self._repath_timer: bs.Timer | None = bs.Timer(
            repath_interval,
            babase.WeakCallStrict(self._request_repath),
            repeat=True,
        )
        self._needs_repath: bool = True

        self._timer: bs.Timer | None = bs.Timer(
            0.02, babase.WeakCallStrict(self._tick), repeat=True
        )

    def stop(self) -> None:
        self._timer = None
        self._repath_timer = None

    def set_speed(self, speed: float) -> None:
        self._move_speed = speed

    def force_repath(self) -> None:
        """Force an immediate path recalculation next tick."""
        self._needs_repath = True

    def _request_repath(self) -> None:
        """Periodic repath request."""
        self._needs_repath = True

    def _compute_path(
        self,
        gx: int,
        gz: int,
    ) -> None:
        """Ask the ghost for its target, then BFS a path to it."""
        spaz = self._spaz_ref()
        game = self._game_ref()
        if spaz is None or game is None or game._level_data is None:
            return
        if not isinstance(spaz, PacManGhost):
            return

        ld = game._level_data
        grid = ld.grid
        gw, gh = ld.grid_width, ld.grid_height

        target, allow_door = spaz.get_target_cell()
        if target is None:
            self._path = []
            self._path_index = 0
            self._needs_repath = False
            return

        # Clamp start to grid bounds.
        gx = max(0, min(gw - 1, gx))
        gz = max(0, min(gh - 1, gz))

        # If the ghost's current cell isn't walkable (physics drift
        # pushed it onto a wall), find the nearest walkable cell.
        start = (gx, gz)
        cell = grid[gz][gx] if gx < len(grid[gz]) else '#'
        if cell in ('#', 'X'):
            best = None
            best_d = 999.0
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, nz = gx + dx, gz + dy
                    if 0 <= nx < gw and 0 <= nz < gh:
                        c = grid[nz][nx]
                        if c not in ('#', 'X'):
                            if not allow_door and c == '-':
                                continue
                            d = abs(dx) + abs(dy)
                            if d < best_d:
                                best_d = d
                                best = (nx, nz)
            if best is not None:
                start = best
            else:
                self._path = []
                self._path_index = 0
                self._needs_repath = False
                return

        # Validate target — clamp to nearest walkable cell if it landed
        # on a wall.  Without this, Inky's vector math (and any other
        # targeting that produces an out-of-bounds or wall cell) causes
        # BFS to return [] every tick, spinning in an empty-path loop.
        tx, tz = target
        tx = max(0, min(gw - 1, tx))
        tz = max(0, min(gh - 1, tz))
        t_cell = grid[tz][tx] if tx < len(grid[tz]) else '#'
        if t_cell in ('#', 'X') or (t_cell == '-' and not allow_door):
            best_t = None
            best_td = 999
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, nz = tx + dx, tz + dy
                    if 0 <= nx < gw and 0 <= nz < gh:
                        c = grid[nz][nx]
                        if c in ('#', 'X'):
                            continue
                        if c == '-' and not allow_door:
                            continue
                        d = abs(dx) + abs(dy)
                        if d < best_td:
                            best_td = d
                            best_t = (nx, nz)
            if best_t is not None:
                target = best_t
            else:
                # No walkable cell near target — fall back to start.
                target = start

        path = _bfs_path(grid, start, target, gw, gh,
                         allow_door=allow_door)
        if path and len(path) >= 2:
            self._path = path
            self._path_index = 1
        elif path and len(path) == 1:
            # Already at target.
            self._path = path
            self._path_index = 0
        else:
            self._path = []
            self._path_index = 0

        self._needs_repath = False

    def _tick(self) -> None:
        spaz = self._spaz_ref()
        game = self._game_ref()
        if spaz is None or game is None or not spaz.node:
            self._timer = None
            return
        if game._level_data is None:
            return
        node = spaz.node

        try:
            pos = node.position
        except Exception:
            return

        wx, wz = pos[0], pos[2]
        gx_f, gz_f = game._world_to_grid(wx, wz)
        gx = int(round(gx_f))
        gz = int(round(gz_f))
        cx, cz = game._grid_center(gx, gz)

        cs = game._level_data.cell_size
        # Wider snap threshold so faster ghosts don't miss cell centres
        # and oscillate against walls trying to re-reach them.
        snap_threshold = cs * 0.45

        at_cell_center = (abs(wx - cx) < snap_threshold
                          and abs(wz - cz) < snap_threshold)
        cell_changed = (gx, gz) != self._current_cell

        # Update current cell tracking.
        if at_cell_center and cell_changed:
            self._current_cell = (gx, gz)

            # Notify ghost of arrival.
            if isinstance(spaz, PacManGhost):
                spaz.on_reached_cell(gx, gz)

        # ── EXITING: positional transition check ──
        # on_reached_cell requires at_cell_center which can be missed at
        # speed due to X drift.  Check every tick instead — if the ghost's
        # rounded row is at or above the door row, flip to chase immediately.
        if isinstance(spaz, PacManGhost):
            if spaz.state == GhostState.EXITING:
                door_cell = game._get_ghost_door_cell()
                if door_cell is not None and gz <= door_cell[1]:
                    spaz._enter_maze()

        # Advance path index whenever we are near the next waypoint,
        # regardless of whether cell_changed fired.  This prevents the
        # ghost from getting stuck re-trying a cell it already passed.
        if (self._path
                and self._path_index < len(self._path)):
            twx, twz = game._grid_center(*self._path[self._path_index])
            if (abs(wx - twx) < snap_threshold
                    and abs(wz - twz) < snap_threshold):
                self._path_index += 1

        # ── Recompute path when needed ──
        # This happens:
        #   - periodically (repath timer sets _needs_repath)
        #   - when we've run out of waypoints
        #   - on state changes (force_repath)
        if (self._needs_repath
                or not self._path
                or self._path_index >= len(self._path)):
            self._compute_path(gx, gz)

        # ── Steer toward next waypoint ──
        if (self._path
                and self._path_index < len(self._path)):
            target_gx, target_gz = self._path[self._path_index]
            target_wx, target_wz = game._grid_center(
                target_gx, target_gz)

            delta_x = target_wx - wx
            delta_z = target_wz - wz

            spd = self._move_speed
            if spd <= 1.0:
                move_mag = spd
                run_val = 0.0
            else:
                move_mag = 1.0
                run_val = min(1.0, (spd - 1.0) / 1.5)

            try:
                node.run = run_val
            except Exception:
                pass

            max_corr = self._max_correction
            center_dz = cs * 0.05

            if abs(delta_x) > abs(delta_z):
                lr = move_mag if delta_x > 0 else -move_mag
                node.move_left_right = lr
                off_z = wz - cz
                if abs(off_z) > center_dz:
                    corr = max(-max_corr,
                               min(max_corr, off_z * 4.0 / cs))
                    node.move_up_down = corr
                else:
                    node.move_up_down = 0.0
            elif abs(delta_z) > 0.01:
                ud = -move_mag if delta_z > 0 else move_mag
                node.move_up_down = ud
                off_x = wx - cx
                if abs(off_x) > center_dz:
                    corr = max(-max_corr,
                               min(max_corr, -off_x * 4.0))
                    node.move_left_right = corr
                else:
                    node.move_left_right = 0.0
            else:
                node.move_left_right = 0.0
                node.move_up_down = 0.0
        else:
            node.move_left_right = 0.0
            node.move_up_down = 0.0
            # Directly zero horizontal velocity so the character brakes
            # immediately rather than sliding to a stop on physics alone.
            try:
                node.run = 0.0
                node.velocity = (0.0, node.velocity[1], 0.0)
            except Exception:
                pass



# ── PacManPortal (self-contained bidirectional portal actor) ──

class PacManPortal(bs.Actor):
    """Bidirectional tunnel portal for Pac-Man's side tunnels.

    Both endpoints live inside a single instance, each with their own
    collision material — mirroring the PortalPM pattern.  A single shared
    cooldown flag prevents rapid re-triggering after either end fires.

    position1 / position2 : trigger sphere world positions (left / right).
    exit1     / exit2     : where players land after arriving from the
                            opposite end (defaults to the trigger position).
    color     / color2    : shield colours for each end (default cyan / purple).
    """

    def __init__(
        self,
        position1: tuple[float, float, float] = (0.0, 1.0, 0.0),
        position2: tuple[float, float, float] = (0.0, 1.0, 0.0),
        exit1: tuple[float, float, float] | None = None,
        exit2: tuple[float, float, float] | None = None,
        color: tuple[float, float, float] = (0.2, 3.0, 3.0),
        color2: tuple[float, float, float] | None = None,
        cell_size: float = 1.0,
        visible: bool = True,
    ) -> None:
        super().__init__()
        shared = SharedObjects.get()

        # Positions where players land — default to the opposite trigger.
        self._exit1 = exit1 if exit1 is not None else position1
        self._exit2 = exit2 if exit2 is not None else position2
        self._pos1 = position1
        self._pos2 = position2

        # Shared cooldown — one flag blocks BOTH directions.
        self.cooldown = False
        self._COOLDOWN = 1.2

        # ── Material for portal 1 (entry A → exit B) ──
        mat1 = bs.Material()
        mat1.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._on_player_1),
            ),
        )
        mat1.add_actions(
            conditions=(
                ('they_have_material', shared.object_material),
                'and',
                ('they_dont_have_material', shared.player_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._on_object_1),
            ),
        )

        # ── Material for portal 2 (entry B → exit A) ──
        mat2 = bs.Material()
        mat2.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._on_player_2),
            ),
        )
        mat2.add_actions(
            conditions=(
                ('they_have_material', shared.object_material),
                'and',
                ('they_dont_have_material', shared.player_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._on_object_2),
            ),
        )

        radius = cell_size * 0.6

        self.node1 = bs.newnode(
            'region',
            attrs={
                'position': position1,
                'scale': (0.01, 0.01, 0.01),
                'type': 'sphere',
                'materials': [mat1],
            },
        )
        bs.animate_array(self.node1, 'scale', 3, {
            0.0: (0.01, 0.01, 0.01),
            0.5: (radius, radius, radius),
        })

        self.node2 = bs.newnode(
            'region',
            attrs={
                'position': position2,
                'scale': (0.01, 0.01, 0.01),
                'type': 'sphere',
                'materials': [mat2],
            },
        )
        bs.animate_array(self.node2, 'scale', 3, {
            0.0: (0.01, 0.01, 0.01),
            0.5: (radius, radius, radius),
        })

        if visible:
            c2 = color2 if color2 is not None else (2.5, 0.2, 3.0)
            self._shield1 = bs.newnode(
                'shield',
                attrs={
                    'position': position1,
                    'color': color,
                    'radius': 1.0,
                },
            )
            bs.animate(
                self._shield1,
                'radius',
                {0.0: MIN_SPHERE_SIZE, 0.5: 1.0},
            )

            self._shield2 = bs.newnode(
                'shield',
                attrs={
                    'position': position2,
                    'color': c2,
                    'radius': 1.0,
                },
            )
            bs.animate(
                self._shield2,
                'radius',
                {0.0: MIN_SPHERE_SIZE, 0.5: 1.0},
            )

    def _set_cooldown(self) -> None:
        """Lock the portal pair for _COOLDOWN seconds."""
        self.cooldown = True

        def _off() -> None:
            self.cooldown = False

        bs.timer(self._COOLDOWN, _off)

    # ── Player handlers ──

    def _on_player_1(self) -> None:
        """Player enters portal 1 — teleport to exit 2."""
        if self.cooldown:
            return
        bs.getsound('powerup01').play()
        node = bs.getcollision().opposingnode
        self._set_cooldown()
        node.handlemessage(bs.StandMessage(position=self._exit2))

    def _on_player_2(self) -> None:
        """Player enters portal 2 — teleport to exit 1."""
        if self.cooldown:
            return
        bs.getsound('powerup01').play()
        node = bs.getcollision().opposingnode
        self._set_cooldown()
        node.handlemessage(bs.StandMessage(position=self._exit1))

    # ── Object handlers ──

    def _on_object_1(self) -> None:
        """Non-player object enters portal 1 — warp to pos2."""
        if self.cooldown:
            return
        node = bs.getcollision().opposingnode
        if node.getnodetype() == 'spaz':
            return
        v = node.velocity
        node.position = self._pos2
        self._set_cooldown()

        def _restore(n: bs.Node = node, vel: tuple = v) -> None:
            if n:
                try:
                    n.velocity = vel
                except Exception:
                    pass
        bs.timer(0.01, _restore)

    def _on_object_2(self) -> None:
        """Non-player object enters portal 2 — warp to pos1."""
        if self.cooldown:
            return
        node = bs.getcollision().opposingnode
        if node.getnodetype() == 'spaz':
            return
        v = node.velocity
        node.position = self._pos1
        self._set_cooldown()

        def _restore(n: bs.Node = node, vel: tuple = v) -> None:
            if n:
                try:
                    n.velocity = vel
                except Exception:
                    pass
        bs.timer(0.01, _restore)


# ── PacManGhost (Spaz-based ghost actor) ──

class PacManGhost(Spaz):
    """A ghost character in the Pac-Man game.

    Each ghost has a GhostType that determines its chase targeting.
    The ghost navigates the maze using BFS pathfinding and follows
    classic Pac-Man ghost AI rules.
    """

    def __init__(
        self,
        ghost_type: GhostType,
        game: 'PacManGame',
        position: tuple[float, float, float],
        move_speed: float = 0.8,
    ) -> None:
        cfg = GHOST_CONFIG[ghost_type]

        super().__init__(
            color=cfg['color'],
            highlight=cfg['highlight'],
            character=cfg['character'],
            source_player=None,
            start_invincible=False,
            can_accept_powerups=False,
            powerups_expire=False,
        )

        self.ghost_type = ghost_type
        self._game_ref: weakref.ref['PacManGame'] = weakref.ref(game)
        self._cfg = cfg
        self._base_speed = move_speed
        self.state = GhostState.IN_HOUSE
        self._frightened_timer: bs.Timer | None = None
        self._flash_timer: bs.Timer | None = None
        self._is_flashing = False

        # Make ghost immune to normal combat.
        self.hitpoints = 99999
        self.hitpoints_max = 99999

        # Place at position.
        if self.node:
            self.node.handlemessage('stand', position[0],
                                    position[1], position[2],
                                    0.0)
            # Disable combat capabilities.
            self.node.punch_pressed = False
            self.node.bomb_pressed = False
            # Hide the name tag.
            self.node.name = ''
            self.node.name_color = (0.5, 0.5, 0.5)
            # Make truly invincible at the engine level.
            try:
                self.node.invincible = True
            except Exception:
                pass


        # Create the mover.
        self.mover = GhostMover(
            self, game,
            move_speed=move_speed,
        )

        # Touch region that follows the ghost for player collision.
        self._touch_region: bs.Node | None = None
        self._touch_material: bs.Material | None = None
        self._setup_touch_region()

        # Schedule house exit.
        exit_delay = cfg['house_exit_delay']
        if exit_delay <= 0.0:
            self._begin_exit()
        else:
            self._exit_timer = bs.Timer(
                exit_delay,
                babase.WeakCallStrict(self._begin_exit),
            )

    def _setup_touch_region(self) -> None:
        """Create a small region that follows the ghost for
        detecting player contact."""
        game = self._game_ref()
        if game is None or not self.node:
            return

        self._touch_material = bs.Material()
        # Use object_material (body only) not player_material (body + roller).
        # The roller is a wide cylinder at the feet and extends well beyond
        # the visible character — checking object_material means the ghost
        # must physically overlap the player's body to trigger.
        self._touch_material.add_actions(
            conditions=('they_have_material',
                        SharedObjects.get().object_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect',
                 babase.WeakCallStrict(self._on_player_contact)),
            ),
        )

        if self.node:
            self._touch_region = bs.newnode(
                'region',
                attrs={
                    'position': self.node.position,
                    'scale': (0.6, 1.2, 0.6),
                    'type': 'sphere',
                    'materials': [self._touch_material],
                },
            )
            # Follow the ghost's torso position.
            self.node.connectattr(
                'torso_position', self._touch_region, 'position'
            )

    def _on_player_contact(self) -> None:
        """Called when a player touches this ghost."""
        game = self._game_ref()
        if game is None or game.has_ended():
            return
        if not self.node:
            return

        collision = bs.getcollision()
        try:
            player_node = collision.opposingnode
            spaz = player_node.getdelegate(PlayerSpaz, True)
            player = spaz.getplayer(Player, True)
        except (bs.NotFoundError, Exception):
            return

        if self.state == GhostState.FRIGHTENED:
            # Player eats the ghost!
            self._get_eaten(player)
        elif self.state in (GhostState.CHASE, GhostState.SCATTER):
            # Ghost kills the player!
            self._kill_player(spaz)

    def _kill_player(self, player_spaz: PlayerSpaz) -> None:
        """Ghost touches player in normal mode — player dies."""
        if player_spaz.node:
            try:
                if player_spaz.node.invincible:
                    return
            except Exception:
                pass
            player_spaz.handlemessage(bs.DieMessage())

    def _get_eaten(self, player: 'Player') -> None:
        """Player eats this frightened ghost."""
        game = self._game_ref()
        if game is None:
            return

        # Award points.
        points = 50
        player.team.score += points
        game.stats.player_scored(
            player, points, screenmessage=True, display=True
        )
        game._update_scoreboard()

        # Play sound.
        bs.getsound('shieldHit').play(1.0, position=self.node.position)

        # Switch to eaten state.
        self.state = GhostState.EATEN
        self._frightened_timer = None
        self._flash_timer = None
        self._is_flashing = False

        # Visual: dim and semi-transparent.
        if self.node:
            self.node.color = _EATEN_COLOR
            self.node.highlight = _EATEN_COLOR
            try:
                self.node.name_color = (0.3, 0.3, 0.3)
            except Exception:
                pass

        # Speed up — rush back to ghost house.
        self.mover.set_speed(self._base_speed * 2.0)
        self.mover.force_repath()

    def _begin_exit(self) -> None:
        """Start exiting the ghost house."""
        self.state = GhostState.EXITING
        game = self._game_ref()
        if game is None:
            return

        # Force repath — get_target_cell will return above-door cell.
        self.mover.force_repath()

        # _enter_maze is now triggered by on_reached_cell once the ghost
        # physically clears the door, NOT by a fixed timer. This prevents
        # ghosts from flipping to CHASE while still inside the house.

    def _enter_maze(self) -> None:
        """Ghost has exited the house — start chasing."""
        game = self._game_ref()
        if game is None:
            return
        # Match the current wave state.
        wave_state = game._current_wave_state
        if wave_state in (GhostState.CHASE, GhostState.SCATTER):
            self.state = wave_state
        else:
            self.state = GhostState.CHASE
        self.mover.set_speed(self._base_speed)
        self.mover.force_repath()
        self._update_appearance()

    def set_frightened(self) -> None:
        """Called when a power pellet is collected."""
        if self.state in (GhostState.IN_HOUSE, GhostState.EXITING,
                          GhostState.EATEN):
            return  # Don't frighten ghosts not yet in the maze.

        self.state = GhostState.FRIGHTENED
        self._is_flashing = False
        self.mover.set_speed(self._base_speed * 0.5)

        # Force immediate repath so ghost picks a flee target.
        self.mover.force_repath()

        self._update_appearance()

        # Frightened timer.
        self._frightened_timer = bs.Timer(
            _FRIGHTENED_DURATION,
            babase.WeakCallStrict(self._end_frightened),
        )
        # Start flashing near the end.
        flash_start = max(0.0, _FRIGHTENED_DURATION - _FRIGHTENED_FLASH_TIME)
        self._flash_timer = bs.Timer(
            flash_start,
            babase.WeakCallStrict(self._start_flash),
        )

    def _start_flash(self) -> None:
        """Begin flashing between fright and normal colors."""
        if self.state != GhostState.FRIGHTENED:
            return
        self._is_flashing = True
        self._do_flash_tick()

    def _do_flash_tick(self) -> None:
        if self.state != GhostState.FRIGHTENED or not self.node:
            return
        # Toggle between blazing-blue fright color and blinding white flash.
        if self.node.color == _FRIGHT_COLOR:
            self.node.color = _FRIGHT_FLASH_COLOR
            self.node.highlight = _FRIGHT_FLASH_HIGHLIGHT
        else:
            self.node.color = _FRIGHT_COLOR
            self.node.highlight = _FRIGHT_HIGHLIGHT
        bs.timer(0.25, babase.WeakCallStrict(self._do_flash_tick))

    def _end_frightened(self) -> None:
        """Frightened period ends — return to normal."""
        if self.state != GhostState.FRIGHTENED:
            return
        self._frightened_timer = None
        self._flash_timer = None
        self._is_flashing = False
        game = self._game_ref()
        if game is not None:
            self.state = game._current_wave_state
        else:
            self.state = GhostState.CHASE
        self.mover.set_speed(self._base_speed)
        self.mover.force_repath()
        self._update_appearance()

    def _update_appearance(self) -> None:
        """Set ghost color based on current state."""
        if not self.node:
            return
        if self.state == GhostState.FRIGHTENED:
            self.node.color = _FRIGHT_COLOR
            self.node.highlight = _FRIGHT_HIGHLIGHT
        elif self.state == GhostState.EATEN:
            self.node.color = _EATEN_COLOR
            self.node.highlight = _EATEN_COLOR
        else:
            self.node.color = self._cfg['color']
            self.node.highlight = self._cfg['highlight']

    def _respawn_in_house(self) -> None:
        """Eaten ghost arrives back at house — respawn."""
        self.state = GhostState.IN_HOUSE
        self.mover.set_speed(self._base_speed)
        if self.node:
            self.node.color = self._cfg['color']
            self.node.highlight = self._cfg['highlight']
            try:
                self.node.name_color = (0.5, 0.5, 0.5)
            except Exception:
                pass
        # Re-exit after a short delay.
        bs.timer(2.0, babase.WeakCallStrict(self._begin_exit))

    def on_reached_cell(self, gx: int, gz: int) -> None:
        """Called by GhostMover when the ghost arrives at a cell center."""
        game = self._game_ref()
        if game is None:
            return

        if self.state == GhostState.EATEN:
            house = game._get_ghost_house_center()
            if house is not None and (gx, gz) == house:
                self._respawn_in_house()

        elif self.state == GhostState.EXITING:
            # Trigger _enter_maze once the ghost physically clears the
            # door row — position-based, not a fixed timer, so Zoe and
            # other slow-exit ghosts can't flip to CHASE mid-tunnel.
            door = game._get_ghost_door_cell()
            if door is not None and gz <= door[1]:
                self._enter_maze()

    def get_target_cell(
        self,
    ) -> tuple[tuple[int, int] | None, bool]:
        """Return (target_cell, allow_door) for the GhostMover's BFS.

        The mover will compute the full shortest path to this cell
        and walk the ghost along it one tile at a time.
        """
        game = self._game_ref()
        if game is None or game._level_data is None:
            return (None, False)

        ld = game._level_data
        gw, gh = ld.grid_width, ld.grid_height

        # ── EATEN: return to ghost house (through door) ──
        if self.state == GhostState.EATEN:
            house = game._get_ghost_house_center()
            return (house, True)

        # ── IN_HOUSE: bounce between house cells while waiting to exit ──
        # Do NOT target the door — that causes ghosts to walk out early and
        # then stand idle when _begin_exit eventually fires.
        if self.state == GhostState.IN_HOUSE:
            my_cell = self._get_my_cell(game)
            door = game._get_ghost_door_cell()
            # Collect walkable cells inside the house (below the door row).
            house_cells: list[tuple[int, int]] = []
            if door is not None:
                for gy in range(door[1] + 1, ld.grid_height):
                    for gx in range(gw):
                        c = ld.grid[gy][gx]
                        if c not in ('#', 'X', '-'):
                            if my_cell is None or (gx, gy) != my_cell:
                                house_cells.append((gx, gy))
            if house_cells:
                return (random.choice(house_cells), True)
            # Fallback: stay where we are.
            return (my_cell, True)

        # ── EXITING: head for the cell above the door ──
        if self.state == GhostState.EXITING:
            door = game._get_ghost_door_cell()
            if door is not None:
                # Safety net: already outside → transition immediately.
                my_cell = self._get_my_cell(game)
                if my_cell is not None and my_cell[1] <= door[1]:
                    self._enter_maze()
                    return (self._get_ai_target(game), False)
                above = (door[0], max(0, door[1] - 1))
                return (above, True)
            return (None, True)

        # ── FRIGHTENED: pick a random walkable cell ──
        if self.state == GhostState.FRIGHTENED:
            # Run away from nearest player.
            my_cell = self._get_my_cell(game)
            if my_cell is None:
                return (None, False)
            player_cell, _ = game._get_nearest_player_cell(
                my_cell[0], my_cell[1])
            if player_cell is not None:
                # Pick the corner farthest from the player.
                best_corner = None
                best_dist = -1.0
                for corner in [(1, 1), (gw - 2, 1),
                               (1, gh - 2), (gw - 2, gh - 2)]:
                    d = abs(corner[0] - player_cell[0]) + abs(
                        corner[1] - player_cell[1])
                    if d > best_dist:
                        best_dist = d
                        best_corner = corner
                return (best_corner, False)
            # No player to flee from — wander randomly.
            return (self._get_wander_target(game), False)

        # ── CHASE or SCATTER ──
        return (self._get_ai_target(game), False)

    def _get_my_cell(
        self, game: 'PacManGame'
    ) -> tuple[int, int] | None:
        """Get this ghost's current grid cell."""
        if not self.node:
            return None
        try:
            pos = self.node.position
            gxf, gzf = game._world_to_grid(pos[0], pos[2])
            return (int(round(gxf)), int(round(gzf)))
        except Exception:
            return None

    def _get_wander_target(
        self, game: 'PacManGame'
    ) -> tuple[int, int] | None:
        """Pick a distant junction cell to wander toward.

        Junctions (3+ open neighbours) give the ghost a meaningful path
        rather than a 1-step hop.  Only scans junction cells (typically
        ~20-30 in the classic layout) instead of all 400+ walkable cells,
        so this is cheap to call every repath.

        Minimum Manhattan distance of 6 ensures the ghost walks for a
        while before needing to pick again — eliminates micro-stutter
        from constantly re-wandering to nearby cells.
        """
        ld = game._level_data
        if ld is None:
            return None
        my_cell = self._get_my_cell(game)
        mx, mz = my_cell if my_cell else (0, 0)

        junctions: list[tuple[int, int]] = []
        for gy in range(ld.grid_height):
            for gx in range(ld.grid_width):
                cell = ld.grid[gy][gx]
                if cell in ('#', 'X', '-'):
                    continue
                # Count open neighbours.
                open_n = sum(
                    1 for dx, dz in [(1,0),(-1,0),(0,1),(0,-1)]
                    if game._is_ghost_path(gx + dx, gy + dz)
                )
                if open_n < 3:
                    continue
                # Must be far enough away to be worth pathing to.
                if abs(gx - mx) + abs(gy - mz) < 6:
                    continue
                junctions.append((gx, gy))

        if junctions:
            return random.choice(junctions)

        # Fallback: any walkable cell that is far enough away.
        candidates = [
            (gx, gy)
            for gy in range(ld.grid_height)
            for gx in range(ld.grid_width)
            if ld.grid[gy][gx] not in ('#', 'X', '-')
            and abs(gx - mx) + abs(gy - mz) >= 4
        ]
        return random.choice(candidates) if candidates else None

    def _get_ai_target(
        self, game: 'PacManGame'
    ) -> tuple[int, int] | None:
        """Compute the target cell based on ghost type and state."""
        ld = game._level_data
        if ld is None:
            return None
        gw, gh = ld.grid_width, ld.grid_height

        # SCATTER: go to assigned corner.
        if self.state == GhostState.SCATTER:
            corner = self._cfg['scatter_corner']
            if corner == 'top_right':
                return (gw - 2, 1)
            elif corner == 'top_left':
                return (1, 1)
            elif corner == 'bottom_right':
                return (gw - 2, gh - 2)
            else:
                return (1, gh - 2)

        # CHASE: unique targeting per ghost type.
        my_cell = self._get_my_cell(game)
        if my_cell is None:
            return None
        mgx, mgz = my_cell

        player_cell, player_dir = game._get_nearest_player_cell(
            mgx, mgz)
        if player_cell is None:
            # No living player — wander so ghosts keep moving.
            return self._get_wander_target(game)

        px, pz = player_cell

        if self.ghost_type == GhostType.BLINKY:
            return (px, pz)

        elif self.ghost_type == GhostType.PINKY:
            if player_dir is not None and player_dir != (0, 0):
                tx = px + player_dir[0] * 4
                tz = pz + player_dir[1] * 4
                return (max(0, min(gw - 1, tx)),
                        max(0, min(gh - 1, tz)))
            return (px, pz)

        elif self.ghost_type == GhostType.INKY:
            blinky = game._get_ghost_by_type(GhostType.BLINKY)
            ahead_x = px + (player_dir[0] * 2
                            if player_dir else 0)
            ahead_z = pz + (player_dir[1] * 2
                            if player_dir else 0)
            if blinky is not None and blinky.node:
                bpos = blinky.node.position
                bgx, bgz = game._world_to_grid(bpos[0], bpos[2])
                bx, bz = int(round(bgx)), int(round(bgz))
                tx = ahead_x + (ahead_x - bx)
                tz = ahead_z + (ahead_z - bz)
                return (max(0, min(gw - 1, tx)),
                        max(0, min(gh - 1, tz)))
            return (ahead_x, ahead_z)

        elif self.ghost_type == GhostType.CLYDE:
            dist = _bfs_distance(ld.grid, (mgx, mgz), (px, pz),
                                 gw, gh)
            if dist > 8:
                return (px, pz)
            else:
                corner = self._cfg['scatter_corner']
                if corner == 'bottom_left':
                    return (1, gh - 2)
                elif corner == 'bottom_right':
                    return (gw - 2, gh - 2)
                elif corner == 'top_left':
                    return (1, 1)
                else:
                    return (gw - 2, 1)

        return (px, pz)

    def cleanup(self) -> None:
        """Stop mover and delete touch region."""
        if self.mover:
            self.mover.stop()
        self._frightened_timer = None
        self._flash_timer = None
        if self._touch_region:
            self._touch_region.delete()
            self._touch_region = None
        if self.node:
            self.handlemessage(bs.DieMessage(immediate=True))

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            # Only allow death from our own cleanup (immediate=True).
            if msg.immediate:
                return super().handlemessage(msg)
            # Ignore normal combat deaths — ghosts don't die from
            # punches, bombs, or falling.
            return None
        if isinstance(msg, bs.HitMessage):
            # Ignore all hit/damage messages. Ghosts are invulnerable
            # to normal attacks.
            return None
        if isinstance(msg, bs.FreezeMessage):
            return None
        return super().handlemessage(msg)




# ═══════════════════════════════════════════════════════════════════
# PLAYER / TEAM
# ═══════════════════════════════════════════════════════════════════

class Icon(bs.Actor):
    """Player icon with name and lives count shown at the bottom of screen."""

    def __init__(
        self,
        player: 'Player',
        position: tuple[float, float],
        scale: float,
        *,
        show_lives: bool = True,
        show_death: bool = True,
        name_scale: float = 1.0,
        name_maxwidth: float = 115.0,
        flatness: float = 1.0,
        shadow: float = 1.0,
    ):
        super().__init__()

        self._player = weakref.ref(player)
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._outline_tex = bs.gettexture('characterIconMask')

        icon = player.get_icon()
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'vr_depth': 400,
                'tint2_color': icon['tint2_color'],
                'mask_texture': self._outline_tex,
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'bottomCenter',
            },
        )
        self._name_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': bs.Lstr(value=player.getname()),
                'color': bs.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        if self._show_lives:
            self._lives_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': 'x0',
                    'color': (1, 1, 0.5),
                    'h_align': 'left',
                    'vr_depth': 430,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'h_attach': 'center',
                    'v_attach': 'bottom',
                },
            )
        self.set_position_and_scale(position, scale)

    def set_position_and_scale(
        self, position: tuple[float, float], scale: float
    ) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._name_text.scale = 1.0 * scale * self._name_scale
        if self._show_lives:
            self._lives_text.position = (
                position[0] + scale * 10.0,
                position[1] - scale * 43.0,
            )
            self._lives_text.scale = 1.0 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        player = self._player()
        lives = player.lives if player else 0
        if self._show_lives:
            if lives > 0:
                self._lives_text.text = 'x' + str(lives - 1)
            else:
                self._lives_text.text = ''
        if lives == 0:
            self._name_text.opacity = 0.2
            assert self.node
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2

    def handle_player_spawned(self) -> None:
        """Our player spawned; hooray!"""
        if not self.node:
            return
        self.node.opacity = 1.0
        self.update_for_lives()

    def handle_player_died(self) -> None:
        """Our player died."""
        if not self.node:
            return
        if self._show_death:
            bs.animate(
                self.node,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 1.0,
                    0.55: 0.2,
                },
            )
            player = self._player()
            lives = player.lives if player else 0
            if lives == 0:
                bs.timer(0.6, self.update_for_lives)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            return None
        return super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.lives = 0
        self.icons: list[Icon] = []
        self.respawn_timer: bs.Timer | None = None
        self.respawn_icon: RespawnIcon | None = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0



# ═══════════════════════════════════════════════════════════════════
# GAME MODE
# ═══════════════════════════════════════════════════════════════════

# ba_meta export bascenev1.GameActivity
class PacManGame(bs.TeamGameActivity[Player, Team]):
    """Collect dots in a maze! Based on Easter Egg Hunt with lives."""

    name = 'Pac-Man'
    description = 'Collect all the dots!'
    announce_player_deaths = True

    scoreconfig = bs.ScoreConfig(
        label='Score', scoretype=bs.ScoreType.POINTS
    )

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        return [
            bs.IntSetting(
                'Lives Per Player',
                min_value=1,
                default=3,
                max_value=10,
                increment=1,
            ),
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('3 Minutes', 180),
                    ('5 Minutes', 300),
                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Walls',
                choices=[
                    ('Regular', 0),
                    ('Flat', 1),
                    ('Invisible', 2),
                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Wall Color',
                choices=[
                    ('Classic Blue',    0),
                    ('Pac-Man Pink',    1),
                    ('Ghost White',     2),
                    ('Cherry Red',      3),
                    ('Lime Green',      4),
                    ('Tangerine',       5),
                    ('Galaga Yellow',   6),
                    ('Cyan',           7),
                    ('Deep Purple',     8),
                    ('Neon Magenta',    9),
                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Path Color',
                choices=[
                    ('None',            0),
                    ('Dark Blue',       1),
                    ('Dark Pink',       2),
                    ('Dark Green',      3),
                    ('Dark Red',        4),
                    ('Dark Purple',     5),
                    ('Charcoal',        6),
                ],
                default=0,
            ),
            bs.BoolSetting('Player Collisions', default=False),
            bs.BoolSetting('Ghost Collisions', default=False),
            bs.BoolSetting('Enable Ghosts', default=True),
            bs.FloatChoiceSetting(
                'Ghost Speed',
                choices=[
                    ('0.5', 0.5), ('0.6', 0.6), ('0.7', 0.7),
                    ('0.8', 0.8), ('0.9', 0.9), ('1.0', 1.0),
                    ('1.1', 1.1), ('1.2', 1.2), ('1.3', 1.3),
                    ('1.4', 1.4), ('1.5', 1.5),
                ],
                default=0.8,
            ),
            bs.BoolSetting('Show Path Grid', default=False),
            bs.BoolSetting('Epic Mode', default=False),
        ]

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Pac-Man Arena']

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()

        self._scoreboard = Scoreboard()
        self._lives_per_player = int(settings.get('Lives Per Player', 3))
        self._time_limit = float(settings.get('Time Limit', 0))
        self._wall_style = int(settings.get('Walls', 0))

        _wall_colors: dict[int, tuple[float, float, float]] = {
            0: (0.15, 0.25, 0.9),   # Classic Blue
            1: (0.9,  0.15, 0.55),  # Pac-Man Pink
            2: (0.9,  0.9,  0.9),   # Ghost White
            3: (0.9,  0.08, 0.08),  # Cherry Red
            4: (0.1,  0.85, 0.15),  # Lime Green
            5: (0.95, 0.45, 0.05),  # Tangerine
            6: (0.95, 0.85, 0.05),  # Galaga Yellow
            7: (0.05, 0.85, 0.9),   # Cyan
            8: (0.35, 0.05, 0.75),  # Deep Purple
            9: (0.95, 0.05, 0.85),  # Neon Magenta
        }
        _path_colors: dict[int, tuple[float, float, float] | None] = {
            0: None,                 # None (no path tile)
            1: (0.03, 0.05, 0.18),  # Dark Blue
            2: (0.18, 0.03, 0.10),  # Dark Pink
            3: (0.03, 0.16, 0.04),  # Dark Green
            4: (0.16, 0.03, 0.03),  # Dark Red
            5: (0.10, 0.03, 0.18),  # Dark Purple
            6: (0.08, 0.08, 0.08),  # Charcoal
        }
        self._wall_color: tuple[float, float, float] = _wall_colors.get(
            int(settings.get('Wall Color', 0)), _wall_colors[0]
        )
        self._path_color: tuple[float, float, float] | None = _path_colors.get(
            int(settings.get('Path Color', 0)), None
        )
        self._player_collisions = bool(
            settings.get('Player Collisions', False)
        )
        self._ghost_collisions = bool(
            settings.get('Ghost Collisions', False)
        )
        self._enable_ghosts = bool(settings.get('Enable Ghosts', True))
        self._ghost_speed = float(settings.get('Ghost Speed', 0.8))
        self._show_path_grid = bool(settings.get('Show Path Grid', False))
        self._epic_mode = bool(settings.get('Epic Mode', False))

        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC
            if self._epic_mode
            else bs.MusicType.FORWARD_MARCH
        )

        # Material for dot collection detection.
        # Must enable collision (non-physical) for the callback to fire.
        self._dot_material = bs.Material()
        self._dot_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._on_dot_player_collide),
            ),
        )

        self._collect_sound = bs.getsound('powerup01')
        self._power_sound = bs.getsound('powerup01')
        self._level_data: LevelData | None = None

        # Ghost identifier material — empty, used purely so the
        # ghost door can detect "this is a ghost" and not collide.
        self._ghost_id_material = bs.Material()

        # Ghost no-collide material.
        # Ghosts ALWAYS phase through each other (ghost_id rule).
        # Ghosts phase through players only when Ghost Collisions is off.
        # Kill/eat detection is via the touch region, so this is safe.
        self._ghost_no_collide_material = bs.Material()
        # Always: phase through other ghosts.
        self._ghost_no_collide_material.add_actions(
            conditions=('they_have_material', self._ghost_id_material),
            actions=('modify_part_collision', 'collide', False),
        )
        # Conditional: phase through players.
        if not self._ghost_collisions:
            self._ghost_no_collide_material.add_actions(
                conditions=(
                    'they_have_material', shared.player_material
                ),
                actions=('modify_part_collision', 'collide', False),
            )

        # Player no-collide material — applied when Player Collisions is off.
        # Makes players phase through each other physically.
        # Touch region and dot collection are unaffected.
        self._player_no_collide_material = bs.Material()
        if not self._player_collisions:
            self._player_no_collide_material.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=('modify_part_collision', 'collide', False),
            )

        # Portals are self-contained PacManPortal actors (one per direction).
        # No shared material needed here — each portal makes its own.
        self._portals: list[PacManPortal] = []

        # Ghost door material — blocks players but not ghosts.
        self._ghost_door_material = bs.Material()
        self._ghost_door_material.add_actions(
            conditions=('they_dont_have_material',
                        self._ghost_id_material),
            actions=('modify_part_collision', 'collide', True),
        )
        self._ghost_door_region: bs.Node | None = None
        self._ghost_door_visual: bs.Node | None = None

        # Map dots by their region node for fast lookup on collision.
        self._dot_regions: dict[bs.Node, DotActor] = {}

        # ── Ghost management ──
        self._ghosts: list[PacManGhost] = []
        self._current_wave_state: GhostState = GhostState.SCATTER
        self._wave_index: int = 0
        self._wave_timer: bs.Timer | None = None

    @override
    def get_instance_description(self) -> str | Sequence:
        return 'Collect all the dots!'

    @override
    def get_instance_description_short(self) -> str | Sequence:
        return 'collect the dots'

    @override
    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    @override
    def on_player_join(self, player: Player) -> None:
        player.lives = self._lives_per_player
        player.icons = [Icon(player, position=(0, 50), scale=0.8)]
        if self.has_begun():
            self.spawn_player(player)
            self._update_icons()

    @override
    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        player.icons = []
        bs.timer(0, self._update_icons)

    @override
    def on_begin(self) -> None:
        super().on_begin()

        # Pick layout based on setting.
        layout = CLASSIC_LAYOUT
        cell_size = 1.0

        # Arena offset: fixed height of -10.
        arena_offset = (0.0, -10.0, 0.0)

        # Build the maze.
        builder = PacManLevelBuilder(
            layout=layout,
            cell_size=cell_size,
            wall_height=2.4,
            wall_color=self._wall_color,
            wall_opacity=0.7,
            dot_color=(1.0, 1.0, 0.6),
            power_pellet_color=(1.0, 0.5, 0.1),
            floor_y=0.0,
            origin_offset=arena_offset,
            dot_material=self._dot_material,
            optimized_wireframe=True,
            wall_style=self._wall_style,
            path_color=self._path_color,
        )
        self._level_data = builder.generate()

        # Resize the map's floor to match the maze, at the offset.
        gamemap = self.map
        cs = self._level_data.cell_size
        floor_w = self._level_data.width * cs
        floor_d = self._level_data.height * cs
        if (
            hasattr(gamemap, 'set_floor_size')
            and hasattr(gamemap, 'update_defs_for_spawns')
        ):
            gamemap.set_floor_size(floor_w, floor_d, offset=arena_offset)
            # Push spawn points from the level into the map.
            gamemap.update_defs_for_spawns(self._level_data.player_spawns)
        else:
            babase.print_error(
                'Pac-Man Arena map API not available on active map; '
                'continuing without dynamic floor/spawn updates.'
            )
            if not _PACMAN_ARENA_IMPORT_OK:
                babase.print_error(
                    'Could not import pacman_arena map module. '
                    'Expected at mods/maps/pacman_arena.py.'
                )

        # Set camera area-of-interest so the camera frames the maze.
        gnode = self.globalsnode
        aoi = builder.get_area_of_interest()
        gnode.area_of_interest_bounds = aoi

        # Build region→dot lookup for collision handling.
        for dot in self._level_data.dots:
            self._dot_regions[dot.region_node] = dot

        # Build ghost door wall — white barrier blocking the ghost
        # house entrance. Scans grid for GHOST_DOOR cells.
        self._create_ghost_door_wall(cs, arena_offset)

        # Setup time limit if any.
        if self._time_limit > 0:
            self.setup_standard_time_limit(self._time_limit)

        # Spawn players.
        for player in self.players:
            if player.lives > 0:
                self.spawn_player(player)

        self._update_scoreboard()
        self._update_icons()

        # Periodic check for game-over (all dots collected).
        bs.timer(1.0, self._check_end, repeat=True)

        # Show path grid: red locator squares on every walkable cell.
        if self._show_path_grid and self._level_data:
            ld = self._level_data
            floor_top = 0.5 + arena_offset[1]
            path_y = floor_top + 0.05  # Just above floor surface.
            for gy in range(ld.grid_height):
                for gx in range(ld.grid_width):
                    if self._is_path(gx, gy):
                        pcx, pcz = self._grid_center(gx, gy)
                        bs.newnode(
                            'locator',
                            attrs={
                                'shape': 'box',
                                'position': (pcx, path_y, pcz),
                                'size': (cs * 0.9, 0.05, cs * 0.9),
                                'color': (1.0, 0.15, 0.15),
                                'opacity': 0.5,
                                'draw_beauty': True,
                                'additive': True,
                            },
                        )

        # ── Spawn ghosts ──
        if self._enable_ghosts and self._level_data:
            self._spawn_ghosts()
            self._start_wave_timer()

        # ── Set up tunnel portals ──
        self._setup_portals()

    def _setup_portals(self) -> None:
        """Spawn one self-contained PacManPortal per tunnel pair.

        Each instance manages both endpoints — entering either end
        teleports the player to the opposite exit.  A single shared
        cooldown flag prevents the player from being bounced straight back.
        """
        ld = self._level_data
        if ld is None or not ld.tunnel_pairs:
            return

        cs = ld.cell_size
        floor_top = 0.5 + ld.origin_offset[1]
        p_off = 0.0

        portal_y = floor_top + 1.0 + p_off
        exit_y = floor_top + 1.5 + p_off

        # Portals are always invisible (shields hidden)

        for left_cell, right_cell in ld.tunnel_pairs:
            lx, lz = self._grid_center(*left_cell)
            rx, rz = self._grid_center(*right_cell)

            exit_lx = lx + cs   # one cell right of the left portal
            exit_rx = rx - cs   # one cell left of the right portal

            portal = PacManPortal(
                position1=(lx, portal_y, lz),
                position2=(rx, portal_y, rz),
                exit1=(exit_lx, exit_y, lz),
                exit2=(exit_rx, exit_y, rz),
                color=(0.2, 3.0, 3.0),
                color2=(2.5, 0.2, 3.0),
                cell_size=cs,
                visible=False,
            )
            self._portals.append(portal)

    def _spawn_ghosts(self) -> None:
        """Spawn all four ghost types inside the ghost house."""
        ld = self._level_data
        if ld is None:
            return

        house_center = self._get_ghost_house_center()
        door_cell = self._get_ghost_door_cell()
        if house_center is None:
            return

        floor_top = 0.5 + ld.origin_offset[1]
        spawn_y = floor_top + 1.5

        # Find all door cells to get door column range.
        all_doors: list[tuple[int, int]] = []
        for gy in range(ld.grid_height):
            for gx in range(ld.grid_width):
                if ld.grid[gy][gx] == GHOST_DOOR:
                    all_doors.append((gx, gy))

        if all_doors:
            door_cx = sum(c[0] for c in all_doors) / len(all_doors)
            door_row = all_doors[0][1]
        elif door_cell is not None:
            door_cx = float(door_cell[0])
            door_row = door_cell[1]
        else:
            door_cx = float(house_center[0])
            door_row = house_center[1] - 1

        # Collect walkable EMPTY cells inside the house (near the door).
        house_cells: list[tuple[int, int]] = []
        for gy in range(door_row + 1,
                        min(door_row + 3, ld.grid_height)):
            for gx in range(ld.grid_width):
                if ld.grid[gy][gx] == EMPTY:
                    if abs(gx - door_cx) <= 3:
                        house_cells.append((gx, gy))

        # Fallback if no house cells found.
        if not house_cells:
            house_cells = [house_center]

        for i, gtype in enumerate(GhostType):
            # Blinky spawns outside the house (one cell above the door).
            if gtype == GhostType.BLINKY and door_cell is not None:
                sg = (door_cell[0], door_cell[1] - 1)
            else:
                # Other ghosts get a house cell (cycle through list).
                idx = (i - 1) % max(1, len(house_cells))
                sg = house_cells[idx]

            sx, sz = self._grid_center(sg[0], sg[1])

            ghost = PacManGhost(
                ghost_type=gtype,
                game=self,
                position=(sx, spawn_y, sz),
                move_speed=self._ghost_speed,
            )
            # Tag ghost so the door region ignores it, and so ghosts
            # phase through each other and the player physically.
            # Applied to ALL node material slots — previously only 2 of 5
            # were covered, allowing rollers and extras to still bump.
            if ghost.node:
                try:
                    for slot in ['materials', 'roller_materials',
                                 'extras_material', 'punch_materials',
                                 'pickup_materials']:
                        mats = list(getattr(ghost.node, slot))
                        mats.append(self._ghost_id_material)
                        mats.append(self._ghost_no_collide_material)
                        setattr(ghost.node, slot, mats)
                except Exception:
                    pass
            self._ghosts.append(ghost)

    def _start_wave_timer(self) -> None:
        """Start the scatter/chase wave alternation."""
        self._wave_index = 0
        if not _WAVE_PATTERN:
            return
        state, duration = _WAVE_PATTERN[0]
        self._current_wave_state = state
        self._wave_timer = bs.Timer(
            duration,
            babase.WeakCallStrict(self._advance_wave),
        )

    def _advance_wave(self) -> None:
        """Move to the next scatter/chase wave phase."""
        self._wave_index += 1
        if self._wave_index >= len(_WAVE_PATTERN):
            self._current_wave_state = GhostState.CHASE
            return
        state, duration = _WAVE_PATTERN[self._wave_index]
        self._current_wave_state = state
        # Update all active ghosts.
        for ghost in self._ghosts:
            if ghost.state in (GhostState.CHASE, GhostState.SCATTER):
                ghost.state = state
                ghost._update_appearance()
                ghost.mover.force_repath()
        self._wave_timer = bs.Timer(
            duration,
            babase.WeakCallStrict(self._advance_wave),
        )

    def _apply_spawn_invincibility(self, spaz: 'PlayerSpaz',
                                     duration: float = 3.0) -> None:
        """Make spaz invincible for duration seconds, then clear it."""
        if not spaz.node:
            return
        try:
            spaz.node.invincible = True
        except Exception:
            return
        def _clear(node: bs.Node = spaz.node) -> None:
            if node:
                try:
                    node.invincible = False
                except Exception:
                    pass
        bs.timer(duration, _clear)

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        # Spawn at a player-spawn from the level data, or map default.
        pos: tuple[float, float, float] | None = None
        if self._level_data and self._level_data.player_spawns:
            pos = random.choice(self._level_data.player_spawns)
            spaz = self.spawn_player_spaz(player, position=pos)
        else:
            spaz = self.spawn_player_spaz(player)

        # Override the default 1s invincibility with a 4s window.
        self._apply_spawn_invincibility(spaz, duration=4.0)

        # Notify icons that this player has spawned.
        for icon in player.icons:
            icon.handle_player_spawned()

        # Apply player no-collide material to all relevant node slots so
        # players phase through each other when Player Collisions is off.
        if not self._player_collisions and spaz.node:
            try:
                for slot in ['materials', 'roller_materials',
                             'extras_material']:
                    mats = list(getattr(spaz.node, slot))
                    mats.append(self._player_no_collide_material)
                    setattr(spaz.node, slot, mats)
            except Exception:
                pass

        return spaz

    # ── Grid helpers ──

    def _get_grid_cell(self, gx: int, gy: int) -> str:
        """Return the cell character at grid (gx, gy)."""
        ld = self._level_data
        if ld is None:
            return ' '
        if 0 <= gy < ld.grid_height and 0 <= gx < ld.grid_width:
            return ld.grid[gy][gx]
        return ' '

    def _is_path(self, gx: int, gy: int) -> bool:
        """True if (gx, gy) is a walkable path cell.
        Out-of-bounds, wall, void, and ghost door cells are not walkable.
        Interior empty spaces (tunnels, ghost house) ARE walkable."""
        ld = self._level_data
        if ld is None:
            return False
        if gx < 0 or gx >= ld.grid_width or gy < 0 or gy >= ld.grid_height:
            return False
        cell = ld.grid[gy][gx]
        return cell != WALL and cell != VOID and cell != GHOST_DOOR

    def _world_to_grid(
        self, wx: float, wz: float
    ) -> tuple[float, float]:
        """World (x, z) → floating-point grid (col, row)."""
        ld = self._level_data
        assert ld is not None
        cs = ld.cell_size
        gw, gh = ld.grid_width, ld.grid_height
        ox, oz = ld.origin_offset[0], ld.origin_offset[2]

        off_x = -(gw * cs) / 2.0 + cs / 2.0
        off_z = -(gh * cs) / 2.0 + cs / 2.0

        gx = (wx - ox - off_x) / cs
        gz = (wz - oz - off_z) / cs
        return (gx, gz)

    def _grid_center(
        self, gx: int, gy: int
    ) -> tuple[float, float]:
        """Grid (col, row) → world (x, z) center of that cell."""
        ld = self._level_data
        assert ld is not None
        cs = ld.cell_size
        gw, gh = ld.grid_width, ld.grid_height
        ox, oz = ld.origin_offset[0], ld.origin_offset[2]

        off_x = -(gw * cs) / 2.0 + cs / 2.0
        off_z = -(gh * cs) / 2.0 + cs / 2.0

        wx = gx * cs + off_x + ox
        wz = gy * cs + off_z + oz
        return (wx, wz)

    # ── Ghost helpers ──

    def _is_ghost_path(self, gx: int, gy: int) -> bool:
        """Like _is_path but ghosts CAN walk through the ghost door."""
        ld = self._level_data
        if ld is None:
            return False
        if gx < 0 or gx >= ld.grid_width or gy < 0 or gy >= ld.grid_height:
            return False
        cell = ld.grid[gy][gx]
        return cell != WALL and cell != VOID

    def _get_ghost_door_cell(self) -> tuple[int, int] | None:
        """Return the grid cell of the ghost door (first '-' found)."""
        ld = self._level_data
        if ld is None:
            return None
        for gy in range(ld.grid_height):
            for gx in range(ld.grid_width):
                if ld.grid[gy][gx] == GHOST_DOOR:
                    return (gx, gy)
        return None

    def _get_ghost_house_center(self) -> tuple[int, int] | None:
        """Return the center of the ghost house interior.
        Detected as EMPTY cells directly below the ghost door row
        and within a few columns of the door."""
        ld = self._level_data
        if ld is None:
            return None

        # Find ALL door cells to get the door's column range.
        door_cells: list[tuple[int, int]] = []
        for gy in range(ld.grid_height):
            for gx in range(ld.grid_width):
                if ld.grid[gy][gx] == GHOST_DOOR:
                    door_cells.append((gx, gy))

        if not door_cells:
            return None

        door_min_x = min(c[0] for c in door_cells)
        door_max_x = max(c[0] for c in door_cells)
        door_y = door_cells[0][1]
        door_center_x = (door_min_x + door_max_x) / 2.0

        # Scan rows below the door for EMPTY cells near the door.
        margin = 3  # Only count empties within ±3 cols of door center
        empty_cells: list[tuple[int, int]] = []
        for gy in range(door_y + 1, min(door_y + 4, ld.grid_height)):
            for gx in range(ld.grid_width):
                if ld.grid[gy][gx] == EMPTY:
                    if abs(gx - door_center_x) <= margin:
                        empty_cells.append((gx, gy))

        if not empty_cells:
            # Fallback: just below the door center.
            cx = int(round(door_center_x))
            return (cx, door_y + 1)

        avg_x = sum(c[0] for c in empty_cells) // len(empty_cells)
        avg_y = sum(c[1] for c in empty_cells) // len(empty_cells)
        return (avg_x, avg_y)

    def _get_nearest_player_cell(
        self, gx: int, gz: int
    ) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        """Return (cell, direction) of the nearest living player."""
        best_cell: tuple[int, int] | None = None
        best_dir: tuple[int, int] | None = None
        best_dist = 99999.0

        for team in self.teams:
            for player in team.players:
                if not player.is_alive():
                    continue
                try:
                    actor = player.actor
                    if actor is None or not actor.node:
                        continue
                    pos = actor.node.position
                    pgx_f, pgz_f = self._world_to_grid(pos[0], pos[2])
                    pgx, pgz = int(round(pgx_f)), int(round(pgz_f))
                    dist = abs(pgx - gx) + abs(pgz - gz)
                    if dist < best_dist:
                        best_dist = dist
                        best_cell = (pgx, pgz)
                        best_dir = (0, 0)
                except Exception:
                    continue

        return best_cell, best_dir

    def _get_ghost_by_type(
        self, gtype: GhostType
    ) -> PacManGhost | None:
        """Find a living ghost by type (used for Inky's targeting)."""
        for ghost in self._ghosts:
            if ghost.ghost_type == gtype and ghost.node:
                return ghost
        return None

    def _frighten_all_ghosts(self) -> None:
        """Called when a power pellet is collected."""
        for ghost in self._ghosts:
            ghost.set_frightened()

    def _create_ghost_door_wall(
        self, cs: float, arena_offset: tuple[float, float, float]
    ) -> None:
        """Create a white wall blocking the ghost house door."""
        ld = self._level_data
        if ld is None:
            return

        # Find all GHOST_DOOR cells in the grid.
        door_cells: list[tuple[int, int]] = []
        for gy in range(ld.grid_height):
            for gx in range(ld.grid_width):
                if ld.grid[gy][gx] == GHOST_DOOR:
                    door_cells.append((gx, gy))

        if not door_cells:
            return

        # Compute bounding box of door cells in world coords.
        xs = []
        zs = []
        for gx, gy in door_cells:
            wx, wz = self._grid_center(gx, gy)
            xs.append(wx)
            zs.append(wz)

        center_x = (min(xs) + max(xs)) / 2.0
        center_z = (min(zs) + max(zs)) / 2.0

        # Width covers all door cells, depth is 0.5 cubes.
        wall_w = len(door_cells) * cs
        wall_d = cs * 0.5
        wall_h = cs  # Same visual height as wall cubes.

        # Flush with outer face: shift toward lower Z (outside).
        # The surrounding row walls are centered at center_z with
        # size cs. Outer face = center_z - cs/2.
        # Our wall (depth wall_d) outer face should match:
        # wall_center_z - wall_d/2 = center_z - cs/2
        # wall_center_z = center_z - cs/2 + wall_d/2
        flush_z = center_z - cs / 2.0 + wall_d / 2.0

        floor_top = 0.5 + arena_offset[1]
        wall_y = floor_top + wall_h / 2.0

        shared = SharedObjects.get()

        # Collision region — blocks players but NOT ghosts.
        collision_mat = bs.Material()
        collision_mat.add_actions(
            conditions=('they_dont_have_material',
                        self._ghost_id_material),
            actions=('modify_part_collision', 'collide', True),
        )
        footing_mat = bs.Material()
        footing_mat.add_actions(
            conditions=(
                ('they_have_material', shared.footing_material),
                'and',
                ('they_dont_have_material', self._ghost_id_material),
            ),
            actions=('modify_part_collision', 'collide', True),
        )

        self._ghost_door_region = bs.newnode(
            'region',
            attrs={
                'position': (center_x, wall_y, flush_z),
                'scale': (wall_w, wall_h * 2.4, wall_d),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    collision_mat,
                    self._ghost_door_material,
                ],
            },
        )

        # Visual: white locator box (respects wall style).
        if self._wall_style != 2:  # Not Invisible
            if self._wall_style == 1:  # Flat
                vis_wall_h = wall_h * 0.15
            else:
                vis_wall_h = wall_h
            vis_wall_y = floor_top + vis_wall_h / 2.0
            self._ghost_door_visual = bs.newnode(
                'locator',
                attrs={
                    'shape': 'box',
                    'position': (center_x, vis_wall_y, flush_z),
                    'size': (wall_w, vis_wall_h, wall_d),
                    'color': (1.0, 1.0, 1.0),
                    'opacity': 0.9,
                    'draw_beauty': True,
                    'additive': False,
                },
            )

    def _on_dot_player_collide(self) -> None:
        """Called when a player touches a dot region."""
        if self.has_ended():
            return
        collision = bs.getcollision()
        try:
            src_node = collision.sourcenode
            opp_node = collision.opposingnode
            # The source is the dot region, opposing is the player.
            spaz = opp_node.getdelegate(PlayerSpaz, True)
            player = spaz.getplayer(Player, True)
        except bs.NotFoundError:
            return

        # Find which dot was hit.
        dot = self._dot_regions.get(src_node)
        if dot is None or dot.collected:
            return

        # Collect it!
        dot.collected = True
        is_pp = dot.is_power_pellet

        # Award points.
        points = 10 if is_pp else 1
        player.team.score += points
        self.stats.player_scored(
            player, points, screenmessage=False, display=False
        )
        self._update_scoreboard()

        # Play sound.
        sound = self._power_sound if is_pp else self._collect_sound
        sound.play(0.5, position=dot.locator_node.position)

        # Flash effect at dot position.
        light = bs.newnode(
            'light',
            attrs={
                'position': dot.locator_node.position,
                'height_attenuated': False,
                'radius': 0.15 if is_pp else 0.08,
                'color': (1.0, 0.5, 0.1) if is_pp else (1.0, 1.0, 0.5),
            },
        )
        bs.animate(
            light, 'intensity', {0: 0, 0.1: 1.0, 0.2: 0}, loop=False
        )
        bs.timer(0.3, light.delete)

        # Remove the dot visuals and region.
        dot.locator_node.delete()
        dot.region_node.delete()

        # Power pellet: frighten all ghosts!
        if is_pp:
            self._frighten_all_ghosts()

    def _check_end(self) -> None:
        """End game if all dots collected or all players out of lives."""
        if self.has_ended():
            return

        # Check if all dots are collected.
        if self._level_data:
            remaining = sum(
                1 for d in self._level_data.dots if not d.collected
            )
            if remaining == 0:
                self.end_game()
                return

        # Check if all players are out of lives.
        any_alive = False
        for team in self.teams:
            for player in team.players:
                if player.lives > 0:
                    any_alive = True
                    break
        if not any_alive and self.has_begun():
            bs.timer(1.5, self.end_game)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)

            # Notify icons that this player died.
            for icon in player.icons:
                icon.handle_player_died()

            player.lives -= 1

            if player.lives > 0:
                # Respawn after a delay.
                assert self.initialplayerinfos is not None
                respawn_time = 2.0
                player.respawn_timer = bs.Timer(
                    respawn_time,
                    bs.CallStrict(self.spawn_player_if_exists, player),
                )
                player.respawn_icon = RespawnIcon(player, respawn_time)
            else:
                # Out of lives — check if game should end.
                bs.timer(1.0, self._check_end)
        else:
            return super().handlemessage(msg)
        return None

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score)

    def _update_icons(self) -> None:
        """Reposition all player icons evenly along the bottom of the screen."""
        count = len(self.teams)
        x_offs = 85
        xval = x_offs * (count - 1) * -0.5
        for team in self.teams:
            if len(team.players) == 1:
                player = team.players[0]
                for icon in player.icons:
                    icon.set_position_and_scale((xval, 30), 0.7)
                    icon.update_for_lives()
                xval += x_offs

    @override
    def end_game(self) -> None:
        if self.has_ended():
            return
        # Clear node references.
        self._dot_regions.clear()
        self._ghost_door_region = None
        self._ghost_door_visual = None
        # Clean up ghosts.
        self._wave_timer = None
        for ghost in self._ghosts:
            ghost.cleanup()
        self._ghosts.clear()
        if self._level_data is not None:
            self._level_data.walls.clear()
            self._level_data.dots.clear()
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results)
