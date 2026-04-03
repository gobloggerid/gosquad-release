# Released under the MIT License. See LICENSE for details.
#
"""Flappy Spaz - dodge moving TNT pipes as long as you can!"""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs
import babase

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------

PLAY_Z = -6.0
PLAY_Z_DEPTH = 6.0

PLAY_X_MIN = -12.0
PLAY_X_MAX = 12.0
PLAY_Y_MIN = 1.0
PLAY_Y_MAX = 14.0

PIPE_SPAWN_X = PLAY_X_MAX + 3.0
PIPE_DELETE_X = PLAY_X_MIN - 3.0

UPDATE_INTERVAL = 1.0 / 30.0

NUM_CHANNELS = 8
CHANNEL_WIDTH = 1.0
WALL_THICKNESS = 0.15

# The lowest internal pipe speed (3.0) is displayed as "1.0".
SPEED_OFFSET = 2.0


# ---------------------------------------------------------------------------
#  Pipe Pair (obstacle only — no scoring regions)
# ---------------------------------------------------------------------------


class CameraAnchor(bs.Actor):
    """Invisible physics prop used to pin the camera.

    Handles OutOfBoundsMessage so the engine doesn't spam warnings
    when the tiny sphere drifts outside map bounds.
    """

    def __init__(
        self,
        position: Sequence[float],
        materials: list[bs.Material],
    ):
        super().__init__()
        self.node: bs.Node = bs.newnode('prop', delegate=self, attrs={
            'position': position,
            'velocity': (0, 0, 0),
            'body': 'sphere',
            'body_scale': 0.01,
            'mesh': None,
            'light_mesh': None,
            'shadow_size': 0.0,
            'is_area_of_interest': True,
            'materials': materials,
        })

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.OutOfBoundsMessage):
            # Just nudge it back to center — don't delete.
            if self.node:
                cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
                cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0
                self.node.position = (cx, cy, PLAY_Z)
            return None
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
            return None
        return super().handlemessage(msg)


class _PipeBoxDelegate:
    """Lightweight delegate for pipe-crate prop nodes.

    Handles OutOfBoundsMessage so the engine doesn't spam warnings
    when a box drifts outside map bounds.
    """

    def __init__(self) -> None:
        self.node: bs.Node | None = None

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.OutOfBoundsMessage):
            if self.node:
                self.node.delete()
            return None
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
            return None
        return None


class PipePair:
    """A pair of TNT-crate columns with a gap for the player to fly
    through."""

    def __init__(
        self,
        x_pos: float,
        gap_center_y: float,
        gap_size: float,
        box_scale: float,
        box_spacing: float,
        speed: float,
        pipe_material: bs.Material,
        score_material: bs.Material,
    ):
        self.x_pos = x_pos
        self._gap_center_y = gap_center_y
        self._gap_size = gap_size
        self._alive = True
        self._speed = speed
        self.scored_players: set[int] = set()

        self._boxes: list[bs.Node] = []
        self._box_delegates: list[_PipeBoxDelegate] = []
        self._box_targets_y: list[float] = []

        step = box_scale + box_spacing
        tnt_mesh = bs.getmesh('tnt')
        tnt_tex = bs.gettexture('tnt')

        gap_top = gap_center_y + gap_size / 2.0
        gap_bottom = gap_center_y - gap_size / 2.0

        # Top column.
        y = gap_top + box_scale / 2.0
        while y - box_scale / 2.0 < PLAY_Y_MAX + box_scale:
            self._spawn_box(
                x_pos, y, box_scale, speed,
                tnt_mesh, tnt_tex, pipe_material,
            )
            y += step

        # Bottom column.
        y = gap_bottom - box_scale / 2.0
        while y + box_scale / 2.0 > PLAY_Y_MIN - box_scale:
            self._spawn_box(
                x_pos, y, box_scale, speed,
                tnt_mesh, tnt_tex, pipe_material,
            )
            y -= step

        # Score region in the gap — detects players passing through.
        self.score_region: bs.Node = bs.newnode('region', attrs={
            'position': (x_pos, gap_center_y, PLAY_Z),
            'scale': (0.5, gap_size * 0.8, PLAY_Z_DEPTH),
            'type': 'box',
            'materials': [score_material],
        })

    def _spawn_box(
        self,
        x: float, y: float, scale: float, speed: float,
        mesh: bs.Mesh, tex: bs.Texture, mat: bs.Material,
    ) -> None:
        delegate = _PipeBoxDelegate()
        node = bs.newnode('prop', delegate=delegate, attrs={
            'position': (x, y, PLAY_Z),
            'velocity': (-speed, 0, 0),
            'mesh': mesh,
            'light_mesh': mesh,
            'body': 'crate',
            'body_scale': scale,
            'shadow_size': 0.0,
            'color_texture': tex,
            'reflection': 'soft',
            'reflection_scale': [0.23],
            'materials': [mat],
            'is_area_of_interest': False,
        })
        delegate.node = node
        self._boxes.append(node)
        self._box_delegates.append(delegate)
        self._box_targets_y.append(y)

    def update(self, speed: float) -> None:
        """Correct drift on boxes, move score region, and track x."""
        if not self._alive:
            return
        actual_x: float | None = None
        for i, node in enumerate(self._boxes):
            try:
                pos = node.position
                if actual_x is None:
                    actual_x = pos[0]
                node.velocity = (
                    -speed,
                    (self._box_targets_y[i] - pos[1]) * 30.0,
                    (PLAY_Z - pos[2]) * 30.0,
                )
            except Exception:
                pass
        # Use actual box x so the region stays perfectly aligned
        # with the crates (rather than drifting from math rounding).
        if actual_x is not None:
            self.x_pos = actual_x
        else:
            self.x_pos -= speed * UPDATE_INTERVAL
        # Region nodes don't have velocity — reposition each tick.
        try:
            self.score_region.position = (
                self.x_pos, self._gap_center_y, PLAY_Z,
            )
        except Exception:
            pass

    def freeze(self) -> None:
        """Stop all boxes in place (zero velocity)."""
        if not self._alive:
            return
        for node in self._boxes:
            try:
                node.velocity = (0, 0, 0)
            except Exception:
                pass
        self._alive = False

    def delete(self) -> None:
        """Remove all nodes belonging to this pipe pair."""
        self._alive = False
        for n in self._boxes:
            try:
                n.delete()
            except Exception:
                pass
        self._boxes.clear()
        self._box_delegates.clear()
        try:
            self.score_region.delete()
        except Exception:
            pass


# ---------------------------------------------------------------------------
#  Player / Team
# ---------------------------------------------------------------------------


class Player(bs.Player['Team']):
    """Flappy Spaz player."""

    def __init__(self) -> None:
        super().__init__()
        self.lane_idx: int = 0
        self.pipes_passed: int = 0


class Team(bs.Team[Player]):
    """Flappy Spaz team."""

    def __init__(self) -> None:
        super().__init__()
        self.score: int = 0


# ---------------------------------------------------------------------------
#  Game
# ---------------------------------------------------------------------------


# ba_meta export bascenev1.GameActivity
class FlappySpazGame(bs.TeamGameActivity[Player, Team]):
    """Dodge moving TNT pipes and score points!"""

    name = 'Flappy Spaz'
    description = 'Fly through as many pipes as you can!'

    scoreconfig = bs.ScoreConfig(
        label='Score',
        scoretype=bs.ScoreType.POINTS,
        version='B',
    )

    # Print messages when players die.
    announce_player_deaths = True

    # Don't allow joining after start (prevents leave/rejoin abuse).
    allow_mid_activity_joins = False

    # -- Settings --

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session],
    ) -> list[bs.Setting]:
        return [
            bs.FloatChoiceSetting(
                'Gap Size',
                choices=[
                    ('Tiny', 2.5), ('Small', 3.0), ('Normal', 3.5),
                    ('Large', 4.5), ('Huge', 6.0),
                ],
                default=3.5,
            ),
            bs.FloatChoiceSetting(
                'Pipe Spacing',
                choices=[
                    ('Close', 6.0), ('Normal', 9.0),
                    ('Far', 12.0), ('Very Far', 15.0),
                ],
                default=6.0,
            ),
            bs.FloatChoiceSetting(
                'Starting Speed',
                choices=[
                    ('1.0', 3.0), ('2.0', 4.0), ('3.0', 5.0),
                    ('4.0', 6.0), ('5.0', 7.0), ('6.0', 8.0),
                    ('7.0', 9.0), ('8.0', 10.0),
                ],
                default=3.0,
            ),
            bs.BoolSetting('Score Sound', default=False),
            bs.BoolSetting('Epic Mode', default=False),
        ]

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(
            sessiontype,
            (bs.DualTeamSession, bs.FreeForAllSession, bs.CoopSession),
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Flappy Spaz Sky']

    # -- Init --

    def __init__(self, settings: dict):
        super().__init__(settings)

        # Settings.
        self._gap_size: float = float(settings.get('Gap Size', 3.5))
        self._pipe_spacing: float = float(settings.get('Pipe Spacing', 6.0))
        self._pipe_speed: float = float(settings.get('Starting Speed', 3.0))
        self._box_scale: float = 0.6      # Locked: Small.
        self._box_spacing: float = 0.05   # Locked: Tight.
        self._epic_mode: bool = bool(settings.get('Epic Mode', False))
        self._score_sound_enabled: bool = bool(
            settings.get('Score Sound', False)
        )

        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )

        # State.
        self._pipes: list[PipePair] = []
        self._update_timer: bs.Timer | None = None
        self._speed_timer: bs.Timer | None = None
        self._game_started = False
        self._ended = False
        self._countdown_text: bs.Node | None = None
        self._speed_text: bs.Node | None = None
        self._speed_color_combine: bs.Node | None = None
        self._starting_speed: float = self._pipe_speed
        self._platform_region: bs.Node | None = None
        self._camera_anchor: CameraAnchor | None = None
        self._channel_centers: list[float] = []

        # Materials (created in on_begin).
        self._ghost_material: bs.Material | None = None
        self._pipe_material: bs.Material | None = None
        self._death_material: bs.Material | None = None
        self._wall_material: bs.Material | None = None
        self._score_region_material: bs.Material | None = None

        # Scoreboard.
        self._scoreboard = Scoreboard()
        self._score_sound = bs.getsound('score')

    @override
    def get_instance_description(self) -> str | Sequence:
        return 'Fly through as many pipes as you can!'

    @override
    def get_instance_description_short(self) -> str | Sequence:
        return 'score points!'

    # -- Lifecycle --

    @override
    def on_team_join(self, team: Team) -> None:
        super().on_team_join(team)
        self._update_scoreboard()

    @override
    def on_player_join(self, player: Player) -> None:
        if self._game_started or not self.has_begun():
            return
        self.spawn_player(player)

    @override
    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        # A departing player may trigger game-over.
        self._check_end_game()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        shared = SharedObjects.get()
        self.globalsnode.happy_thoughts_mode = True

        self._create_materials(shared)
        self._create_camera_anchor()
        self._create_borders()
        self._create_lanes(shared)
        self._create_platform(shared)

        # Main tick loop.
        self._update_timer = bs.Timer(
            UPDATE_INTERVAL, self._update, repeat=True,
        )

        # Speed ramp: increase speed by 5% periodically.
        ramp_interval = 2.5 if self._epic_mode else 10.0
        self._speed_timer = bs.Timer(
            ramp_interval, self._ramp_speed, repeat=True,
        )

        # Spawn all players onto the platform.
        for player in self.players:
            self.spawn_player(player)

        # 2-second orient delay, then 3-second countdown.
        bs.timer(2.0, self._start_countdown)

    # -- Materials --

    def _create_materials(self, shared: SharedObjects) -> None:
        # Ghost: collides with nothing (camera anchor).
        self._ghost_material = bs.Material()
        self._ghost_material.add_actions(
            actions=('modify_part_collision', 'collide', False),
        )

        # Pipe prop: no-collide by default, kills players on touch.
        # Physical is False so the player impact doesn't scatter crates.
        self._pipe_material = bs.Material()
        self._pipe_material.add_actions(
            actions=('modify_part_collision', 'collide', False),
        )
        self._pipe_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'their_node', 'at_connect', bs.DieMessage()),
            ),
        )

        # Death border: kills on contact (non-physical).
        self._death_material = bs.Material()
        self._death_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'their_node', 'at_connect', bs.DieMessage()),
            ),
        )

        # Lane wall: blocks players only.
        self._wall_material = bs.Material()
        self._wall_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )

        # Score region: detects players passing through pipe gaps.
        self._score_region_material = bs.Material()
        self._score_region_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._on_score_region_enter),
            ),
        )

    # -- Arena Setup --

    def _create_camera_anchor(self) -> None:
        cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
        cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0
        self._camera_anchor = CameraAnchor(
            position=(cx, cy, PLAY_Z),
            materials=[self._ghost_material],
        ).autoretain()
        hw = (PLAY_X_MAX - PLAY_X_MIN) / 2.0
        hh = (PLAY_Y_MAX - PLAY_Y_MIN) / 2.0
        self.globalsnode.area_of_interest_bounds = (
            cx - hw, cy - hh, PLAY_Z - 0.5,
            cx + hw, cy + hh, PLAY_Z + 0.5,
        )

    def _create_borders(self) -> None:
        cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
        cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0
        w = PLAY_X_MAX - PLAY_X_MIN
        h = PLAY_Y_MAX - PLAY_Y_MIN
        t = 0.8

        walls = [
            ((cx, PLAY_Y_MAX + t / 2, PLAY_Z),
             (w + t * 2, t, PLAY_Z_DEPTH)),
            ((cx, PLAY_Y_MIN - t / 2, PLAY_Z),
             (w + t * 2, t, PLAY_Z_DEPTH)),
            ((PLAY_X_MIN - t / 2, cy, PLAY_Z),
             (t, h + t * 2, PLAY_Z_DEPTH)),
            ((PLAY_X_MAX + t / 2, cy, PLAY_Z),
             (t, h + t * 2, PLAY_Z_DEPTH)),
        ]
        for pos, scl in walls:
            bs.newnode('region', attrs={
                'position': pos,
                'scale': scl,
                'type': 'box',
                'materials': [self._death_material],
            })

    def _create_lanes(self, shared: SharedObjects) -> None:
        cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
        wall_h = PLAY_Y_MAX - PLAY_Y_MIN + 4.0
        wall_cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0

        self._channel_centers = [
            cx - i * CHANNEL_WIDTH for i in range(NUM_CHANNELS)
        ]

        for i in range(NUM_CHANNELS + 1):
            wx = cx + CHANNEL_WIDTH / 2.0 - i * CHANNEL_WIDTH
            bs.newnode('region', attrs={
                'position': (wx, wall_cy, PLAY_Z),
                'scale': (WALL_THICKNESS, wall_h, PLAY_Z_DEPTH),
                'type': 'box',
                'materials': [shared.footing_material, self._wall_material],
            })

    def _create_platform(self, shared: SharedObjects) -> None:
        cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
        cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0
        lanes_cx = cx - (NUM_CHANNELS - 1) * CHANNEL_WIDTH / 2.0
        total_w = NUM_CHANNELS * CHANNEL_WIDTH + 2.0

        self._platform_region = bs.newnode('region', attrs={
            'position': (lanes_cx, cy, PLAY_Z),
            'scale': (total_w, 0.3, PLAY_Z_DEPTH),
            'type': 'box',
            'materials': [shared.footing_material, self._wall_material],
        })

    # -- Countdown --

    def _start_countdown(self) -> None:
        self._countdown_text = bs.newnode('text', attrs={
            'v_attach': 'center',
            'h_attach': 'center',
            'h_align': 'center',
            'v_align': 'center',
            'position': (0, 0),
            'scale': 2.0,
            'color': (0.2, 1.0, 0.2, 1.0),
            'flatness': 0.5,
            'shadow': 0.5,
            'text': '3',
        })
        self._countdown_sounds = {
            3: bs.getsound('announceThree'),
            2: bs.getsound('announceTwo'),
            1: bs.getsound('announceOne'),
        }
        self._countdown_sounds[3].play()
        bs.getsound('tick').play()
        bs.timer(1.0, bs.CallStrict(self._countdown_tick, 2))
        bs.timer(2.0, bs.CallStrict(self._countdown_tick, 1))
        bs.timer(3.0, self._on_countdown_end)

    def _countdown_tick(self, val: int) -> None:
        if self._countdown_text:
            self._countdown_text.text = str(val)
        if val in self._countdown_sounds:
            self._countdown_sounds[val].play()
        bs.getsound('tick').play()

    def _on_countdown_end(self) -> None:
        self._game_started = True

        # Clean up countdown text.
        if self._countdown_text:
            self._countdown_text.delete()
            self._countdown_text = None

        # Remove spawn platform.
        if self._platform_region:
            self._platform_region.delete()
            self._platform_region = None

        # Restrict controls to movement only (no combat) for all
        # players.  spawn_player_spaz already connected full controls,
        # so this single reconnect swaps to restricted mode.
        for player in self.players:
            if player.is_alive() and player.actor is not None:
                assert isinstance(player.actor, PlayerSpaz)
                player.actor.connect_controls_to_player(
                    enable_punch=False,
                    enable_bomb=False,
                    enable_pickup=False,
                )

        # Create speed indicator (hidden, fades in after title text
        # disappears).
        self._speed_color_combine = bs.newnode(
            'combine', attrs={'size': 4},
        )
        self._speed_text = bs.newnode('text', attrs={
            'v_attach': 'top',
            'h_attach': 'center',
            'h_align': 'center',
            'v_align': 'center',
            'position': (0, -70),
            'scale': 0.9,
            'flatness': 0.5,
            'shadow': 0.5,
            'text': '',
        })
        self._speed_color_combine.connectattr(
            'output', self._speed_text, 'color',
        )
        # Start fully transparent; fade in after game description
        # clears (~2s).
        self._speed_color_combine.input0 = 0.2
        self._speed_color_combine.input1 = 1.0
        self._speed_color_combine.input2 = 0.2
        self._speed_color_combine.input3 = 0.0
        bs.timer(2.0, self._fade_in_speed_text)
        self._update_speed_display()

        # Begin pipe spawning.
        self._spawn_pipe()

        # Check for immediate end (single player, etc).
        bs.timer(5.0, self._check_end_game)

    # -- Spawning --

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        occupied: set[int] = set()
        for p in self.players:
            if p is not player and p.is_alive():
                occupied.add(p.lane_idx)

        lane_idx = 0
        for i in range(len(self._channel_centers)):
            if i not in occupied:
                lane_idx = i
                break

        player.lane_idx = lane_idx
        cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0
        center = (self._channel_centers[lane_idx], cy + 1.0, PLAY_Z)

        spaz = self.spawn_player_spaz(player, center)
        if spaz.node:
            spaz.node.is_area_of_interest = False

        # Restrict controls immediately — no combat at any point.
        spaz.connect_controls_to_player(
            enable_punch=False,
            enable_bomb=False,
            enable_pickup=False,
        )

        spaz.play_big_death_sound = True
        return spaz

    # -- Update Loop --

    def _update(self) -> None:
        cx = (PLAY_X_MIN + PLAY_X_MAX) / 2.0
        cy = (PLAY_Y_MIN + PLAY_Y_MAX) / 2.0

        # Keep camera anchor centered.
        try:
            anchor = self._camera_anchor.node
            pos = anchor.position
            anchor.velocity = (
                (cx - pos[0]) * 30.0,
                (cy - pos[1]) * 30.0,
                (PLAY_Z - pos[2]) * 30.0,
            )
        except Exception:
            pass

        # Prevent players from becoming area-of-interest.
        for player in self.players:
            if player.is_alive() and player.actor and player.actor.node:
                try:
                    player.actor.node.is_area_of_interest = False
                except Exception:
                    pass

        # Update and cull pipes (skip if game ended — pipes are frozen).
        if self._game_started and not self._ended:
            dead: list[PipePair] = []
            for pipe in self._pipes:
                pipe.update(self._pipe_speed)
                if pipe.x_pos < PIPE_DELETE_X:
                    dead.append(pipe)
            for pipe in dead:
                pipe.delete()
                self._pipes.remove(pipe)

    def _fade_in_speed_text(self) -> None:
        if self._speed_color_combine:
            bs.animate(
                self._speed_color_combine, 'input3',
                {0.0: 0.0, 0.5: 0.8},
            )

    # -- Scoring --

    def _on_score_region_enter(self) -> None:
        """Called when a player enters a pipe gap's score region."""
        collision = bs.getcollision()
        try:
            region = collision.sourcenode
            spaz_node = collision.opposingnode
        except bs.NotFoundError:
            return

        # Find the pipe this region belongs to.
        pipe: PipePair | None = None
        for p in self._pipes:
            try:
                if p.score_region == region:
                    pipe = p
                    break
            except Exception:
                pass
        if pipe is None:
            return

        # Find the player who owns this spaz.
        player: Player | None = None
        for p in self.players:
            if p.is_alive() and p.actor and p.actor.node == spaz_node:
                player = p
                break
        if player is None:
            return

        # Only score once per player per pipe.
        player_id = id(player)
        if player_id in pipe.scored_players:
            return
        pipe.scored_players.add(player_id)

        # Increment score.
        player.pipes_passed += 1
        player.team.score += 1

        # Visual + audio feedback.
        if self._score_sound_enabled:
            self._score_sound.play()
        popupcolor: Sequence[float]
        popupstr = '+1'
        if len(self.players) > 1:
            popupcolor = bs.safecolor(player.color, target_intensity=0.75)
            popupstr += ' ' + player.getname()
        else:
            popupcolor = (1, 1, 1, 1)

        # Show popup at the score region position.
        try:
            pos = pipe.score_region.position
            PopupText(
                popupstr,
                position=pos,
                color=popupcolor,
                scale=1.0,
            ).autoretain()
        except Exception:
            pass

        # Award individual player stats (matters in teams mode).
        self.stats.player_scored(
            player, 1, showpoints=False, screenmessage=False,
        )
        self._update_scoreboard()

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score)

    def _update_speed_display(self) -> None:
        """Update the speed indicator text and heatmap color."""
        if not self._speed_text or not self._speed_color_combine:
            return

        # Compute how far we are from starting speed toward "danger"
        # speed. We treat 4x starting speed as full red.
        ratio = (
            (self._pipe_speed - self._starting_speed)
            / (self._starting_speed * 3.0)
        )
        ratio = max(0.0, min(1.0, ratio))

        # Green (0.2, 1.0, 0.2) → Yellow (1.0, 1.0, 0.2)
        #   → Red (1.0, 0.2, 0.2)
        if ratio < 0.5:
            t = ratio * 2.0  # 0..1 over first half
            r = 0.2 + 0.8 * t
            g = 1.0
        else:
            t = (ratio - 0.5) * 2.0  # 0..1 over second half
            r = 1.0
            g = 1.0 - 0.8 * t

        self._speed_color_combine.input0 = r
        self._speed_color_combine.input1 = g
        self._speed_color_combine.input2 = 0.2

        # Display speed as offset value (lowest internal = 1.0).
        display_speed = self._pipe_speed - SPEED_OFFSET
        self._speed_text.text = f'Speed: {display_speed:.1f}'

    def _ramp_speed(self) -> None:
        if not self._game_started or self._ended:
            return
        self._pipe_speed *= 1.05
        self._update_speed_display()

    # -- Pipe Spawning --

    def _spawn_pipe(self) -> None:
        if self._ended:
            return

        min_y = PLAY_Y_MIN + self._gap_size / 2.0 + 1.0
        max_y = PLAY_Y_MAX - self._gap_size / 2.0 - 1.0
        gap_y = random.uniform(min_y, max_y)

        self._pipes.append(PipePair(
            x_pos=PIPE_SPAWN_X,
            gap_center_y=gap_y,
            gap_size=self._gap_size,
            box_scale=self._box_scale,
            box_spacing=self._box_spacing,
            speed=self._pipe_speed,
            pipe_material=self._pipe_material,
            score_material=self._score_region_material,
        ))

        delay = self._pipe_spacing / max(0.1, self._pipe_speed)
        bs.timer(delay, self._spawn_pipe)

    # -- Death Handling --

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)

            # No respawn — once you're dead, you're out.
            # In co-op, end the instant everyone dies.
            # In teams/ffa, allow a 1-second fudge for simultaneous deaths.
            if isinstance(self.session, bs.CoopSession):
                bs.pushcall(self._check_end_game)
            else:
                bs.timer(1.0, self._check_end_game)
            return None
        return super().handlemessage(msg)

    def _check_end_game(self) -> None:
        if self._ended:
            return

        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break

        # In co-op, go until everyone is dead.
        # In teams/ffa, go until one team remains.
        if isinstance(self.session, bs.CoopSession):
            if living_team_count <= 0:
                self.end_game()
        else:
            if living_team_count <= 1:
                self.end_game()

    # -- End --

    @override
    def end_game(self) -> None:
        if self._ended:
            return
        self._ended = True

        # Award per-player scores (relevant for stats/teams).
        for team in self.teams:
            for player in team.players:
                if player.pipes_passed > 0:
                    self.stats.player_scored(
                        player, player.pipes_passed,
                        showpoints=False, screenmessage=False,
                    )

        # Set team scores.
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

        # Freeze all pipes in place (visual dramatic effect).
        for pipe in self._pipes:
            pipe.freeze()
        self._speed_timer = None


# ---------------------------------------------------------------------------
#  Plugin — Register Co-op Practice Levels
# ---------------------------------------------------------------------------


# ba_meta export babase.Plugin
class FlappySpazPlugin(babase.Plugin):
    """Registers Flappy Spaz co-op levels (Easy + Hard)."""

    def on_app_running(self) -> None:
        classic = babase.app.classic
        if classic is None:
            return

        classic.add_coop_practice_level(
            bs.Level(
                name='Flappy Spaz Easy',
                displayname='${GAME} (Easy)',
                gametype=FlappySpazGame,
                settings={
                    'Gap Size': 4.5,
                    'Pipe Spacing': 6.0,
                    'Starting Speed': 3.0,
                    'Epic Mode': False,
                },
                preview_texture_name='rampagePreview',
            )
        )

        classic.add_coop_practice_level(
            bs.Level(
                name='Flappy Spaz Hard',
                displayname='${GAME} (Hard)',
                gametype=FlappySpazGame,
                settings={
                    'Gap Size': 3.0,
                    'Pipe Spacing': 6.0,
                    'Starting Speed': 3.0,
                    'Epic Mode': False,
                },
                preview_texture_name='rampagePreview',
            )
        )
