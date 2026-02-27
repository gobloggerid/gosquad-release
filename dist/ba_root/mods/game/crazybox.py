# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# Edited by goblogger
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random

# import _babase
from math import cos, sin
from typing import TYPE_CHECKING

import babase

# import bauiv1 as bui
import bascenev1 as bs
from bascenev1lib.actor.bomb import Blast, Bomb, BombFactory, ExplodeMessage

# from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import (
        Any,
    )


class DisconnectMessage:
    pass


class ConnectMessage:
    pass


class Box(bs.Actor):
    def __init__(
        self,
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        bomb_type: str = 'normal',
        box_type: str = 'small',
        bomb_scale: float = 1.0,
    ):
        super().__init__()
        shared = SharedObjects.get()
        factory = BombFactory.get()
        self.pos: Sequence[float] = (
            (-11.857367) + round(random.uniform(0, 23), 6),
            round(random.uniform(2, 9), 2),
            (-4.3599663) + round(random.uniform(0, 8), 6),
        )
        self.random = self.force = self.ang = self.x = self.z = (
            self.momentum
        ) = 0

        self.typee = box_type
        self._exploded = False
        self.ground = False
        self._should_update_ai = True  # Flag to control AI updates
        self._explode_callbacks: list[Callable[[Bomb, Blast], Any]] = []

        materials: tuple[bs.Material, ...] = (
            factory.bomb_material,
            shared.footing_material,
            shared.object_material,
        )

        if box_type == 'small':
            self.data = {
                'walk_force': 9.35,
                'jump_force': 190,
                'walk_cd': 1474,
                'jump_cd': 1500,
                'light_color': (1, 0, 0.4),
                'points': 100,
                'texture': bs.gettexture('star'),
                'size': 0.9,
            }
        elif box_type == 'large':
            self.data = {
                'walk_force': 13.3905,
                'jump_force': 260,
                'walk_cd': 900,
                'jump_cd': 3000,
                'light_color': (0, 0.2, 1.55),
                'points': 50,
                'texture': bs.gettexture('egg2'),
                'size': 1.2,
            }

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': self.pos,
                'velocity': velocity,
                'mesh': bs.getmesh('powerup'),
                'light_mesh': bs.getmesh('powerup'),
                'body': 'crate',
                'mesh_scale': self.data['size'],
                'body_scale': self.data['size'],
                'density': 0.5,
                'gravity_scale': 0.5,
                'shadow_size': 0.5,
                'color_texture': self.data['texture'],
                'reflection': 'powerup',
                'reflection_scale': [0.23],
                'materials': materials,
            },
        )
        self.light = bs.newnode(
            'light', attrs={'color': self.data['light_color'], 'radius': 0.4}
        )
        self.node.connectattr('position', self.light, 'position')
        self.move_used = self.highjump_used = self.jump_used = False
        bs.animate(self.node, 'mesh_scale', {0.0: 0.0, 0.7: self.data['size']})
        bs.timer(1.0, self.start_updating)

    def start_updating(self) -> None:
        """Start the AI update timer."""
        if self._should_update_ai:
            self.move_timer = bs.Timer(
                0.1, bs.WeakCallStrict(self.update_ai), repeat=True
            )

    def refresh(self, type_: str = 'move') -> None:
        """Reset the cooldown for a specific action."""
        if type_ == 'move':
            self.move_used = False
        elif type_ == 'jump':
            self.jump_used = False
        elif type_ == 'highjump':
            self.highjump_used = False

    def move(self) -> None:
        """Move the box in a random direction."""
        if (
            not self.node
            or not self.node.exists()
            or self.move_used
            or self.node.position[1] >= 1.0
        ):
            return

        self.move_used = True
        bs.timer(self.data['walk_cd'] * 0.001, lambda: self.refresh('move'))
        self.ang = random.randint(0, 360)
        self.x = cos(self.ang) * self.data['walk_force']
        self.z = sin(self.ang) * self.data['walk_force']
        self.node.velocity = (self.x, 0, self.z)

    def high_jump(self) -> None:
        """Make the box jump higher."""
        if not self.node or not self.node.exists() or self.highjump_used:
            return

        self.highjump_used = True
        bs.timer(10.0, lambda: self.refresh('highjump'))
        self.node.handlemessage(
            'impulse',
            self.node.position[0],
            self.node.position[1],
            self.node.position[2],
            0.0,
            0.0,
            0.0,
            self.data['jump_force'] + 70,
            0,
            0,
            0,
            0,
            1,
            0,
        )

    def jump(self) -> None:
        """Make the box jump."""
        if not self.node or not self.node.exists() or self.jump_used:
            return

        self.jump_used = True
        bs.timer(self.data['jump_cd'] * 0.001, lambda: self.refresh('jump'))
        self.node.handlemessage(
            'impulse',
            self.node.position[0],
            self.node.position[1],
            self.node.position[2],
            0.0,
            0.0,
            0.0,
            self.data['jump_force'],
            0,
            0,
            0,
            0,
            1,
            0,
        )

    def act_crazy(self) -> None:
        """Make the box move erratically when held by a player."""
        if not self.node or not self.node.exists():
            return

        self.node.velocity = (
            self.node.velocity[0] + round(random.uniform(-2.0, 2.0), 2),
            random.random() * 1.5,
            self.node.velocity[2] + round(random.uniform(-2.0, 2.0), 2),
        )
        self.node.extra_acceleration = (
            self.node.velocity[0] * 1.3,
            self.node.velocity[1] * 45,
            self.node.velocity[2] * 1.3,
        )

    def update_ai(self) -> None:
        """Update the box's AI behavior."""
        if (
            not self._should_update_ai
            or not self.node
            or not self.node.exists()
        ):
            return

        for p in self.activity.players:
            if p.actor and p.actor.node and p.actor.node.exists():
                if p.actor.node.hold_node == self.node:
                    self.act_crazy()
                else:
                    self.node.extra_acceleration = (0, 0, 0)
                    self.random = random.randint(1, 4)
                    if self.random == 1:
                        self.move()
                    elif self.random == 2:
                        self.jump()
                    elif self.random == 3 and self.typee == 'large':
                        self.high_jump()

    def on_expire(self) -> None:
        """Handle expiration of the box."""
        super().on_expire()
        self._explode_callbacks = []
        self._should_update_ai = False

    def respawn(self) -> None:
        """Respawn the box (currently not implemented)."""

    def _handle_die(self) -> None:
        """Handle the box's death."""
        if self.light and self.light.exists():
            self.light.delete()
        if self.node and self.node.exists():
            self.node.delete()

    def _handle_oob(self) -> None:
        """Handle out-of-bounds events."""
        self.handlemessage(bs.DieMessage())

    def add_explode_callback(self, call: Callable[[Bomb, Blast], Any]) -> None:
        """Add a callback to be called when the box explodes."""
        self._explode_callbacks.append(call)

    def explode(self) -> None:
        """Make the box explode."""
        if self._exploded:
            return

        self._exploded = True
        if self.node and self.node.exists():
            blast = Blast(
                position=self.node.position,
                velocity=self.node.velocity,
                blast_radius=2.4,
                blast_type='tnt',
                hit_type='normal',
                hit_subtype='tnt',
            ).autoretain()

            for callback in self._explode_callbacks:
                callback(self, blast)

        bs.timer(0.001, bs.WeakCallStrict(self.handlemessage, bs.DieMessage()))

    def _add_material(self, material: bs.Material) -> None:
        """Add a material to the box's materials list."""
        if not self.node or not self.node.exists():
            return

        materials = self.node.materials
        if material not in materials:
            assert isinstance(materials, tuple)
            self.node.materials = materials + (material,)

    def _handle_hit(self, msg: bs.HitMessage) -> None:
        """Handle hit messages."""
        # if msg.hit_subtype == 'tnt':
        # return

        # if not self._exploded and msg.hit_type != 'punch':
        if not self._exploded:
            self._should_update_ai = (
                False  # Stop AI updates instead of setting to None
            )
            bs.timer(
                1.0, bs.WeakCallStrict(self.handlemessage, ExplodeMessage())
            )
            killer = msg.get_source_player(bs.Player)
            if killer is not None:
                assert killer.team is not None
                self.activity.stats.player_scored(
                    killer, self.data['points'], screenmessage=False
                )
                killer.team.score += self.data['points']
                self.activity._dingsound.play()
                self.activity._update_scoreboard()

    def handlemessage(self, msg: Any) -> Any:
        """Handle incoming messages."""
        if isinstance(msg, ExplodeMessage):
            self.explode()
        elif isinstance(msg, bs.HitMessage):
            self._handle_hit(msg)
        elif isinstance(msg, bs.DieMessage):
            bs.timer(
                random.uniform(1.5, 5.02),
                lambda: Box(box_type=self.typee).autoretain(),
            )
            self._handle_die()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self._handle_oob()
        else:
            super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Player class for Crazy Box game."""


class Team(bs.Team[Player]):
    """Team class for Crazy Box game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class CrazyBoxGame(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Crazy Boxes'
    description = 'Blow up the Crazy Boxes!'
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[babase.Setting]:
        settings = [
            bs.IntSetting(
                'Points to win per Player',
                min_value=50,
                default=800,
                increment=50,
            ),
            bs.IntSetting(
                'Small Box Count', min_value=1, default=1, increment=1
            ),
            bs.IntSetting(
                'Large Box Count', min_value=1, default=2, increment=1
            ),
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
                default=0,
            ),
            bs.FloatChoiceSetting(
                'Respawn Times',
                choices=[
                    ('Shorter', 0.25),
                    ('Short', 0.5),
                    ('Normal', 1.0),
                    ('Long', 2.0),
                    ('Longer', 4.0),
                ],
                default=1.0,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Football Stadium']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.co = int(settings['Small Box Count'])
        self.c2 = int(settings['Large Box Count'])
        self._scoreboard = Scoreboard()
        self._score_to_win: int | None = None
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = False
        self.boxes_to_win = int(settings['Points to win per Player'])
        self._time_limit = float(settings['Time Limit'])
        self.region: list[bs.NodeActor] = []
        self.block_box_mat = bs.Material()
        self.block_box_mat.add_actions(
            conditions=('they_have_material', BombFactory.get().bomb_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )

        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.FORWARD_MARCH
        )

        self._enable_powers = False
        self._switch_powers_timer = bs.Timer(
            30.0, self._switch_powers, repeat=True
        )

    def _setup_standard_tnt_drops(self) -> None:
        """Set up standard TNT drops (not used in this game)."""

    def get_instance_description(self) -> str | Sequence:
        return (
            'Blow up boxes with hands or bombs \nand score ${ARG1} points to win!',
            self.boxes_to_win,
        )

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        for _ in range(self.co):
            Box().autoretain()
        for _ in range(self.c2):
            Box(box_type='large').autoretain()
        self.setup_standard_powerup_drops()
        b = self.map.defs.boxes['map_bounds']
        self.region.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': (b[0], b[1] + 10, b[2]),
                        'type': 'box',
                        'scale': (b[6], 1.0, b[8]),
                        'materials': [self.block_box_mat],
                    },
                )
            )
        )

        self._score_to_win = self.boxes_to_win * max(
            1, max(len(t.players) for t in self.teams)
        )
        self._update_scoreboard()

        tips = bs.newnode(
            'text',
            attrs={
                'text': '** Blow all the boxes up with your punch or bombs **',
                'scale': 1.2,
                'maxwidth': 800,
                'position': (0, 200),
                'shadow': 0.5,
                'flatness': 0.5,
                'color': (0, 0.8, 0),
                'h_align': 'center',
                'v_attach': 'bottom',
            },
        )
        bs.timer(20.0, tips.delete)

    def _switch_powers(self) -> None:
        activity = bs.getactivity()
        if activity is not None:
            activity.toggle_slow_motion()

        self._enable_powers = not self._enable_powers
        # Instantly activate powers for all players
        # only when powers are enable
        for player in self.players:
            actor = player.actor
            if not actor or not getattr(actor, 'node', None):
                continue

            if not self._enable_powers:
                actor.node.hockey = False
                if getattr(actor, '_puppetspaz', None) and (
                    actor._puppetspaz.node
                ):
                    actor._puppetspaz.node.hockey = False
            else:
                actor.equip_speed()
                actor.equip_dash()
                actor.equip_teleport()
                actor.equip_super_jump()
                if getattr(actor, '_puppetspaz', None):
                    actor._puppetspaz.equip_speed()
                    actor._puppetspaz.equip_dash()
                    actor._puppetspaz.equip_teleport()
                    actor._puppetspaz.equip_super_jump()

    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)

        spaz.equip_shields(decay=False)
        if self._enable_powers:
            spaz.equip_speed()
            spaz.equip_dash()
            spaz.equip_teleport()
            spaz.equip_super_jump()

        return spaz

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            self.respawn_player(player)
        else:
            return super().handlemessage(msg)
        return None

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.score, self._score_to_win
            )
            if team.score >= self._score_to_win:
                bs.timer(0.5, self.end_game)

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
