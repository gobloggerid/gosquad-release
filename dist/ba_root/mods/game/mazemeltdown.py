# ba_meta require api 9

# Updated to API9 with Claude Opus 4.6

"""Maze Meltdown — navigate a randomly generated maze before your score melts away!"""

from __future__ import annotations

import random
from collections import deque
from typing import TYPE_CHECKING, override
from dataclasses import dataclass, field

import bascenev1 as bs
import babase

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects
from maps.mazemeltdown_map import MazeRaceMap

if TYPE_CHECKING:
    from typing import Any, Sequence


# ═══════════════════════════════════════════════════════════════
#  MAZE GENERATOR
# ═══════════════════════════════════════════════════════════════

class MazeGenerator:
    _DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    def __init__(self, cols: int = 10, rows: int = 10,
                 seed: int | None = None) -> None:
        self.cols = cols
        self.rows = rows
        self._rng = random.Random(seed)
        self._carved: list[list[set[tuple[int, int]]]] = [
            [set() for _ in range(rows)] for _ in range(cols)
        ]

    def generate(self, braid: float = 0.0) -> list[str]:
        """Generate the maze, then braid it by the given factor (0.0–1.0).

        Braiding punches extra openings through dead-end walls, turning
        dead ends into intersections and creating loops.  A factor of 0.0
        is the original DFS maze; 1.0 removes every dead end.
        """
        self._carve_maze()
        if braid > 0.0:
            self._braid(braid)
        return self._to_char_grid()

    def _braid(self, factor: float) -> None:
        """Post-process: randomly open walls on dead-end cells.

        A dead-end cell has exactly one carved passage.  We find all of
        them, shuffle, then for each one (with probability = factor) punch
        through one of its remaining closed walls — preferring walls that
        lead to another dead end so two dead ends merge into a loop at once.
        """
        for cx in range(self.cols):
            for cy in range(self.rows):
                # Dead end = only one open direction.
                if len(self._carved[cx][cy]) != 1:
                    continue
                if self._rng.random() > factor:
                    continue

                # Closed neighbours we could connect to.
                closed: list[tuple[int, int, int, int]] = []
                for dx, dy in self._DIRS:
                    nx, ny = cx + dx, cy + dy
                    if (dx, dy) not in self._carved[cx][cy]:
                        if 0 <= nx < self.cols and 0 <= ny < self.rows:
                            closed.append((nx, ny, dx, dy))

                if not closed:
                    continue

                # Prefer connecting to another dead end — creates a loop
                # between two dead ends, maximising intersection gain.
                dead_end_neighbours = [
                    c for c in closed
                    if len(self._carved[c[0]][c[1]]) == 1
                ]
                candidates = dead_end_neighbours if dead_end_neighbours else closed
                nx, ny, dx, dy = self._rng.choice(candidates)
                self._carved[cx][cy].add((dx, dy))
                self._carved[nx][ny].add((-dx, -dy))

    def _carve_maze(self) -> None:
        visited = [[False] * self.rows for _ in range(self.cols)]
        stack: list[tuple[int, int]] = []
        cx, cy = 0, 0
        visited[cx][cy] = True
        stack.append((cx, cy))
        while stack:
            cx, cy = stack[-1]
            neighbors: list[tuple[int, int, int, int]] = []
            for dx, dy in self._DIRS:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if not visited[nx][ny]:
                        neighbors.append((nx, ny, dx, dy))
            if neighbors:
                nx, ny, dx, dy = self._rng.choice(neighbors)
                self._carved[cx][cy].add((dx, dy))
                self._carved[nx][ny].add((-dx, -dy))
                visited[nx][ny] = True
                stack.append((nx, ny))
            else:
                stack.pop()

    def _to_char_grid(self) -> list[str]:
        gw = 2 * self.cols + 1
        gh = 2 * self.rows + 1
        grid = [['#'] * gw for _ in range(gh)]
        for cx in range(self.cols):
            for cy in range(self.rows):
                grid[2 * cy + 1][2 * cx + 1] = ' '
                if (1, 0) in self._carved[cx][cy]:
                    grid[2 * cy + 1][2 * cx + 2] = ' '
                if (0, 1) in self._carved[cx][cy]:
                    grid[2 * cy + 2][2 * cx + 1] = ' '
        return [''.join(row) for row in grid]


# ═══════════════════════════════════════════════════════════════
#  MAZE SOLVER
# ═══════════════════════════════════════════════════════════════

def solve_maze_bfs(
    char_grid: list[str], start: tuple[int, int], end: tuple[int, int],
) -> list[tuple[int, int]]:
    gw = len(char_grid[0]) if char_grid else 0
    gh = len(char_grid)
    visited = {start}
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue: deque[tuple[int, int]] = deque([start])
    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) == end:
            break
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < gw and 0 <= ny < gh:
                if (nx, ny) not in visited and char_grid[ny][nx] != '#':
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (cx, cy)
                    queue.append((nx, ny))
    if end not in parent:
        return []
    path: list[tuple[int, int]] = []
    cur: tuple[int, int] | None = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


# ═══════════════════════════════════════════════════════════════
#  ENDPOINT SELECTION  (Outside → Outside)
# ═══════════════════════════════════════════════════════════════

def _edge_maze_cells(cols: int, rows: int) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for cx in range(cols):
        cells.add((cx, 0))
        cells.add((cx, rows - 1))
    for cy in range(rows):
        cells.add((0, cy))
        cells.add((cols - 1, cy))
    return cells


def _maze_to_char(mx: int, my: int) -> tuple[int, int]:
    return (2 * mx + 1, 2 * my + 1)


def _bfs_farthest_in_pool(
    char_grid: list[str], start: tuple[int, int],
    pool: set[tuple[int, int]],
) -> tuple[int, int] | None:
    """BFS from start; return farthest reachable cell that is in pool."""
    gw = len(char_grid[0]) if char_grid else 0
    gh = len(char_grid)
    visited = {start}
    queue: deque[tuple[int, int]] = deque([start])
    best: tuple[int, int] | None = None
    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) in pool:
            best = (cx, cy)
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < gw and 0 <= ny < gh:
                if (nx, ny) not in visited and char_grid[ny][nx] != '#':
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return best


def select_endpoints(
    char_grid: list[str], cols: int, rows: int,
    rng: random.Random,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Select start/end on opposite edges of the maze (Outside→Outside)."""
    edge_m = _edge_maze_cells(cols, rows)
    edge_c = {_maze_to_char(cx, cy) for cx, cy in edge_m}

    # Double-BFS for a well-separated edge pair.
    seed_cell = rng.choice(sorted(edge_c))
    cand_end = _bfs_farthest_in_pool(char_grid, seed_cell, edge_c)
    if cand_end is None:
        cand_end = seed_cell
    final_start = _bfs_farthest_in_pool(char_grid, cand_end, edge_c)
    if final_start is None:
        final_start = seed_cell
    final_end = _bfs_farthest_in_pool(char_grid, final_start, edge_c)
    if final_end is None:
        final_end = cand_end

    return final_start, final_end


# ═══════════════════════════════════════════════════════════════
#  WALL BUILDER
# ═══════════════════════════════════════════════════════════════

@dataclass
class MazeBuildData:
    wall_nodes: list[bs.Node] = field(default_factory=list)
    path_nodes: list[bs.Node] = field(default_factory=list)
    wall_regions: list[bs.Node] = field(default_factory=list)
    spotlight_nodes: list[
        tuple[bs.Node, int, int, float,
              tuple[float, float, float]]
    ] = field(default_factory=list)
    # (node, gx, gy, target_opacity, real_position)
    finish_region: bs.Node | None = None
    start_pos: tuple[float, float, float] = (0.0, 1.5, 0.0)
    finish_pos: tuple[float, float, float] = (0.0, 1.5, 0.0)
    optimal_moves: int = 0
    grid_width: int = 0
    grid_height: int = 0
    cell_size: float = 1.0
    char_grid: list[str] = field(default_factory=list)


class MazeBuilder:
    def __init__(
        self, char_grid: list[str], cell_size: float = 1.6,
        wall_height: float = 2.4,
        wall_color: tuple[float, float, float] = (0.3, 0.6, 1.0),
        wall_opacity: float = 0.7, floor_y: float = 0.0,
        z_offset: float = 0.0,
        wall_style: int = 0,
        path_color: tuple[float, float, float] | None = None,
        optimize_walls: bool = True,
        spotlight: bool = False,
    ) -> None:
        self._grid = char_grid
        self._gh = len(char_grid)
        self._gw = max(len(row) for row in char_grid) if char_grid else 0
        self._grid = [row.ljust(self._gw) for row in self._grid]
        self._cs = cell_size
        self._wall_h = wall_height
        self._wall_color = wall_color
        self._wall_opacity = wall_opacity
        self._floor_y = floor_y
        self._z_offset = z_offset
        self._wall_style = wall_style
        self._path_color = path_color
        self._optimize_walls = optimize_walls
        self._spotlight = spotlight

    def grid_to_world(self, gx: float, gy: float) -> tuple[float, float, float]:
        cs = self._cs
        ox = -(self._gw * cs) / 2.0 + cs / 2.0
        oz = -(self._gh * cs) / 2.0 + cs / 2.0
        return (gx * cs + ox, self._floor_y,
                gy * cs + oz + self._z_offset)

    def world_to_grid(self, wx: float, wz: float) -> tuple[int, int]:
        cs = self._cs
        ox = -(self._gw * cs) / 2.0 + cs / 2.0
        oz = -(self._gh * cs) / 2.0 + cs / 2.0
        return (round((wx - ox) / cs),
                round((wz - self._z_offset - oz) / cs))

    def _is_wall(self, gx: int, gy: int) -> bool:
        if 0 <= gy < self._gh and 0 <= gx < self._gw:
            return self._grid[gy][gx] == '#'
        return True

    def _merge_walls_2d(self) -> list[tuple[int, int, int, int]]:
        h_runs: list[tuple[int, int, int, int]] = []
        for gy in range(self._gh):
            gx = 0
            while gx < self._gw:
                if self._is_wall(gx, gy):
                    start = gx
                    while gx < self._gw and self._is_wall(gx, gy):
                        gx += 1
                    h_runs.append((start, gy, gx - start, 1))
                else:
                    gx += 1
        h_runs.sort(key=lambda r: (r[0], r[2], r[1]))
        merged: list[tuple[int, int, int, int]] = []
        used: set[int] = set()
        for i, (gx, gy, w, h) in enumerate(h_runs):
            if i in used:
                continue
            cur_h = h
            cur_end = gy + h
            for j in range(i + 1, len(h_runs)):
                if j in used:
                    continue
                ogx, ogy, ow, _ = h_runs[j]
                if ogx == gx and ow == w and ogy == cur_end:
                    cur_h += 1
                    cur_end += 1
                    used.add(j)
                elif ogx == gx and ow == w and ogy > cur_end:
                    break
            used.add(i)
            merged.append((gx, gy, w, cur_h))
        return merged

    def _individual_walls(self) -> list[tuple[int, int, int, int]]:
        """Return each wall cell as its own 1x1 rect (no merging)."""
        cells: list[tuple[int, int, int, int]] = []
        for gy in range(self._gh):
            for gx in range(self._gw):
                if self._is_wall(gx, gy):
                    cells.append((gx, gy, 1, 1))
        return cells

    def _merge_paths_2d(self) -> list[tuple[int, int, int, int]]:
        """Merge open (non-wall) cells into minimal rectangles.

        Uses the same greedy row-scan + vertical-extend algorithm as
        _merge_walls_2d, but operates on path cells instead of wall cells.
        Result: far fewer locator nodes when Optimize Nodes is enabled.
        """
        h_runs: list[tuple[int, int, int, int]] = []
        for gy in range(self._gh):
            gx = 0
            while gx < self._gw:
                if not self._is_wall(gx, gy):
                    start = gx
                    while gx < self._gw and not self._is_wall(gx, gy):
                        gx += 1
                    h_runs.append((start, gy, gx - start, 1))
                else:
                    gx += 1
        h_runs.sort(key=lambda r: (r[0], r[2], r[1]))
        merged: list[tuple[int, int, int, int]] = []
        used: set[int] = set()
        for i, (gx, gy, w, h) in enumerate(h_runs):
            if i in used:
                continue
            cur_h = h
            cur_end = gy + h
            for j in range(i + 1, len(h_runs)):
                if j in used:
                    continue
                ogx, ogy, ow, _ = h_runs[j]
                if ogx == gx and ow == w and ogy == cur_end:
                    cur_h += 1
                    cur_end += 1
                    used.add(j)
                elif ogx == gx and ow == w and ogy > cur_end:
                    break
            used.add(i)
            merged.append((gx, gy, w, cur_h))
        return merged

    def _individual_paths(self) -> list[tuple[int, int, int, int]]:
        """Return each open cell as its own 1x1 rect (no merging)."""
        cells: list[tuple[int, int, int, int]] = []
        for gy in range(self._gh):
            for gx in range(self._gw):
                if not self._is_wall(gx, gy):
                    cells.append((gx, gy, 1, 1))
        return cells

    def build(
        self, race_path: list[tuple[int, int]],
        finish_material: bs.Material,
    ) -> MazeBuildData:
        shared = SharedObjects.get()
        cs = self._cs
        data = MazeBuildData(
            grid_width=self._gw, grid_height=self._gh, cell_size=cs,
            char_grid=list(self._grid),
            optimal_moves=max(0, len(race_path) - 1),
        )
        floor_top = self._floor_y + 0.5
        vis_h = cs * 0.15 if self._wall_style == 1 else cs
        cube_cy = floor_top + vis_h / 2.0
        wall_cy = floor_top + self._wall_h / 2.0

        collision_mat = bs.Material()
        collision_mat.add_actions(
            actions=('modify_part_collision', 'collide', True))
        collision_mat.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=('modify_part_collision', 'friction', 0.0),
        )


        # In spotlight mode, force individual tiles and start hidden
        # by placing them below the floor. Position-based hiding is more
        # reliable than opacity for additive-mode locator nodes.
        use_individual = not self._optimize_walls or self._spotlight
        _HIDDEN_Y = -50.0  # far below floor

        # Wall visuals — merged or individual cubes.
        vis_rects = (self._individual_walls() if use_individual
                     else self._merge_walls_2d())
        if self._wall_style != 2:
            for gx, gy, w, h in vis_rects:
                cx, _, cz = self.grid_to_world(
                    gx + (w - 1) / 2.0, gy + (h - 1) / 2.0)
                real_pos = (cx, cube_cy, cz)
                node_pos = (_HIDDEN_Y, _HIDDEN_Y, _HIDDEN_Y) if (
                    self._spotlight and w == 1 and h == 1) else real_pos
                wn = bs.newnode('locator', attrs={
                    'shape': 'box',
                    'position': node_pos,
                    'size': (w * cs, vis_h, h * cs),
                    'color': self._wall_color,
                    'opacity': self._wall_opacity,
                    'draw_beauty': True, 'additive': True,
                })
                data.wall_nodes.append(wn)
                if self._spotlight and w == 1 and h == 1:
                    data.spotlight_nodes.append(
                        (wn, gx, gy, self._wall_opacity, real_pos))

        # Path tiles — merged rects when optimizing, individual when
        # spotlight is active (spotlight needs per-cell addressing).
        if self._path_color is not None:
            tile_y = floor_top + 0.01
            path_rects = (self._individual_paths() if use_individual
                          else self._merge_paths_2d())
            for gx, gy, w, h in path_rects:
                cx, _, cz = self.grid_to_world(
                    gx + (w - 1) / 2.0, gy + (h - 1) / 2.0)
                # Merged tiles use the full cell area; individual tiles keep
                # the small 0.95 inset so seams between cells are visible.
                tile_w = w * cs if w > 1 else cs * 0.95
                tile_d = h * cs if h > 1 else cs * 0.95
                real_pos = (cx, tile_y, cz)
                node_pos = (_HIDDEN_Y, _HIDDEN_Y, _HIDDEN_Y
                            ) if self._spotlight else real_pos
                pn = bs.newnode('locator', attrs={
                    'shape': 'box',
                    'position': node_pos,
                    'size': (tile_w, 0.02, tile_d),
                    'color': self._path_color,
                    'opacity': 1.0,
                    'draw_beauty': True, 'additive': False,
                })
                data.path_nodes.append(pn)
                if self._spotlight:
                    # Only 1x1 cells are individually addressable by spotlight.
                    data.spotlight_nodes.append(
                        (pn, gx, gy, 1.0, real_pos))

        # Wall collision.
        # Each box is shrunk by a fixed 0.05 units on X and Z only.
        # This breaks corner contact-normal ambiguity (the ODE "stuck in
        # corner" problem) while keeping gaps far smaller than the player's
        # roller radius (~0.3 units) — players cannot enter the gap.
        # Raise the wall collision box 0.25 units above floor_top.
        # This eliminates the 90-degree floor-wall junction — the concave
        # corner where the floor's upward normal and wall's horizontal normal
        # meet is what traps body parts. Below 0.25 units only the floor
        # exists, giving a single clean normal. The torso still hits the wall
        # face cleanly. The 0.05 X/Z gap still breaks corner contact ambiguity.
        # Jump is off by default so the small floor gap is unexploitable,
        # and even with jump on the body (~0.6 units) can't fit through 0.25.
        _CORNER_GAP = 0.05
        _FLOOR_LIFT = 0.25
        for gx, gy, w, h in self._merge_walls_2d():
            cx, _, cz = self.grid_to_world(
                gx + (w - 1) / 2.0, gy + (h - 1) / 2.0)
            lift_h = self._wall_h - _FLOOR_LIFT
            lift_cy = floor_top + _FLOOR_LIFT + lift_h / 2.0
            region = bs.newnode('region', attrs={
                'position': (cx, lift_cy, cz),
                'scale': (w * cs - _CORNER_GAP,
                          lift_h,
                          h * cs - _CORNER_GAP),
                'type': 'box',
                'materials': [collision_mat],
            })
            data.wall_regions.append(region)

        # Start / Finish.
        if race_path:
            sgx, sgy = race_path[0]
            sx, _, sz = self.grid_to_world(sgx, sgy)
            data.start_pos = (sx, floor_top + 1.5, sz)

            egx, egy = race_path[-1]
            ex, _, ez = self.grid_to_world(egx, egy)
            data.finish_pos = (ex, floor_top + 1.5, ez)

            # Start marker.
            bs.newnode('locator', attrs={
                'shape': 'circle',
                'position': (sx, floor_top + 0.03, sz),
                'size': (cs * 0.8,),
                'color': (1.0, 1.0, 0.0), 'opacity': 0.8,
                'draw_beauty': True, 'additive': True,
            })
            bs.newnode('text', attrs={
                'text': 'START', 'in_world': True,
                'position': (sx, floor_top + 0.1, sz),
                'color': (1.0, 1.0, 0.2, 1.0),
                'scale': 0.018, 'h_align': 'center',
            })

            # Finish marker.
            bs.newnode('locator', attrs={
                'shape': 'circle',
                'position': (ex, floor_top + 0.03, ez),
                'size': (cs * 0.8,),
                'color': (0.0, 1.0, 0.4), 'opacity': 0.8,
                'draw_beauty': True, 'additive': True,
            })
            bs.newnode('text', attrs={
                'text': 'FINISH', 'in_world': True,
                'position': (ex, floor_top + 0.1, ez),
                'color': (0.2, 1.0, 0.5, 1.0),
                'scale': 0.018, 'h_align': 'center',
            })

            # Finish region.
            data.finish_region = bs.newnode('region', attrs={
                'position': (ex, floor_top + 1.0, ez),
                'scale': (cs * 1.2, 3.0, cs * 1.2),
                'type': 'box',
                'materials': [finish_material],
            })

        return data


# ═══════════════════════════════════════════════════════════════
#  PLAYER / TEAM
# ═══════════════════════════════════════════════════════════════

class Player(bs.Player['Team']):
    def __init__(self) -> None:
        self.moves: int = 0
        self.live_score: float = 0.0
        self.last_grid_cell: tuple[int, int] | None = None
        self.visited_cells: set[tuple[int, int]] = set()
        self.finished: bool = False
        self.finish_order: int = -1
        self.rank: int | None = None
        self.move_math_node: bs.Node | None = None
        self.move_text_node: bs.Node | None = None


class Team(bs.Team[Player]):
    def __init__(self) -> None:
        self.score: int = 0
        self.time: float | None = None
        self.finished: bool = False


# ═══════════════════════════════════════════════════════════════
#  GAME
# ═══════════════════════════════════════════════════════════════

# ba_meta export bascenev1.GameActivity
class MazeRaceGame(bs.TeamGameActivity[Player, Team]):
    """Navigate from START to FINISH — keep as many points as you can!
    Every second and new move costs you! Be fast AND efficient.
    Run out of points and you're dead!"""

    name = 'Maze Meltdown'
    description = 'Navigate the maze before your score melts away!'
    # Block mid-game joins — latecomers will be queued for the next round.
    allow_mid_activity_joins = False
    scoreconfig = bs.ScoreConfig(
        label='Score', lower_is_better=False,
        scoretype=bs.ScoreType.POINTS,
    )

    @override
    @classmethod
    def get_available_settings(cls, sessiontype: type[bs.Session]) -> list[bs.Setting]:
        return [
            bs.IntChoiceSetting('Maze Size', choices=[
                (f'{n}x{n}', n) for n in range(3, 16)
            ], default=7),
            bs.IntChoiceSetting('Braid', choices=[
                ('Off',   0),
                ('25%',  25),
                ('50%',  50),
                ('75%',  75),
                ('100%', 100),
            ], default=25),
            bs.IntChoiceSetting('Maze View', choices=[
                ('Path', 0), ('Walls', 1), ('Path & Walls', 2),
            ], default=2),
            bs.IntChoiceSetting('Walls', choices=[
                ('Regular', 0), ('Flat', 1),
            ], default=1),
            bs.BoolSetting('Optimize Nodes', default=True),
            bs.IntChoiceSetting('Wall Color', choices=[
                ('Blue',  0), ('Pink',  1),
                ('White',   2), ('Red',    3),
                ('Lime',    4), ('Orange',     5),
                ('Yellow', 6), ('Cyan',          7),
                ('Purple',   8), ('Magenta',  9),
                ('Rainbow',       10),
            ], default=0),
            bs.IntChoiceSetting('Path Color', choices=[
                ('None',          99),
                ('Blue',  0), ('Pink',  1),
                ('White',   2), ('Red',    3),
                ('Lime',    4), ('Orange',     5),
                ('Yellow', 6), ('Cyan',          7),
                ('Purple',   8), ('Magenta',  9),
                ('Rainbow',       10),
            ], default=0),
            bs.FloatChoiceSetting('Cell Size', choices=[
                ('0.50', 0.50), ('0.75', 0.75), ('1.00', 1.00),
                ('1.25', 1.25), ('1.50', 1.50), ('1.75', 1.75),
                ('2.00', 2.00), ('2.25', 2.25), ('2.50', 2.50),
            ], default=0.75),
            bs.BoolSetting('Player Collisions', default=False),
            bs.BoolSetting('Enable Punch', default=False),
            bs.BoolSetting('Enable Bomb', default=False),
            bs.BoolSetting('Enable Jump', default=False),
            bs.BoolSetting('Enable Pickup', default=False),
            bs.FloatChoiceSetting('Spotlight', choices=[
                ('Off', 0.0),
                ('Radius 1.5', 1.5),
                ('Radius 3.0', 3.0),
                ('Radius 4.5', 4.5),
            ], default=0.0),
            bs.IntChoiceSetting('Hints', choices=[
                ('Off', 0),
                ('Last 30 Seconds', 30),
                ('Last 60 Seconds', 60),
                ('Last 90 Seconds', 90),
            ], default=60),
            bs.IntChoiceSetting('Player Trails', choices=[
                ('Off', 0),
                ('5 Seconds', 5),
                ('10 Seconds', 10),
                ('15 Seconds', 15),
            ], default=0),
            bs.BoolSetting('Epic Mode', default=False),
            bs.IntChoiceSetting('Camera Mode', choices=[
                ('Full Maze', 0),
                ('Dynamic', 1),
            ], default=0),
            bs.IntChoiceSetting('Camera Y Offset', choices=[
                (str(n), n) for n in range(-20, 21)
            ], default=0),
            bs.IntChoiceSetting('Camera Z Offset', choices=[
                (str(n), n) for n in range(-20, 21)
            ], default=4),
            bs.IntChoiceSetting('Maze Y Offset', choices=[
                (str(n), n) for n in range(-10, 11)
            ], default=-10),
            bs.IntChoiceSetting('Maze Z Offset', choices=[
                (str(n), n) for n in range(-10, 11)
            ], default=-10),
        ]

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, (bs.DualTeamSession, bs.FreeForAllSession))

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Maze Meltdown Arena']

    @override
    def get_instance_description(self) -> str | Sequence:
        return 'Reach the finish with the most points!'

    @override
    def get_instance_description_short(self) -> str | Sequence:
        return 'Solve the fastest, and with least moves!'

    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._score_sound = bs.getsound('score')
        self._swipsound = bs.getsound('swip')
        self._beep1 = bs.getsound('raceBeep1')
        self._beep2 = bs.getsound('raceBeep2')
        self._tick_sound = bs.getsound('tick')

        self._maze_size: int = int(settings['Maze Size'])
        self._braid_factor: float = int(settings.get('Braid', 0)) / 100.0
        self._maze_view: int = int(settings.get('Maze View', 2))
        self._wall_style: int = int(settings.get('Walls', 0))
        self._optimize_walls: bool = bool(
            settings.get('Optimize Nodes', True))
        self._epic_mode: bool = bool(settings.get('Epic Mode', False))
        self._cell_size_setting: float = float(settings.get('Cell Size', 0.0))
        self._player_collisions: bool = bool(
            settings.get('Player Collisions', False))
        self._enable_punch: bool = bool(settings.get('Enable Punch', False))
        self._enable_bomb: bool = bool(settings.get('Enable Bomb', False))
        self._enable_jump: bool = bool(settings.get('Enable Jump', False))
        self._enable_pickup: bool = bool(settings.get('Enable Pickup', False))
        self._hint_seconds: int = int(settings.get('Hints', 0))
        self._trail_duration: float = float(settings.get('Player Trails', 0))
        self._trail_nodes: dict[tuple[int, int], bs.Node] = {}
        self._spotlight_radius: float = float(
            settings.get('Spotlight', 0.0))
        self._spotlight_active: bool = self._spotlight_radius > 0.0

        self._camera_mode: int = int(settings.get('Camera Mode', 0))
        self._camera_y_offset: float = float(
            settings.get('Camera Y Offset', 0))
        self._camera_z_offset: float = float(
            settings.get('Camera Z Offset', 4))
        self._maze_y_offset: float = float(
            settings.get('Maze Y Offset', -10))
        self._maze_z_offset: float = float(
            settings.get('Maze Z Offset', -10))

        _wall_colors: dict[int, tuple[float, float, float]] = {
            0: (0.15, 0.25, 0.9),   # Blue
            1: (0.9,  0.15, 0.55),  # Pink
            2: (0.9,  0.9,  0.9),   # White
            3: (0.9,  0.08, 0.08),  # Red
            4: (0.1,  0.85, 0.15),  # Lime
            5: (0.95, 0.45, 0.05),  # Orange
            6: (0.95, 0.85, 0.05),  # Yellow
            7: (0.05, 0.85, 0.9),   # Cyan
            8: (0.35, 0.05, 0.75),  # Purple
            9: (0.95, 0.05, 0.85),  # Magenta
            10: (1.0,  0.0,  0.0),  # Rainbow (start colour)
        }
        _wall_color_idx = int(settings.get('Wall Color', 0))
        self._wall_rainbow = (_wall_color_idx == 10)
        self._wall_color = _wall_colors.get(
            _wall_color_idx, _wall_colors[0])

        _path_color_idx = int(settings.get('Path Color', 0))
        if _path_color_idx == 99:
            self._path_color_raw: tuple[float, float, float] | None = None
            self._path_rainbow = False
        elif _path_color_idx == 10:
            _pc = _wall_colors.get(_path_color_idx, _wall_colors[0])
            self._path_color_raw = _pc
            self._path_rainbow = True
        else:
            _pc = _wall_colors.get(_path_color_idx, _wall_colors[0])
            self._path_color_raw = _pc
            self._path_rainbow = False

        # Derive what to show from Maze View setting.
        # 0 = Path only, 1 = Walls only, 2 = Path & Walls.
        self._show_walls: bool = self._maze_view in (1, 2)
        self._show_path: bool = self._maze_view in (0, 2)
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC_RACE if self._epic_mode else bs.MusicType.RACE)

        self._maze_data: MazeBuildData | None = None
        self._builder: MazeBuilder | None = None
        self._optimal_moves: int = 0
        self._race_started: bool = False
        self._start_lights: list[bs.Node] | None = None
        self.finish_material: bs.Material | None = None
        self._move_track_timer: bs.Timer | None = None
        self._scoreboard_timer: bs.Timer | None = None
        self._finish_count: int = 0
        self._last_team_time: float | None = None
        self._race_start_time: float = 0.0
        self._race_path: list[tuple[int, int]] = []
        self._hint_timer: bs.Timer | None = None
        self._hints_active: bool = False
        self._spotlight_timer: bs.Timer | None = None
        self._camera_timer: bs.Timer | None = None
        self._last_cam_center: tuple[float, float, float] = (
            0.0, self._maze_y_offset + 2.0, self._maze_z_offset)
        # Horizon-lock: Y and Z are frozen at init; only X slides.
        self._cam_fixed_y: float = self._maze_y_offset + 2.0 + self._camera_y_offset
        self._cam_fixed_z: float = self._maze_z_offset + self._camera_z_offset
        self._maze_world_w: float = 0.0
        self._maze_world_d: float = 0.0

        # Countdown scoring — calculated after maze is generated.
        self._start_score: int = self._maze_size * 50
        self._move_cost: float = 0.0
        self._time_cost_per_sec: float = 0.0
        self._score_drain_timer: bs.Timer | None = None

    @override
    def on_transition_in(self) -> None:
        super().on_transition_in()
        shared = SharedObjects.get()

        self.finish_material = bs.Material()
        self.finish_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._handle_finish_collide),
            ),
        )

        # Player no-collide material — when Player Collisions is off,
        # players phase through each other.
        self._no_player_collide_material = bs.Material()
        if not self._player_collisions:
            self._no_player_collide_material.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=('modify_part_collision', 'collide', False),
            )

        seed = random.randint(0, 999999)
        gen = MazeGenerator(cols=self._maze_size, rows=self._maze_size, seed=seed)
        char_grid = gen.generate(braid=self._braid_factor)

        # Select start/end based on layout.
        rng = random.Random(seed)
        start_cell, end_cell = select_endpoints(
            char_grid, self._maze_size, self._maze_size,
            rng)

        race_path = solve_maze_bfs(char_grid, start_cell, end_cell)
        self._race_path = race_path

        if self._cell_size_setting > 0.0:
            cell_size = self._cell_size_setting
        else:
            cell_size = max(0.8, 2.0 - self._maze_size * 0.06)
        # Derive MazeBuilder parameters from Maze View setting.
        # If walls hidden, use wall_style 2 (invisible visuals, collisions
        # still exist). Otherwise use the player's Regular/Flat choice.
        effective_wall_style = self._wall_style if self._show_walls else 2
        path_color = self._path_color_raw if self._show_path else None

        self._builder = MazeBuilder(
            char_grid=char_grid, cell_size=cell_size,
            wall_color=self._wall_color,
            wall_style=effective_wall_style,
            path_color=path_color,
            optimize_walls=self._optimize_walls,
            spotlight=self._spotlight_active,
            floor_y=self._maze_y_offset,
            z_offset=self._maze_z_offset,
        )
        self._maze_data = self._builder.build(race_path, self.finish_material)
        self._optimal_moves = self._maze_data.optimal_moves

        # Calculate drain rates from maze size.
        # Half the score is allocated to time drain, half to move drain.
        # A player taking 3× optimal moves loses the full move budget.
        move_budget = self._start_score * 0.5
        time_budget = self._start_score * 0.5
        self._move_cost = move_budget / max(
            1, self._optimal_moves * 3)
        # Time drain: spread over estimated reasonable completion time.
        estimated_time = self._optimal_moves * 2.0
        self._time_cost_per_sec = time_budget / max(1.0, estimated_time)

        # Rainbow animation: slow hue cycle on wall and/or path locators.
        _RAINBOW: dict[float, tuple[float, float, float]] = {
            0.0: (1.0, 0.0, 0.0),
            1.0: (1.0, 0.5, 0.0),
            2.0: (1.0, 1.0, 0.0),
            3.0: (0.0, 1.0, 0.0),
            4.0: (0.0, 0.4, 1.0),
            5.0: (0.5, 0.0, 1.0),
            6.0: (1.0, 0.0, 0.0),
        }
        if self._wall_rainbow:
            for wn in self._maze_data.wall_nodes:
                bs.animate_array(wn, 'color', 3, _RAINBOW, loop=True)
        if self._path_rainbow:
            for pn in self._maze_data.path_nodes:
                bs.animate_array(pn, 'color', 3, _RAINBOW, loop=True)

        our_map = self.map
        assert isinstance(our_map, MazeRaceMap)
        gw = self._maze_data.grid_width * cell_size
        gh = self._maze_data.grid_height * cell_size
        self._maze_world_w = gw
        self._maze_world_d = gh
        our_map.set_floor_size(gw, gh,
                               maze_y=self._maze_y_offset,
                               maze_z=self._maze_z_offset)
        our_map.update_defs([self._maze_data.start_pos], gw, gh,
                            cam_y=self._camera_y_offset,
                            cam_z=self._camera_z_offset,
                            maze_y=self._maze_y_offset,
                            maze_z=self._maze_z_offset)

        # Set initial camera center on the start position and apply
        # the AOI directly to globalsnode (update_defs only changes
        # class-level defs which the map already consumed).
        sp = self._maze_data.start_pos
        gnode = self.globalsnode

        if self._camera_mode == 0:
            # Full Maze — AOI covers entire maze, engine picks zoom.
            aoi_w = gw + 4.0
            aoi_d = gh + 4.0
            cam_cx = 0.0
            cam_cy = self._maze_y_offset + 4.0 + self._camera_y_offset
            cam_cz = self._maze_z_offset + self._camera_z_offset
            gnode.area_of_interest_bounds = (
                cam_cx - aoi_w * 0.5, cam_cy - 5.0, cam_cz - aoi_d * 0.5,
                cam_cx + aoi_w * 0.5, cam_cy + 5.0, cam_cz + aoi_d * 0.5)
        else:
            # Dynamic — horizon-locked AOI that slides left/right only.
            aoi_w = min(gw + 2.0, 18.0)
            aoi_d = min(gh + 2.0, 18.0)
            cam_cx = sp[0]
            # Pin Y and Z for the lifetime of this game — no twist, no tilt.
            self._cam_fixed_y = (self._maze_y_offset + 4.0
                                 + self._camera_y_offset)
            self._cam_fixed_z = self._maze_z_offset + self._camera_z_offset
            self._last_cam_center = (cam_cx,
                                     self._cam_fixed_y,
                                     self._cam_fixed_z)
            gnode.area_of_interest_bounds = (
                cam_cx - aoi_w * 0.5,
                self._cam_fixed_y - 3.0,
                self._cam_fixed_z - aoi_d * 0.5,
                cam_cx + aoi_w * 0.5,
                self._cam_fixed_y + 3.0,
                self._cam_fixed_z + aoi_d * 0.5)

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self._scoreboard_timer = bs.Timer(0.5, self._update_scoreboard, repeat=True)
        if self._camera_mode == 1:
            self._camera_timer = bs.Timer(0.1, self._update_camera, repeat=True)

        t_scale = 0.4 if self.slow_motion else 1.0
        lstart = 7.1 * t_scale
        inc = 1.25 * t_scale
        bs.timer(lstart, self._do_light_1)
        bs.timer(lstart + inc, self._do_light_2)
        bs.timer(lstart + 2 * inc, self._do_light_3)
        bs.timer(lstart + 3 * inc, self._start_race)

        light_y = 50 if self.slow_motion else 150
        self._start_lights = []
        for i in range(4):
            lnub = bs.newnode('image', attrs={
                'texture': bs.gettexture('nub'), 'opacity': 1.0,
                'absolute_scale': True,
                'position': (-75 + i * 50, light_y),
                'scale': (50, 50), 'attach': 'center',
            })
            bs.animate(lnub, 'opacity', {
                4.0 * t_scale: 0, 5.0 * t_scale: 1.0,
                12.0 * t_scale: 1.0, 12.5 * t_scale: 0.0,
            })
            bs.timer(13.0 * t_scale, lnub.delete)
            self._start_lights.append(lnub)

        # Dim initial state — matches the Race minigame exactly.
        self._start_lights[0].color = (0.2, 0.0, 0.0)
        self._start_lights[1].color = (0.2, 0.0, 0.0)
        self._start_lights[2].color = (0.2, 0.05, 0.0)
        self._start_lights[3].color = (0.0, 0.3, 0.0)

        bs.broadcastmessage(
            f'Starting score: {self._start_score}  —  '
            f'Every Second and New Move costs points!',
            color=(0.3, 1.0, 0.8),
        )

        # Schedule path hints if enabled.
        if self._hint_seconds > 0:
            estimated_time = self._optimal_moves * 2.0
            delay = max(0.0, estimated_time - self._hint_seconds)
            bs.timer(delay, self._activate_hints)

        # Start spotlight update loop.
        if self._spotlight_active:
            self._spotlight_timer = bs.Timer(
                0.1, self._update_spotlight, repeat=True)

    def _update_camera(self) -> None:
        """Slide camera left/right only (horizon-locked, no rotation).

        Y and Z are frozen at game start so the viewing angle never changes.
        Only the X axis tracks the player centroid, giving a pure lateral
        slide rather than a twist or tilt.
        """
        if self.has_ended() or self._maze_world_w <= 0:
            return

        # Collect only the X positions of alive, unfinished players.
        xs: list[float] = []
        for player in self.players:
            if not player.exists() or player.finished:
                continue
            if not player.is_alive():
                continue
            try:
                assert isinstance(player.actor, PlayerSpaz)
                assert player.actor.node
                xs.append(player.actor.node.position[0])
            except Exception:
                continue

        # Target X — centroid of players, or hold the last known position.
        target_x = (sum(xs) / len(xs)) if xs else self._last_cam_center[0]

        # Smooth interpolation on X only.
        lerp = 0.3
        lx = self._last_cam_center[0] + (target_x - self._last_cam_center[0]) * lerp

        # Clamp X so the AOI never drifts outside the maze.
        mw = self._maze_world_w
        md = self._maze_world_d
        aoi_w = min(mw + 2.0, 18.0)
        aoi_d = min(md + 2.0, 18.0)
        half_w = aoi_w * 0.5
        if aoi_w >= mw:
            lx = 0.0  # Maze fits entirely — just center it.
        else:
            lx = max(-(mw * 0.5) + half_w, min(mw * 0.5 - half_w, lx))

        # Y and Z are locked — camera angle never changes.
        self._last_cam_center = (lx,
                                 self._cam_fixed_y,
                                 self._cam_fixed_z)

        # Update the globalsnode AOI (min_x, min_y, min_z, max_x, max_y, max_z).
        gnode = self.globalsnode
        gnode.area_of_interest_bounds = (
            lx - aoi_w * 0.5,
            self._cam_fixed_y - 3.0,
            self._cam_fixed_z - aoi_d * 0.5,
            lx + aoi_w * 0.5,
            self._cam_fixed_y + 3.0,
            self._cam_fixed_z + aoi_d * 0.5)

    def _do_light_1(self) -> None:
        self._beep1.play()
        if self._start_lights and len(self._start_lights) > 0:
            self._start_lights[0].color = (1.0, 0.0, 0.0)

    def _do_light_2(self) -> None:
        self._beep1.play()
        if self._start_lights and len(self._start_lights) > 1:
            self._start_lights[1].color = (1.0, 0.0, 0.0)

    def _do_light_3(self) -> None:
        self._beep1.play()
        if self._start_lights and len(self._start_lights) > 2:
            self._start_lights[2].color = (1.0, 0.3, 0.0)

    def _start_race(self) -> None:
        self._beep2.play()
        if self._start_lights and len(self._start_lights) > 3:
            self._start_lights[3].color = (0.0, 1.0, 0.0)
        self._race_started = True
        self._race_start_time = bs.time()
        self._move_track_timer = bs.Timer(0.1, self._track_moves, repeat=True)

        # Initialize all player live scores and start the time drain.
        for player in self.players:
            player.live_score = float(self._start_score)
            self._update_player_text(player)

        self._score_drain_timer = bs.Timer(
            1.0, self._drain_time_score, repeat=True)

        # Unfreeze all players — give them controls.
        for player in self.players:
            if player.is_alive() and isinstance(player.actor, PlayerSpaz):
                player.actor.connect_controls_to_player(
                    enable_punch=self._enable_punch,
                    enable_bomb=self._enable_bomb,
                    enable_jump=self._enable_jump,
                    enable_pickup=self._enable_pickup,
                )

    # ── Hints ──

    def _activate_hints(self) -> None:
        """Begin spawning hint markers along the solution path."""
        if self.has_ended() or self._hints_active or self._builder is None:
            return
        self._hints_active = True

        bs.broadcastmessage('Hint activated!', color=(0.2, 1.0, 0.4))

        # Build the hint cell list: reversed path, every other tile.
        reversed_path = list(reversed(self._race_path))
        hint_cells = reversed_path[::2]

        # Spawn each hint with a 2-second stagger.
        for i, cell in enumerate(hint_cells):
            bs.timer(i * 2.0,
                     bs.WeakCallStrict(self._spawn_hint, cell))

    def _spawn_hint(self, cell: tuple[int, int]) -> None:
        """Place a green glowing circle locator on a path cell."""
        if self.has_ended() or self._builder is None:
            return
        gx, gy = cell
        wx, wy, wz = self._builder.grid_to_world(gx, gy)
        cs = self._maze_data.cell_size if self._maze_data else 1.0
        floor_top = wy + 0.5

        bs.newnode('locator', attrs={
            'shape': 'circle',
            'position': (wx, floor_top + 0.05, wz),
            'size': (cs * 0.6,),
            'color': (0.1, 1.0, 0.3),
            'opacity': 0.8,
            'draw_beauty': True,
            'additive': True,
        })
        # Small flash of light for the glow effect.
        light = bs.newnode('light', attrs={
            'position': (wx, floor_top + 0.3, wz),
            'color': (0.1, 1.0, 0.3),
            'height_attenuated': False,
            'radius': 0.15,
        })
        bs.animate(light, 'intensity', {0: 0, 0.3: 0.6, 0.6: 0.3})

    # ── Spotlight ──

    def _update_spotlight(self) -> None:
        """Show/hide tiles by moving them into/out of view."""
        if self.has_ended() or self._maze_data is None:
            return
        if self._builder is None:
            return

        _HIDDEN_Y = -50.0

        # Gather all alive player grid positions.
        player_cells: list[tuple[int, int]] = []
        for player in self.players:
            if not player.is_alive() or player.finished:
                continue
            try:
                pos = player.position
            except Exception:
                continue
            cell = self._builder.world_to_grid(pos.x, pos.z)
            player_cells.append(cell)

        if not player_cells:
            return

        # Radius in char-grid units (each maze cell = 2 grid units).
        r_sq = (self._spotlight_radius * 2.0) ** 2

        for node, gx, gy, target_opacity, real_pos in (
                self._maze_data.spotlight_nodes):
            if not node.exists():
                continue
            visible = False
            for px, py in player_cells:
                dx = gx - px
                dy = gy - py
                if dx * dx + dy * dy <= r_sq:
                    visible = True
                    break
            if visible:
                node.position = real_pos
            else:
                node.position = (_HIDDEN_Y, _HIDDEN_Y, _HIDDEN_Y)

    # ── Move Tracking ──

    def _track_moves(self) -> None:
        if not self._race_started or self.has_ended() or self._builder is None:
            return
        for player in self.players:
            if not player.is_alive() or player.finished:
                continue
            try:
                pos = player.position
            except Exception:
                continue
            cell = self._builder.world_to_grid(pos.x, pos.z)
            if player.last_grid_cell is None:
                player.last_grid_cell = cell
                player.visited_cells.add(cell)
                if self._trail_duration > 0:
                    self._place_trail(cell, player)
                continue
            if cell != player.last_grid_cell:
                player.last_grid_cell = cell
                # Place a trail on every cell transition.
                if self._trail_duration > 0:
                    self._place_trail(cell, player)
                # Only charge for tiles we haven't visited before.
                if cell not in player.visited_cells:
                    player.visited_cells.add(cell)
                    player.moves += 1
                    player.live_score = max(
                        0.0, player.live_score - self._move_cost)
                    self._update_player_text(player)
                    if player.live_score <= 0:
                        self._kill_player(player)

    def _drain_time_score(self) -> None:
        """Deduct time-based points from all active players each second."""
        if not self._race_started or self.has_ended():
            return
        for player in self.players:
            if not player.is_alive() or player.finished:
                continue
            player.live_score = max(
                0.0, player.live_score - self._time_cost_per_sec)
            self._update_player_text(player)
            if player.live_score <= 0:
                self._kill_player(player)

    def _kill_player(self, player: Player) -> None:
        """Kill a player who ran out of points."""
        if not player.is_alive():
            return
        player.finished = True  # Mark as done so they aren't processed.
        player.live_score = 0.0
        bs.broadcastmessage(
            f'{player.getname(full=True)} ran out of points!',
            color=(1.0, 0.3, 0.2),
        )
        try:
            assert isinstance(player.actor, PlayerSpaz)
            player.actor.handlemessage(bs.DieMessage())
        except Exception:
            pass
        self._check_end_game()

    def _place_trail(self, cell: tuple[int, int],
                     player: Player) -> None:
        """Place or replace a trail marker on a cell."""
        if self._builder is None or self._maze_data is None:
            return
        gx, gy = cell
        wx, wy, wz = self._builder.grid_to_world(gx, gy)
        cs = self._maze_data.cell_size
        floor_top = wy + 0.5

        # Delete existing trail on this cell.
        old = self._trail_nodes.pop(cell, None)
        if old and old.exists():
            old.delete()

        # Get the player's team color.
        color = player.team.color

        node = bs.newnode('locator', attrs={
            'shape': 'circle',
            'position': (wx, floor_top + 0.02, wz),
            'size': (cs * 0.5,),
            'color': color,
            'opacity': 0.6,
            'draw_beauty': True,
            'additive': True,
        })
        self._trail_nodes[cell] = node

        # Fade out then delete after the trail duration.
        dur = self._trail_duration
        bs.animate(node, 'opacity', {
            0: 0.6,
            dur * 0.6: 0.6,
            dur: 0.0,
        })

        def _remove_trail(c: tuple[int, int],
                          n: bs.Node) -> None:
            # Only remove from dict if this is still the active node
            # for the cell (hasn't been overwritten).
            if self._trail_nodes.get(c) is n:
                del self._trail_nodes[c]
            if n.exists():
                n.delete()

        bs.timer(dur, bs.CallStrict(_remove_trail, cell, node))

    def _attach_move_text(self, player: Player) -> None:
        try:
            spaz = player.actor
            if not isinstance(spaz, PlayerSpaz) or not spaz.node:
                return
            m = bs.newnode('math', owner=spaz.node,
                           attrs={'input1': (0, 2.2, 0), 'operation': 'add'})
            spaz.node.connectattr('torso_position', m, 'input2')
            score_display = int(player.live_score) if player.live_score > 0 else self._start_score
            txt = bs.newnode('text', owner=m, attrs={
                'text': str(score_display),
                'in_world': True,
                'color': (0.3, 1.0, 0.85, 1.0),
                'scale': 0.016, 'h_align': 'center', 'shadow': 0.5,
            })
            m.connectattr('output', txt, 'position')
            player.move_math_node = m
            player.move_text_node = txt
        except Exception:
            pass

    def _update_player_text(self, player: Player) -> None:
        try:
            if player.move_text_node and player.move_text_node.exists():
                score = int(player.live_score)
                ratio = score / max(1, self._start_score)
                if ratio > 0.6:
                    color = (0.3, 1.0, 0.85, 1.0)   # Green — healthy
                elif ratio > 0.3:
                    color = (1.0, 1.0, 0.3, 1.0)     # Yellow — caution
                else:
                    color = (1.0, 0.3, 0.2, 1.0)     # Red — critical
                player.move_text_node.text = str(score)
                player.move_text_node.color = color
        except Exception:
            pass

    # ── Finish Handling ──

    def _handle_finish_collide(self) -> None:
        if not self._race_started or self.has_ended():
            return
        collision = bs.getcollision()
        try:
            spaz = collision.opposingnode.getdelegate(PlayerSpaz, True)
            player = spaz.getplayer(Player, True)
        except bs.NotFoundError:
            return
        if player.finished:
            return

        player.finished = True
        self._finish_count += 1
        player.finish_order = self._finish_count

        # Score is whatever's left on the countdown.
        final_score = max(0, int(player.live_score))
        player.team.score += final_score

        # Award through stats (shows kill-feed style points).
        self.stats.player_scored(
            player, final_score, screenmessage=False, display=True)

        self._score_sound.play()
        self._flash_player(player, 1.0)

        ordinal = self._ordinal(player.finish_order)

        # Result text above head.
        try:
            assert isinstance(player.actor, PlayerSpaz)
            assert player.actor.node
            m = bs.newnode('math', owner=player.actor.node,
                           attrs={'input1': (0, 2.6, 0), 'operation': 'add'})
            player.actor.node.connectattr('torso_position', m, 'input2')
            result_color = (
                (0.2, 1.0, 0.3, 1.0) if final_score > 0
                else (1.0, 0.3, 0.2, 1.0))
            txt = bs.newnode('text', owner=m, attrs={
                'text': f'{ordinal}!  {final_score} pts',
                'in_world': True, 'color': result_color,
                'scale': 0.015, 'h_align': 'center',
            })
            m.connectattr('output', txt, 'position')
            bs.animate(txt, 'scale', {0: 0, 0.3: 0.019, 3.0: 0.019, 3.5: 0})
            bs.timer(4.0, m.delete)
        except Exception:
            pass

        bs.broadcastmessage(
            f'{player.getname(full=True)} finished {ordinal}! '
            f'({final_score} pts)',
            color=(0.3, 1.0, 0.5),
        )

        assert player.actor
        player.actor.handlemessage(bs.DieMessage(immediate=True))

        # Record team finish time.
        team = player.team
        if all(p.finished for p in team.players):
            team.finished = True
            team.time = bs.time() - self._race_start_time
            self._last_team_time = team.time
        self._update_scoreboard()
        self._check_end_game()

    @staticmethod
    def _ordinal(n: int) -> str:
        """Return ordinal string for a number (1st, 2nd, 3rd, etc)."""
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f'{n}{suffix}'

    def _flash_player(self, player: Player, scale: float) -> None:
        try:
            assert isinstance(player.actor, PlayerSpaz)
            assert player.actor.node
            pos = player.actor.node.position
            light = bs.newnode('light', attrs={
                'position': pos, 'color': (1, 1, 0),
                'height_attenuated': False, 'radius': 0.4,
            })
            bs.timer(0.5, light.delete)
            bs.animate(light, 'intensity', {0: 0, 0.1: 1.0 * scale, 0.5: 0})
        except Exception:
            pass

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            # Sum locked-in scores from finished players plus
            # live draining scores from active players.
            display = team.score  # Already has finished players' scores.
            for player in team.players:
                if player.exists() and not player.finished:
                    display += max(0, int(player.live_score))
            self._scoreboard.set_team_value(team, display)

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        assert self._maze_data is not None
        assert self._builder is not None

        pos = self._maze_data.start_pos
        player.visited_cells.clear()

        spaz = self.spawn_player_spaz(player, position=pos)

        # Apply no-collide material so players phase through each other.
        if not self._player_collisions and spaz.node:
            try:
                for slot in ('materials', 'roller_materials',
                             'extras_material'):
                    mats = list(getattr(spaz.node, slot))
                    mats.append(self._no_player_collide_material)
                    setattr(spaz.node, slot, mats)
            except Exception:
                pass

        # Reconnect with restricted controls.
        spaz.connect_controls_to_player(
            enable_punch=self._enable_punch,
            enable_bomb=self._enable_bomb,
            enable_jump=self._enable_jump,
            enable_pickup=self._enable_pickup,
        )

        # Freeze player until the countdown finishes.
        if not self._race_started:
            spaz.disconnect_controls_from_player()

        player.move_math_node = None
        player.move_text_node = None
        self._attach_move_text(player)
        return spaz

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            # No respawns — dead players are out.
            self._check_end_game()
        else:
            return super().handlemessage(msg)
        return None

    def _check_end_game(self) -> None:
        """End the game when every player is either finished or dead."""
        if self.has_ended():
            return
        for player in self.players:
            if not player.exists():
                continue
            # Still racing — not done yet.
            if player.is_alive() and not player.finished:
                return
        bs.timer(1.0, self.end_game)

    @override
    def end_game(self) -> None:
        # Stop drains and camera tracking.
        self._score_drain_timer = None
        self._camera_timer = None

        results = bs.GameResults()
        for team in self.teams:
            if team.score > 0 or team.finished:
                results.set_team_score(team, team.score)
            else:
                results.set_team_score(team, None)

        self.end(
            results=results,
            announce_winning_team=True,
        )

    @override
    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()
