# Released under AGPL-3.0-or-later. See LICENSE for details.
#
# This file incorporates work covered by the following permission notice:
#   Released under the MIT License. See LICENSE for details.
#
"""Provides an easter egg hunt game; but on happy thoughts."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.onscreencountdown import OnScreenCountdown
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.respawnicon import RespawnIcon
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.respawn_timer: bs.Timer | None = None
        self.respawn_icon: RespawnIcon | None = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class EggHuntInTheSkyGame(bs.TeamGameActivity[Player, Team]):
    """A game where score is based on collecting eggs."""

    name = 'Egg Hunt in the Sky'
    description = 'Gather eggs!'
    available_settings = [
        bs.BoolSetting('Pro Mode', default=False),
        bs.BoolSetting('Epic Mode', default=False),
    ]
    scoreconfig = bs.ScoreConfig(label='Score', scoretype=bs.ScoreType.POINTS)

    # We're currently hard-coded for one map.
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Happy Thoughts']

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return (
            issubclass(sessiontype, bs.CoopSession)
            or issubclass(sessiontype, bs.DualTeamSession)
            or issubclass(sessiontype, bs.FreeForAllSession)
        )

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._last_player_death_time = None
        self._scoreboard = Scoreboard()
        self.egg_mesh = bs.getmesh('egg')
        self.egg_tex_1 = bs.gettexture('eggTex1')
        self.egg_tex_2 = bs.gettexture('eggTex2')
        self.egg_tex_3 = bs.gettexture('eggTex3')
        self._collect_sound = bs.getsound('powerup01')
        self._pro_mode = settings.get('Pro Mode', False)
        self._epic_mode = settings.get('Epic Mode', False)
        self._max_eggs = 4.0
        self.egg_material = bs.Material()
        self.egg_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_connect', self._on_egg_player_collide),),
        )
        self._eggs: list[Egg] = []
        self._update_timer: bs.Timer | None = None
        self._countdown: OnScreenCountdown | None = None

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.FORWARD_MARCH
        )

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    # Called when our game actually starts.
    def on_begin(self) -> None:
        super().on_begin()
        self._update_scoreboard()
        self._update_timer = bs.Timer(0.25, self._update, repeat=True)
        duration = 30 if self.slow_motion else 60
        self._countdown = OnScreenCountdown(duration, endcall=self.end_game)
        bs.timer(4.0, self._countdown.start)

    # Overriding the default character spawning.
    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)
        spaz.connect_controls_to_player()
        return spaz

    def _on_egg_player_collide(self) -> None:
        if self.has_ended():
            return
        collision = bs.getcollision()

        # Be defensive here; we could be hitting the corpse of a player
        # who just left/etc.
        try:
            egg = collision.sourcenode.getdelegate(Egg, True)
            player = collision.opposingnode.getdelegate(
                PlayerSpaz, True
            ).getplayer(Player, True)
        except bs.NotFoundError:
            return

        player.team.score += 1

        # Displays a +1 (and adds to individual player score in
        # teams mode).
        self.stats.player_scored(player, 1, screenmessage=False)
        if self._max_eggs < 9:
            self._max_eggs += 2.0
        elif self._max_eggs < 14:
            self._max_eggs += 1.0
        elif self._max_eggs < 34:
            self._max_eggs += 0.6
        self._update_scoreboard()
        self._collect_sound.play(0.5, position=egg.node.position)

        # Create a flash.
        light = bs.newnode(
            'light',
            attrs={
                'position': egg.node.position,
                'height_attenuated': False,
                'radius': 0.1,
                'color': (1, 1, 0),
            },
        )
        bs.animate(light, 'intensity', {0: 0, 0.1: 1.0, 0.2: 0}, loop=False)
        bs.timer(0.200, light.delete)
        egg.handlemessage(bs.DieMessage())

    def _update(self) -> None:
        # Misc. periodic updating.
        mb = self.map.get_def_bound_box('area_of_interest_bounds')
        assert mb
        xpos = random.uniform(mb[0], mb[3])
        ypos = random.uniform(mb[1], mb[4])
        zpos = random.uniform(mb[2], mb[5])

        # Prune dead eggs from our list.
        self._eggs = [e for e in self._eggs if e]

        # Spawn more eggs if we've got space.
        if len(self._eggs) < int(self._max_eggs):
            # Occasionally spawn a bomb in addition.
            if self._pro_mode and random.random() < 0.4:
                actor = Bomb(
                    position=(xpos, ypos, zpos), bomb_type='impact'
                ).autoretain()
            else:
                actor = Egg(position=(xpos, ypos, zpos))
                self._eggs.append(actor)

            if actor.node:
                # We want everything to float
                actor.node.gravity_scale = 0.0
                # Some velocity so the game doesn't look stiff
                nvelocity = bs.Vec3(
                    random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0), 0
                ).normalized()
                s = random.uniform(-0.4, 0.4)
                # Let's make it a bit more spicy since we don't have any bots
                if self._pro_mode:
                    s *= 10
                actor.node.velocity = (
                    nvelocity[0] * s,
                    nvelocity[1] * s,
                    nvelocity[2] * s,
                )

    # Various high-level game events come through this method.
    def handlemessage(self, msg: Any) -> Any:
        # Respawn dead players.
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            # Respawn them shortly.
            player = msg.getplayer(Player)
            assert self.initialplayerinfos is not None
            respawn_time = 2.0 + len(self.initialplayerinfos) * 1.0
            player.respawn_timer = bs.Timer(
                respawn_time, bs.CallStrict(self.spawn_player_if_exists, player)
            )
            player.respawn_icon = RespawnIcon(player, respawn_time)
        else:
            # Default handler.
            return super().handlemessage(msg)
        return None

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score)

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results)


class Egg(bs.Actor):
    """A lovely egg that can be picked up for points."""

    def __init__(self, position: tuple[float, float, float] = (0.0, 1.0, 0.0)):
        super().__init__()
        activity = self.activity
        assert isinstance(activity, EggHuntInTheSkyGame)
        shared = SharedObjects.get()

        # Spawn just above the provided point.
        self._spawn_pos = (position[0], position[1] + 1.0, position[2])
        ctex = (activity.egg_tex_1, activity.egg_tex_2, activity.egg_tex_3)[
            random.randrange(3)
        ]
        mats = [shared.object_material, activity.egg_material]
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': activity.egg_mesh,
                'color_texture': ctex,
                'body': 'capsule',
                'reflection': 'soft',
                'mesh_scale': 0.5,
                'body_scale': 0.6,
                'density': 4.0,
                'reflection_scale': [0.15],
                'shadow_size': 0.6,
                'position': self._spawn_pos,
                'materials': mats,
                'is_area_of_interest': True,
            },
        )

    def exists(self) -> bool:
        return bool(self.node)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, bs.HitMessage):
            if self.node:
                assert msg.force_direction is not None
                self.node.handlemessage(
                    'impulse',
                    msg.pos[0],
                    msg.pos[1],
                    msg.pos[2],
                    msg.velocity[0],
                    msg.velocity[1],
                    msg.velocity[2],
                    1.0 * msg.magnitude,
                    1.0 * msg.velocity_magnitude,
                    msg.radius,
                    0,
                    msg.force_direction[0],
                    msg.force_direction[1],
                    msg.force_direction[2],
                )
        else:
            super().handlemessage(msg)


# ba_meta export plugin
class AddToCoopPracticeLevels(bs.Plugin):
    def on_app_running(self) -> None:
        bs.app.classic.add_coop_practice_level(
            bs.Level(
                name='Egg Hunt in the Sky',
                gametype=EggHuntInTheSkyGame,
                settings={},
                preview_texture_name='alwaysLandPreview',
            ),
        )
        bs.app.classic.add_coop_practice_level(
            bs.Level(
                name='Pro Egg Hunt in the Sky',
                gametype=EggHuntInTheSkyGame,
                settings={'Pro Mode': True},
                preview_texture_name='alwaysLandPreview',
            ),
        )
