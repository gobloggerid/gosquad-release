# Released under the MIT License. See LICENSE for details.
#
# RUMBLE RUSH — A chaotic obstacle-course race for BombSquad.
#
# Navigate a grid of mystery tiles: some are safe, some will
# betray you. Bounce pads launch you skyward, icy tiles send
# you sliding, rumbling tiles shake and fall, and false tiles
# vanish the instant you touch them. First to the finish wins!

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
import logging
import weakref
from enum import Enum
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.flag import Flag
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


# ────────────────────────────────────────────────────────────
#  PLATFORM TYPES & TILE ACTOR
# ────────────────────────────────────────────────────────────

class PlatformType(Enum):
    """All possible tile behaviours."""
    SOLID = 'solid'            # Green  — permanent safe ground
    DISAPPEARING = 'disappearing'  # Red    — reveals & falls instantly
    BOUNCY = 'bouncy'          # Blue   — super-jump on press
    ICY = 'icy'                # Cyan   — near-zero friction
    RUMBLING = 'rumbling'    # Orange — shakes, then falls & respawns

    @property
    def color(self) -> tuple[float, float, float]:
        return _TYPE_COLORS[self]

    @property
    def label(self) -> str:
        return _TYPE_LABELS[self]


_TYPE_COLORS: dict[PlatformType, tuple[float, float, float]] = {
    PlatformType.SOLID: (0.3, 0.8, 0.3),
    PlatformType.DISAPPEARING: (1.0, 0.25, 0.2),
    PlatformType.BOUNCY: (0.2, 0.5, 1.0),
    PlatformType.ICY: (0.4, 0.9, 1.0),
    PlatformType.RUMBLING: (0.9, 0.6, 0.1),
}

_TYPE_LABELS: dict[PlatformType, str] = {
    PlatformType.SOLID: 'Solid',
    PlatformType.DISAPPEARING: 'False',
    PlatformType.BOUNCY: 'Bounce',
    PlatformType.ICY: 'Ice',
    PlatformType.RUMBLING: 'Rumble',
}


class RumblePlatform(bs.Actor):
    """A single mystery tile in the course.

    Starts neutral gray. Reveals its true color and behaviour when
    a player first steps on it. Can fall, respawn, bounce, slide,
    or rumble depending on its PlatformType.
    """

    NEUTRAL_COLOR = (0.45, 0.45, 0.5)
    TILE_W = 2.0
    TILE_H = 0.25
    TILE_D = 2.0
    VIS_SHRINK = 0.06

    # Bounce impulse settings.
    BOUNCE_MAGNITUDE = 1000.0
    BOUNCE_COOLDOWN = 0.4
    BOUNCE_VEL_THRESHOLD = 3.5

    # Rumble timing.
    RUMBLE_SHAKE_TIME = 1.8
    RESPAWN_DELAY = 3.0

    def __init__(
        self,
        position: tuple[float, float, float],
        ptype: PlatformType = PlatformType.SOLID,
        game: RumbleRushGame | None = None,
    ):
        super().__init__()
        self.ptype = ptype
        self.position = position
        self._game_ref = weakref.ref(game) if game else None

        # State flags.
        self._revealed = False
        self._gone = False

        # Animation timers.
        self._fall_timer: bs.Timer | None = None
        self._respawn_timer: bs.Timer | None = None
        self._memory_timer: bs.Timer | None = None

        # Bounce tracking (blue tiles).
        self._last_bounce_time: float = 0.0
        self._bounce_target: bs.Node | None = None
        self._bounce_watch_timer: bs.Timer | None = None

        # Visual nodes.
        self._locator: bs.Node | None = None
        self._color_light: bs.Node | None = None
        self._label_node: bs.Node | None = None

        # Build collision & visuals.
        self._floor_material, self._type_material = self._create_materials()
        self.node = self._create_region(self._floor_material,
                                        self._type_material)
        self._build_visuals(self.NEUTRAL_COLOR)

    # ── Material & Region Factories ──────────────────────────

    def _create_materials(self) -> tuple[bs.Material, bs.Material]:
        """Build the floor (walkable) and type-specific materials."""
        shared = SharedObjects.get()

        floor_mat = bs.Material()
        floor_mat.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
                ('call', 'at_connect', self._on_player_touch),
            ),
        )
        floor_mat.add_actions(
            conditions=('they_have_material', shared.object_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )

        type_mat = bs.Material()
        if self.ptype == PlatformType.ICY:
            type_mat.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=('modify_part_collision', 'friction', 0.02),
            )
        elif self.ptype == PlatformType.BOUNCY:
            type_mat.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=('call', 'at_connect', self._on_bounce_connect),
            )
            type_mat.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=('call', 'at_disconnect',
                         self._on_bounce_disconnect),
            )

        return floor_mat, type_mat

    def _create_region(
        self,
        floor_mat: bs.Material,
        type_mat: bs.Material,
    ) -> bs.Node:
        """Create the collision region node."""
        shared = SharedObjects.get()
        return bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': self.position,
                'scale': (self.TILE_W, self.TILE_H, self.TILE_D),
                'type': 'box',
                'materials': [shared.footing_material, floor_mat, type_mat],
            },
        )

    def _build_visuals(self, color: tuple[float, float, float]) -> None:
        """Create (or recreate) the locator box and glow light."""
        vw = self.TILE_W - self.VIS_SHRINK
        vd = self.TILE_D - self.VIS_SHRINK
        self._locator = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': self.position,
                'color': color,
                'opacity': 0.9,
                'draw_beauty': True,
                'additive': False,
                'size': [vw, self.TILE_H, vd],
            },
        )
        self._color_light = bs.newnode(
            'light',
            attrs={
                'position': self.position,
                'color': color,
                'intensity': 0.25,
                'radius': 0.8,
                'volume_intensity_scale': 0.0,
                'height_attenuated': False,
            },
        )

    # ── Helper: Game Setting Access ──────────────────────────

    def _game_setting(self, attr: str, default: Any = False) -> Any:
        """Safely read a setting from the game instance."""
        game = self._game_ref() if self._game_ref else None
        return getattr(game, attr, default) if game else default

    # ── Touch / Reveal ───────────────────────────────────────

    def _on_player_touch(self) -> None:
        """First contact reveals the tile; reactive tiles then trigger."""
        if self._gone or self._revealed:
            return

        self._revealed = True

        if self.ptype == PlatformType.DISAPPEARING:
            self._reveal()
            self._begin_fall()
        else:
            self._reveal()
            if self.ptype == PlatformType.RUMBLING:
                self._shake()
                bs.timer(self.RUMBLE_SHAKE_TIME,
                         bs.WeakCallStrict(self._vanish))

            # Memory mode: fade safe tiles back to gray after 6s.
            if self._game_setting('_memory_mode'):
                if self.ptype != PlatformType.RUMBLING:
                    bs.timer(6.0,
                             bs.WeakCallStrict(self._memory_fade_back))

    def _reveal(self) -> None:
        """Swap from neutral to the tile's true color with a pop."""
        color = self.ptype.color
        if self._locator:
            self._locator.color = color
        if self._color_light:
            self._color_light.color = color
            bs.animate(self._color_light, 'intensity',
                       {0.0: 1.0, 0.2: 0.25})
        bs.getsound('tick').play(volume=0.3, position=self.position)
        self._show_label()

    # ── Tile Labels ──────────────────────────────────────────

    def _show_label(self) -> None:
        """Display the type name above the tile (if setting enabled)."""
        self._delete_label()
        if not self._game_setting('_tile_labels'):
            return

        color = self.ptype.color
        pos = self.position
        self._label_node = bs.newnode(
            'text',
            attrs={
                'text': self.ptype.label,
                'in_world': True,
                'scale': 0.01,
                'color': (*color, 1.0),
                'position': (pos[0], pos[1] + 0.6, pos[2]),
                'h_align': 'center',
            },
        )

    def _delete_label(self) -> None:
        """Remove the floating label node."""
        if self._label_node:
            self._label_node.delete()
            self._label_node = None

    # ── Bounce (Blue Tiles) ──────────────────────────────────

    def _on_bounce_connect(self) -> None:
        """Player landed on a bouncy tile — start watching for a jump."""
        if self._gone:
            return
        try:
            node = bs.getcollision().opposingnode
        except bs.NotFoundError:
            return
        if node.getnodetype() != 'spaz' or node.knockout > 0.0:
            return

        self._bounce_target = node
        self._bounce_watch_timer = bs.Timer(
            0.02, bs.WeakCallStrict(self._check_for_jump), repeat=True,
        )

    def _on_bounce_disconnect(self) -> None:
        """Player left the bouncy tile."""
        self._bounce_target = None
        self._bounce_watch_timer = None

    def _check_for_jump(self) -> None:
        """~50 fps poll: when vertical velocity spikes, boost it."""
        node = self._bounce_target
        if node is None or not node.exists() or self._gone:
            self._bounce_watch_timer = None
            return

        if node.velocity[1] > self.BOUNCE_VEL_THRESHOLD:
            now = bs.time()
            if now - self._last_bounce_time < self.BOUNCE_COOLDOWN:
                return
            self._last_bounce_time = now

            pos = node.position
            node.handlemessage(
                'impulse',
                pos[0], pos[1], pos[2],   # position
                0.0, 0.0, 0.0,            # velocity
                self.BOUNCE_MAGNITUDE,     # magnitude
                0.0, 0.0, 0,              # vmag, radius, srcmag
                0.0, 1.0, 0.0,            # force direction (up)
            )
            bs.getsound('corkPop').play(
                volume=0.8, position=self.position,
            )
            self._bounce_watch_timer = None

    # ── Memory Mode Fade ─────────────────────────────────────

    def _memory_fade_back(self) -> None:
        """Fade a revealed safe tile back to neutral gray."""
        if self._gone:
            return
        self._delete_label()
        self._memory_step = 0
        self._memory_from = self.ptype.color
        self._memory_timer = bs.Timer(
            0.03, bs.WeakCallStrict(self._do_memory_fade), repeat=True,
        )

    def _do_memory_fade(self) -> None:
        """Animate one step of the color fade (gray ← type color)."""
        if self._gone:
            self._memory_timer = None
            return
        self._memory_step += 1
        t = min(1.0, self._memory_step * 0.02)

        fc, nc = self._memory_from, self.NEUTRAL_COLOR
        c = tuple(fc[i] + (nc[i] - fc[i]) * t for i in range(3))

        if self._locator:
            self._locator.color = c
        if self._color_light:
            self._color_light.color = c

        if t >= 1.0:
            self._memory_timer = None
            self._revealed = False  # Allow re-reveal on next touch.

    # ── Rumbling (Orange Tiles) ─────────────────────────────

    def _shake(self) -> None:
        """Visual shake + rumble before a rumbling tile falls."""
        if not self._locator:
            return
        pos = self.position
        bs.getsound('bombRoll01').play(volume=0.6, position=pos)

        def _jitter() -> None:
            if self._locator:
                self._locator.position = (
                    pos[0] + random.uniform(-0.1, 0.1),
                    pos[1] + random.uniform(-0.04, 0.04),
                    pos[2] + random.uniform(-0.1, 0.1),
                )

        for i in range(18):
            bs.timer(i * 0.1, _jitter)

        if self._color_light:
            bs.animate(
                self._color_light, 'intensity',
                {0.0: 0.4, 0.5: 1.0, 1.0: 0.4, 1.5: 1.2, 1.8: 1.5},
            )

    def _vanish(self) -> None:
        """Rumble timer expired — start falling."""
        if not self._gone:
            self._begin_fall()

    # ── Falling Animation ────────────────────────────────────

    def _begin_fall(self) -> None:
        """Start the fall animation (keeps original floor material)."""
        if self._gone:
            return
        self._gone = True

        if self._color_light:
            self._color_light.intensity = 1.5
        bs.getsound('explosion01').play(position=self.position)

        self._fall_y = self.position[1]
        self._fall_vel = 0.0
        self._fall_step = 0
        self._fall_timer = bs.Timer(
            0.016, bs.WeakCallStrict(self._do_fall_step), repeat=True,
        )

    def _do_fall_step(self) -> None:
        """One frame of the falling animation (~60 fps)."""
        self._fall_step += 1
        self._fall_vel += 12.0 * 0.016
        self._fall_y -= self._fall_vel * 0.016

        y = self._fall_y
        px, pz = self.position[0], self.position[2]
        t = min(1.0, self._fall_step * 0.02)
        bc = self.ptype.color
        r, g, b = bc[0] * (1.0 - t), bc[1] * (1.0 - t), bc[2] * (1.0 - t)

        if self.node:
            self.node.position = (px, y, pz)
        if self._locator:
            self._locator.position = (px, y, pz)
            self._locator.color = (r, g, b)
        if self._color_light:
            self._color_light.position = (px, y, pz)
            self._color_light.color = (r, g, b)
            self._color_light.intensity = max(
                0.0, 1.5 - self._fall_step * 0.03,
            )
        if self._label_node:
            self._label_node.position = (px, y + 0.6, pz)
            self._label_node.color = (r, g, b, max(0.0, 1.0 - t))

        if y < -6.0:
            self._fall_timer = None
            self._cleanup_and_maybe_respawn()

    # ── Cleanup & Respawn ────────────────────────────────────

    def _delete_nodes(self) -> None:
        """Delete all visual and collision nodes."""
        for node in (self.node, self._locator,
                     self._color_light, self._label_node):
            if node:
                node.delete()
        self._locator = None
        self._color_light = None
        self._label_node = None

    def _cleanup_and_maybe_respawn(self) -> None:
        """Remove nodes; schedule respawn if applicable."""
        self._delete_nodes()

        should_respawn = False
        if self.ptype == PlatformType.RUMBLING:
            should_respawn = True
        elif self.ptype == PlatformType.DISAPPEARING:
            should_respawn = self._game_setting('_red_respawn')

        if should_respawn:
            bs.timer(self.RESPAWN_DELAY,
                     bs.WeakCallStrict(self._respawn))

    def _respawn(self) -> None:
        """Rebuild the tile from scratch, fading from black to neutral."""
        # Reset state.
        self._gone = False
        self._revealed = False
        self._last_bounce_time = 0.0
        self._bounce_target = None
        self._bounce_watch_timer = None

        # Rebuild materials & region.
        self._floor_material, self._type_material = self._create_materials()
        self.node = self._create_region(self._floor_material,
                                        self._type_material)

        # Rebuild visuals starting black.
        vw = self.TILE_W - self.VIS_SHRINK
        vd = self.TILE_D - self.VIS_SHRINK
        self._locator = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': self.position,
                'color': (0.0, 0.0, 0.0),
                'opacity': 0.9,
                'draw_beauty': True,
                'additive': False,
                'size': [vw, self.TILE_H, vd],
            },
        )
        self._color_light = bs.newnode(
            'light',
            attrs={
                'position': self.position,
                'color': (0.0, 0.0, 0.0),
                'intensity': 0.0,
                'radius': 0.8,
                'volume_intensity_scale': 0.0,
                'height_attenuated': False,
            },
        )

        # Animate: black → neutral gray over ~1 second.
        self._respawn_step = 0
        self._respawn_timer = bs.Timer(
            0.03, bs.WeakCallStrict(self._do_respawn_fade), repeat=True,
        )

    def _do_respawn_fade(self) -> None:
        """Animate one step of the black → neutral fade."""
        self._respawn_step += 1
        t = min(1.0, self._respawn_step * 0.03)
        nc = self.NEUTRAL_COLOR
        c = (nc[0] * t, nc[1] * t, nc[2] * t)

        if self._locator:
            self._locator.color = c
        if self._color_light:
            self._color_light.color = c
            self._color_light.intensity = 0.25 * t

        if t >= 1.0:
            self._respawn_timer = None

    # ── Lifecycle ────────────────────────────────────────────

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            # Cancel all running timers.
            self._fall_timer = None
            self._respawn_timer = None
            self._memory_timer = None
            self._bounce_watch_timer = None
            self._delete_nodes()
        else:
            return super().handlemessage(msg)
        return None


# ────────────────────────────────────────────────────────────
#  CHECKPOINT REGION
# ────────────────────────────────────────────────────────────

class CheckpointRegion(bs.Actor):
    """Invisible region that tracks player progress through the course."""

    def __init__(
        self,
        position: tuple[float, float, float],
        scale: tuple[float, float, float],
        index: int,
        is_finish: bool = False,
    ):
        super().__init__()
        activity = self.activity
        assert isinstance(activity, RumbleRushGame)
        self.index = index
        self.is_finish = is_finish

        self.node = bs.newnode(
            'region', delegate=self,
            attrs={
                'position': position,
                'scale': scale,
                'type': 'box',
                'materials': [activity.checkpoint_material],
            },
        )

        if is_finish:
            surface_y = 3.3
            self._finish_light = bs.newnode(
                'light',
                attrs={
                    'position': (position[0], surface_y + 1.0, position[2]),
                    'color': (0.2, 1.0, 0.2),
                    'intensity': 0.6,
                    'radius': 2.0,
                    'volume_intensity_scale': 0.0,
                    'height_attenuated': False,
                },
            )
            bs.animate(self._finish_light, 'intensity',
                       {0.0: 0.4, 1.0: 0.8, 2.0: 0.4}, loop=True)


# ────────────────────────────────────────────────────────────
#  HAZARD SPAWNER
# ────────────────────────────────────────────────────────────

class HazardSpawner:
    """Drops bombs near the leading player at a configurable interval."""

    def __init__(self, game: RumbleRushGame):
        self._game = weakref.ref(game)
        self._timer: bs.Timer | None = None

    def start(self, interval: float = 3.0) -> None:
        self._timer = bs.Timer(interval, self._spawn, repeat=True)

    def stop(self) -> None:
        self._timer = None

    def _spawn(self) -> None:
        game = self._game()
        if not game or game.has_ended():
            self._timer = None
            return

        lead_x = game.get_lead_player_x()
        if lead_x is None:
            return

        start_x = game.start_x
        finish_x = game.finish_x

        for _ in range(random.randint(1, 3)):
            x = max(start_x, min(
                lead_x + random.uniform(-2.0, 5.0), finish_x,
            ))
            z = random.uniform(-3.0, 3.0)
            y = random.uniform(8.0, 12.0)
            bomb_type = random.choice(['normal', 'normal', 'ice'])
            Bomb(position=(x, y, z), bomb_type=bomb_type).autoretain()


# ────────────────────────────────────────────────────────────
#  PLAYER / TEAM
# ────────────────────────────────────────────────────────────

class Player(bs.Player['Team']):
    """Rumble Rush player state."""

    def __init__(self) -> None:
        self.last_checkpoint: int = 0
        self.finished: bool = False
        self.rank: int | None = None
        self.finish_time: float | None = None
        self.distance: float = 0.0
        self.distance_txt: bs.Node | None = None


class Team(bs.Team[Player]):
    """Rumble Rush team state."""

    def __init__(self) -> None:
        self.time: float | None = None
        self.finished: bool = False


# ────────────────────────────────────────────────────────────
#  MAIN GAME
# ────────────────────────────────────────────────────────────

# ba_meta export bascenev1.GameActivity
class RumbleRushGame(bs.TeamGameActivity[Player, Team]):
    """A chaotic obstacle-course race!

    Navigate a grid of mystery tiles — bounce pads, ice, rumbling
    floors, and traps — while dodging falling bombs. First to the
    finish wins!
    """

    name = 'Rumble Rush'
    description = 'Survive the obstacle course and reach the finish!'
    scoreconfig = bs.ScoreConfig(
        label='Time',
        lower_is_better=True,
        scoretype=bs.ScoreType.MILLISECONDS,
    )

    # ── Settings ─────────────────────────────────────────────

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session],
    ) -> list[bs.Setting]:
        settings = [
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('5 Minutes', 300),
                    ('10 Minutes', 600),
                    ('20 Minutes', 1200),
                ],
                default=300,
            ),
            bs.FloatChoiceSetting(
                'Tile Gap', default=0.0,
                choices=[
                    ('None', 0.0), ('Small', 0.5), ('Medium', 1.0),
                    ('Large', 1.5), ('Extreme', 2.0),
                ],
            ),
            bs.IntChoiceSetting(
                'Hazards', default=0,
                choices=[
                    ('None', 0), ('Light', 5000),
                    ('Normal', 3000), ('Heavy', 1500),
                ],
            ),
            bs.BoolSetting('Epic Mode', default=False),
            bs.BoolSetting('Red Tile Respawn', default=True),
            bs.BoolSetting('Tile Labels', default=True),
            bs.BoolSetting('Memory Mode (Colors Fade Back)', default=True),
            bs.IntChoiceSetting(
                'Grid Width', default=6,
                choices=[(str(i), i) for i in range(1, 11)],
            ),
            bs.IntChoiceSetting(
                'Grid Depth', default=3,
                choices=[(str(i), i) for i in range(1, 11)],
            ),
            bs.BoolSetting('Player Collisions', default=False),
            bs.BoolSetting('Grabbing', default=False),
            bs.BoolSetting('Punching', default=False),
            bs.BoolSetting('Bombs', default=False),
            bs.BoolSetting('Green Tiles (Solid - Always Safe)', default=True),
            bs.BoolSetting('Blue Tiles (Bouncy - Launches You)', default=False),
            bs.BoolSetting('Cyan Tiles (Icy - Very Slippery)', default=False),
            bs.BoolSetting(
                'Orange Tiles (Rumble - Falls & Respawns)', default=False,
            ),
        ]

        # We have some specific settings in teams mode.
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(
                bs.BoolSetting('Entire Team Must Finish', default=False)
            )
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.MultiTeamSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Rumble Course']

    # ── Init ─────────────────────────────────────────────────

    def __init__(self, settings: dict):
        self._race_started = False
        super().__init__(settings)

        # Read settings.
        self._tile_gap = float(settings.get('Tile Gap', 0.0))
        self._time_limit = float(settings.get('Time Limit', 300))
        self._hazard_interval = int(settings.get('Hazards', 0))
        self._epic_mode = bool(settings['Epic Mode'])
        self._red_respawn = bool(settings.get('Red Tile Respawn', True))
        self._tile_labels = bool(settings.get('Tile Labels', True))
        self._memory_mode = bool(
            settings.get('Memory Mode (Colors Fade Back)', True),
        )
        self._enable_grabbing = bool(settings.get('Grabbing', False))
        self._enable_punching = bool(settings.get('Punching', False))
        self._enable_bombs = bool(settings.get('Bombs', False))
        self._grid_width = int(settings.get('Grid Width', 6))
        self._grid_depth = int(settings.get('Grid Depth', 3))
        self._player_collisions = bool(
            settings.get('Player Collisions', False),
        )
        self._entire_team_must_finish = bool(
            settings.get('Entire Team Must Finish', False)
        )

        # Build list of enabled safe tile types.
        _TILE_SETTINGS = [
            ('Green Tiles (Solid - Always Safe)', PlatformType.SOLID, True),
            ('Blue Tiles (Bouncy - Launches You)', PlatformType.BOUNCY, False),
            ('Cyan Tiles (Icy - Very Slippery)', PlatformType.ICY, False),
            ('Orange Tiles (Rumble - Falls & Respawns)',
             PlatformType.RUMBLING, False),
        ]
        self._safe_types = [
            pt for key, pt, default in _TILE_SETTINGS
            if bool(settings.get(key, default))
        ] or [PlatformType.SOLID]

        # Course geometry (updated in _generate_course).
        tile_w = RumblePlatform.TILE_W
        step_x = tile_w + self._tile_gap
        step_z = RumblePlatform.TILE_D + self._tile_gap
        half_cols = self._grid_width / 2.0
        self._start_x: float = -(step_x * half_cols + tile_w * 0.5)
        self._finish_x: float = (
            self._start_x + (self._grid_width + 1) * step_x
        )
        half_rows = (self._grid_depth - 1) / 2.0
        self._zone_depth: float = half_rows * 2 * step_z + RumblePlatform.TILE_D

        # Timing.
        self._start_time: float | None = None
        self._last_team_time: float | None = None
        self._finish_order: int = 0

        # Object storage.
        self._scoreboard = Scoreboard()
        self._platforms: list[RumblePlatform] = []
        self._checkpoints: list[CheckpointRegion] = []
        self._hazard_spawner: HazardSpawner | None = None
        self._zone_nodes: list[bs.Node] = []
        self._finish_flags: list[Flag] = []

        # Update timers.
        self._scoreboard_timer: bs.Timer | None = None
        self._order_update_timer: bs.Timer | None = None
        self._timer_update: bs.Timer | None = None

        # Checkpoint material (created in on_transition_in).
        self.checkpoint_material: bs.Material | None = None

        # Pre-load sounds & textures.
        self._score_sound = bs.getsound('score')
        self._swip_sound = bs.getsound('swip')
        self._tick_sound = bs.getsound('tick')
        self._beep1 = bs.getsound('raceBeep1')
        self._beep2 = bs.getsound('raceBeep2')
        self._nub_tex = bs.gettexture('nub')

        # Start-light nodes.
        self._start_lights: list[bs.Node] = []

        # Timer HUD.
        self._time_text: bs.Actor | None = None

        # Epic mode.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC_RACE if self._epic_mode else bs.MusicType.RACE
        )

    # ── Public Properties ────────────────────────────────────

    @property
    def start_x(self) -> float:
        return self._start_x

    @property
    def finish_x(self) -> float:
        return self._finish_x

    @override
    def get_instance_description(self) -> str | Sequence:
        if (
            isinstance(self.session, bs.DualTeamSession)
            and self._entire_team_must_finish
        ):
            return 'Reach the finish line! Your entire team has to finish.'
        return 'Reach the finish line!'

    @override
    def get_instance_description_short(self) -> str | Sequence:
        if (
            isinstance(self.session, bs.DualTeamSession)
            and self._entire_team_must_finish
        ):
            return 'reach the finish! (entire team)'
        return 'reach the finish!'

    # ── Course Generation ────────────────────────────────────

    def _generate_course(self) -> None:
        """Build the grid of mystery tiles plus start/finish zones."""
        tile_w = RumblePlatform.TILE_W
        tile_d = RumblePlatform.TILE_D
        gap = self._tile_gap
        base_y = 3.0
        num_cols = self._grid_width
        num_rows = self._grid_depth

        step_x = tile_w + gap
        step_z = tile_d + gap
        half_rows = (num_rows - 1) / 2.0
        rows_z = [(r - half_rows) * step_z for r in range(num_rows)]
        zone_depth = half_rows * 2 * step_z + tile_d

        # Start zone (white).
        half_cols = num_cols / 2.0
        start_x = -(step_x * half_cols + tile_w * 0.5)
        self._create_zone_platform(
            position=(start_x, base_y, 0.0),
            width=tile_w, depth=zone_depth,
            color=(0.9, 0.9, 0.9),
        )

        # Main grid.
        grid_start_x = start_x + step_x
        prev_green_row: int | None = None
        same_row_streak = 0

        for col in range(num_cols):
            x = grid_start_x + col * step_x

            if prev_green_row is None:
                green_row = random.randint(0, num_rows - 1)
            else:
                candidates = [
                    r for r in range(num_rows)
                    if abs(r - prev_green_row) <= 1
                ]
                if same_row_streak >= 2:
                    candidates = [
                        r for r in candidates if r != prev_green_row
                    ]
                green_row = random.choice(candidates or [prev_green_row])

            same_row_streak = (
                same_row_streak + 1
                if prev_green_row is not None and green_row == prev_green_row
                else 1
            )
            prev_green_row = green_row

            for row_idx, z in enumerate(rows_z):
                ptype = (
                    random.choice(self._safe_types)
                    if row_idx == green_row
                    else PlatformType.DISAPPEARING
                )
                plat = RumblePlatform(
                    position=(x, base_y, z),
                    ptype=ptype,
                    game=self,
                )
                plat.autoretain()
                self._platforms.append(plat)

        # Finish zone (green).
        finish_x = grid_start_x + num_cols * step_x
        self._create_zone_platform(
            position=(finish_x, base_y, 0.0),
            width=tile_w, depth=zone_depth,
            color=(0.3, 0.8, 0.3),
        )

        self._finish_x = finish_x
        self._start_x = start_x
        self._zone_depth = zone_depth

        # Update map / camera bounds to fit the actual grid size.
        course_center_x = (start_x + finish_x) / 2.0
        course_span_x = finish_x - start_x + tile_w * 4
        course_span_z = zone_depth + 6.0
        map_cls = type(self.map)
        map_cls.defs.boxes['area_of_interest_bounds'] = (
            (course_center_x, 3.5, 0.0)
            + (0.0, 0.0, 0.0)
            + (course_span_x, 10.0, course_span_z)
        )
        map_cls.defs.boxes['map_bounds'] = (
            (course_center_x, 3.5, 0.0)
            + (0.0, 0.0, 0.0)
            + (course_span_x + 8.0, 20.0, course_span_z + 8.0)
        )

        # Widen the death region to cover the full course.
        if hasattr(self.map, 'death_region') and self.map.death_region:
            self.map.death_region.position = (course_center_x, 0.0, 0.0)
            self.map.death_region.scale = (
                course_span_x + 12.0, 2.0, course_span_z + 8.0,
            )

        self._create_checkpoints()
        self._add_finish_flags()

    def _create_zone_platform(
        self,
        position: tuple[float, float, float],
        width: float, depth: float,
        color: tuple[float, float, float],
    ) -> None:
        """Create a single large rectangular start/finish platform."""
        shared = SharedObjects.get()
        height = RumblePlatform.TILE_H

        mat = bs.Material()
        for mat_tag in (shared.player_material, shared.object_material):
            mat.add_actions(
                conditions=('they_have_material', mat_tag),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'physical', True),
                ),
            )

        region = bs.newnode(
            'region',
            attrs={
                'position': position,
                'scale': (width, height, depth),
                'type': 'box',
                'materials': [shared.footing_material, mat],
            },
        )
        self._zone_nodes.append(region)

        shrink = RumblePlatform.VIS_SHRINK
        bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': position,
                'color': color,
                'opacity': 0.9,
                'draw_beauty': True,
                'additive': False,
                'size': [width - shrink, height, depth - shrink],
            },
        )
        bs.newnode(
            'light',
            attrs={
                'position': position,
                'color': color,
                'intensity': 0.4,
                'radius': 1.5,
                'volume_intensity_scale': 0.0,
                'height_attenuated': False,
            },
        )

    def _create_checkpoints(self) -> None:
        """Space 3 checkpoints + a finish gate along the course."""
        span = self._finish_x - self._start_x
        tile_w = RumblePlatform.TILE_W
        zone_d = self._zone_depth

        for i, frac in enumerate([0.25, 0.50, 0.75, 1.0]):
            x = self._start_x + span * frac
            is_finish = (frac == 1.0)
            pos = (x, 3.8 if is_finish else 4.5, 0.0)
            scale = (
                (tile_w * 0.8, 2.0, zone_d) if is_finish
                else (3.0, 6.0, 8.0)
            )
            cp = CheckpointRegion(
                position=pos, scale=scale, index=i, is_finish=is_finish,
            )
            cp.autoretain()
            self._checkpoints.append(cp)

    def _add_finish_flags(self) -> None:
        """Place green flags on either side of the finish zone."""
        half_d = self._zone_depth * 0.5
        for z_off in [-(half_d - 0.3), (half_d - 0.3)]:
            flag = Flag(
                position=(self._finish_x, 3.5, z_off),
                color=(0.2, 1.0, 0.2),
                touchable=False,
            )
            flag.autoretain()
            self._finish_flags.append(flag)

    # ── Game Lifecycle ───────────────────────────────────────

    @override
    def on_transition_in(self) -> None:
        super().on_transition_in()
        shared = SharedObjects.get()
        mat = self.checkpoint_material = bs.Material()
        mat.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._handle_checkpoint_collide),
            ),
        )

        # Player no-collide material — applied when Player Collisions is off.
        # Makes players phase through each other physically.
        # Matches pacman.py approach: only collide:False (no physical flag),
        # single condition, single action.
        self._no_player_collide_material = bs.Material()
        if not self._player_collisions:
            self._no_player_collide_material.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=('modify_part_collision', 'collide', False),
            )

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self._generate_course()

        # Timer HUD.
        self._time_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'center',
                    'h_align': 'center',
                    'color': (1, 1, 0.5, 1),
                    'flatness': 0.5,
                    'shadow': 0.5,
                    'position': (0, -50),
                    'scale': 1.4,
                    'text': '0:00.00',
                },
            )
        )

        # Periodic updates.
        self._scoreboard_timer = bs.Timer(
            0.25, self._update_scoreboard, repeat=True,
        )
        self._order_update_timer = bs.Timer(
            0.25, self._update_player_order, repeat=True,
        )

        # Countdown start sequence.
        t_scale = 0.4 if self.slow_motion else 1.0
        light_y = 50 if self.slow_motion else 150
        lstart = 7.1 * t_scale
        inc = 1.25 * t_scale

        bs.timer(lstart, self._do_light_1)
        bs.timer(lstart + inc, self._do_light_2)
        bs.timer(lstart + 2 * inc, self._do_light_3)
        bs.timer(lstart + 3 * inc, self._start_race)

        self._start_lights = []
        colors = [(0.2, 0, 0), (0.2, 0, 0), (0.2, 0.05, 0), (0.0, 0.3, 0)]
        for i, c in enumerate(colors):
            lnub = bs.newnode(
                'image',
                attrs={
                    'texture': self._nub_tex,
                    'opacity': 1.0,
                    'absolute_scale': True,
                    'position': (-75 + i * 50, light_y),
                    'scale': (50, 50),
                    'attach': 'center',
                    'color': c,
                },
            )
            bs.animate(lnub, 'opacity', {
                4.0 * t_scale: 0,
                5.0 * t_scale: 1.0,
                12.0 * t_scale: 1.0,
                12.5 * t_scale: 0.0,
            })
            bs.timer(13.0 * t_scale, lnub.delete)
            self._start_lights.append(lnub)

    # ── Countdown Lights ─────────────────────────────────────

    def _do_light_1(self) -> None:
        self._start_lights[0].color = (1.0, 0, 0)
        self._beep1.play()

    def _do_light_2(self) -> None:
        self._start_lights[1].color = (1.0, 0, 0)
        self._beep1.play()

    def _do_light_3(self) -> None:
        self._start_lights[2].color = (1.0, 0.3, 0)
        self._beep1.play()

    def _start_race(self) -> None:
        """Green light — connect controls and start the clock."""
        self._start_lights[3].color = (0.0, 1.0, 0)
        self._beep2.play()

        for player in self.players:
            if player.actor is not None:
                try:
                    assert isinstance(player.actor, PlayerSpaz)
                    player.actor.connect_controls_to_player(
                        enable_pickup=self._enable_grabbing,
                        enable_punch=self._enable_punching,
                        enable_bomb=self._enable_bombs,
                    )
                except Exception:
                    logging.exception('Error connecting player controls.')

        self._start_time = bs.time()
        self._race_started = True
        self._timer_update = bs.Timer(
            0.05, self._update_time, repeat=True,
        )

        if self._hazard_interval > 0:
            self._hazard_spawner = HazardSpawner(self)
            self._hazard_spawner.start(
                interval=self._hazard_interval * 0.001,
            )

    def _update_time(self) -> None:
        """Update the on-screen race timer."""
        if self._start_time is None:
            return
        elapsed = bs.time() - self._start_time
        minutes = int(elapsed) // 60
        seconds = elapsed - minutes * 60
        if self._time_text and self._time_text.node:
            self._time_text.node.text = f'{minutes}:{seconds:05.2f}'

    # ── Checkpoint Handling ──────────────────────────────────

    def _handle_checkpoint_collide(self) -> None:
        """Called when a player enters a checkpoint region."""
        try:
            region = bs.getcollision().sourcenode.getdelegate(
                CheckpointRegion, True,
            )
            spaz = bs.getcollision().opposingnode.getdelegate(
                PlayerSpaz, True,
            )
        except bs.NotFoundError:
            return

        if not spaz.is_alive():
            return
        try:
            player = spaz.getplayer(Player, True)
        except bs.NotFoundError:
            return
        if player.finished:
            return

        cp_index = region.index

        # Anti-skip: don't let players jump more than 1 checkpoint ahead.
        if cp_index > player.last_checkpoint + 2:
            if player.is_alive():
                assert player.actor
                player.actor.handlemessage(bs.DieMessage())
                bs.broadcastmessage(
                    bs.Lstr(
                        translate=(
                            'statements',
                            'Killing ${NAME} for skipping'
                            ' part of the course!',
                        ),
                        subs=[('${NAME}', player.getname(full=True))],
                    ),
                    color=(1, 0, 0),
                )
            return

        if cp_index > player.last_checkpoint:
            player.last_checkpoint = cp_index
            self._tick_sound.play()

        if region.is_finish and not player.finished:
            self._player_finished(player)

    def _player_finished(self, player: Player) -> None:
        """Handle a player crossing the finish line."""
        self._finish_order += 1
        player.finished = True
        player.rank = self._finish_order
        assert self._start_time is not None
        player.finish_time = bs.time() - self._start_time

        self._score_sound.play()

        # Flash of light on the player.
        if isinstance(player.actor, PlayerSpaz) and player.actor.node:
            pos = player.actor.node.position
            light = bs.newnode(
                'light',
                attrs={
                    'position': pos,
                    'color': (1, 1, 0),
                    'height_attenuated': False,
                    'radius': 0.5,
                },
            )
            bs.timer(0.6, light.delete)
            bs.animate(light, 'intensity', {0: 0, 0.1: 1.5, 0.6: 0})

        assert player.actor
        player.actor.handlemessage(bs.DieMessage(immediate=True))
        player.distance = 99999.0

        # Check team completion.
        team = player.team
        if isinstance(self.session, bs.DualTeamSession):
            if self._entire_team_must_finish:
                # All players on the team must cross the finish.
                team_done = all(p.finished for p in team.players)
            else:
                # First player across wins it for the team.
                team_done = True
        else:
            # FFA: each player is their own team.
            team_done = all(p.finished for p in team.players)

        if team_done:
            team.finished = True
            team.time = player.finish_time
            self._last_team_time = team.time
            self._check_end_game()
        else:
            self._swip_sound.play()

    # ── Player Order / Distance ──────────────────────────────

    def _update_player_order(self) -> None:
        """Update distance tracking and rank display."""
        for player in self.players:
            if player.finished:
                continue
            try:
                pos = player.position
            except bs.NotFoundError:
                continue
            player.distance = pos.x + abs(pos.z) * 0.001

        ranked = sorted(self.players, key=lambda p: p.distance, reverse=True)
        for i, plr in enumerate(ranked):
            plr.rank = i + 1
            if plr.distance_txt:
                plr.distance_txt.text = (
                    str(plr.rank) if plr.is_alive() else ''
                )

    def _update_scoreboard(self) -> None:
        """Update progress bars on the scoreboard."""
        span = self._finish_x - self._start_x
        for team in self.teams:
            distances = [p.distance for p in team.players]
            if not distances:
                best = 0.0
            elif (
                isinstance(self.session, bs.DualTeamSession)
                and self._entire_team_must_finish
            ):
                best = min(distances)
            else:
                best = max(distances)
            progress = min(1.0, max(
                0.0, (best - self._start_x) / span,
            ))
            self._scoreboard.set_team_value(
                team, progress, 1.0,
                flash=(progress >= 1.0), show_value=False,
            )

    def get_lead_player_x(self) -> float | None:
        """Return the X position of the leading alive player."""
        best: float | None = None
        for p in self.players:
            if p.finished or not p.is_alive():
                continue
            try:
                px = p.position.x
                if best is None or px > best:
                    best = px
            except bs.NotFoundError:
                continue
        return best

    # ── Spawn / Death ────────────────────────────────────────

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        if player.team.finished:
            return None  # type: ignore

        step_z = RumblePlatform.TILE_D + self._tile_gap
        half_rows = (self._grid_depth - 1) / 2.0
        spawn_z_choices = [
            (r - half_rows) * step_z for r in range(self._grid_depth)
        ]
        spawn_z = random.choice(spawn_z_choices)
        spawn_pos = (self._start_x, 4.0, spawn_z)

        spaz = self.spawn_player_spaz(
            player, position=spawn_pos, angle=0,
        )
        assert spaz.node

        # Apply no-collide material to all relevant node slots so players
        # phase through each other — matches pacman.py exactly.
        if not self._player_collisions and spaz.node:
            try:
                for slot in ['materials', 'roller_materials',
                             'extras_material']:
                    mats = list(getattr(spaz.node, slot))
                    mats.append(self._no_player_collide_material)
                    setattr(spaz.node, slot, mats)
            except Exception:
                pass

        if not self._race_started:
            spaz.disconnect_controls_from_player()
        else:
            spaz.disconnect_controls_from_player()
            spaz.connect_controls_to_player(
                enable_pickup=self._enable_grabbing,
                enable_punch=self._enable_punching,
                enable_bomb=self._enable_bombs,
            )

        # Rank text above head.
        mathnode = bs.newnode(
            'math', owner=spaz.node,
            attrs={'input1': (0, 1.4, 0), 'operation': 'add'},
        )
        spaz.node.connectattr('torso_position', mathnode, 'input2')
        txt = bs.newnode(
            'text', owner=spaz.node,
            attrs={
                'text': '',
                'in_world': True,
                'color': (1, 1, 0.4),
                'scale': 0.02,
                'h_align': 'center',
            },
        )
        player.distance_txt = txt
        mathnode.connectattr('output', txt, 'position')
        return spaz

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            if not player.finished:
                player.last_checkpoint = 0
                self.respawn_player(player, respawn_time=1.5)
        else:
            super().handlemessage(msg)

    # ── End Game ─────────────────────────────────────────────

    def _check_end_game(self) -> None:
        """Determine whether enough teams have finished to end."""
        active = [t for t in self.teams if not t.finished]
        done = [t for t in self.teams if t.finished and t.time is not None]

        if not active:
            self.end_game()
        elif done:
            session = self.session
            if isinstance(session, bs.DualTeamSession):
                self.end_game()
            else:
                assert isinstance(session, bs.FreeForAllSession)
                pts = len(session.get_ffa_point_awards())
                if len(done) >= pts - len(done):
                    self.end_game()

    @override
    def end_game(self) -> None:
        if self._hazard_spawner:
            self._hazard_spawner.stop()
        self._timer_update = None

        # Freeze the timer display.
        if (
            self._last_team_time is not None
            and self._time_text and self._time_text.node
        ):
            m = int(self._last_team_time) // 60
            s = self._last_team_time - m * 60
            self._time_text.node.text = f'{m}:{s:05.2f}'

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(
                team,
                int(team.time * 1000.0) if team.time is not None else None,
            )
        self.end(
            results=results,
            announce_winning_team=isinstance(
                self.session, bs.DualTeamSession,
            ),
        )

    @override
    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    @override
    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)

        # A player leaving disqualifies the team if 'Entire Team Must
        # Finish' is on (otherwise everyone could leave except the
        # leading player to win).
        if (
            isinstance(self.session, bs.DualTeamSession)
            and self._entire_team_must_finish
        ):
            bs.broadcastmessage(
                bs.Lstr(
                    translate=(
                        'statements',
                        '${TEAM} is disqualified because'
                        ' ${PLAYER} left',
                    ),
                    subs=[
                        ('${TEAM}', player.team.name),
                        ('${PLAYER}', player.getname(full=True)),
                    ],
                ),
                color=(1, 1, 0),
            )
            player.team.finished = True
            player.team.time = None
            bs.getsound('boo').play()
            for otherplayer in player.team.players:
                otherplayer.finished = True
                try:
                    if otherplayer.actor is not None:
                        otherplayer.actor.handlemessage(bs.DieMessage())
                except Exception:
                    logging.exception('Error sending DieMessage.')

        bs.pushcall(self._check_end_game)
