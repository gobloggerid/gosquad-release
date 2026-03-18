# Jumping Contest
# Updated to API 9 by NR Communications LLC
#
# This simple game tests each player's ability in an underappreciated
# aspect of the game: jumping.

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.onscreencountdown import OnScreenCountdown

if TYPE_CHECKING:
    from typing import Any, Sequence


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.jumped: bool = False
        self.height: float = 0.0
        self.score: float = 0.0


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score: float = 0.0


class RaceTimer:
    """The race countdown lights to start things off."""

    def __init__(self, inc_time: float = 1.0) -> None:
        light_y = 150
        self.pos = 0
        self._beep1_sound = bs.getsound('raceBeep1')
        self._beep2_sound = bs.getsound('raceBeep2')
        self.lights: list[bs.Node] = []
        for i in range(4):
            light = bs.newnode(
                'image',
                attrs={
                    'texture': bs.gettexture('nub'),
                    'opacity': 1.0,
                    'absolute_scale': True,
                    'position': (-75 + i * 50, light_y),
                    'scale': (50, 50),
                    'attach': 'center',
                },
            )
            bs.animate(light, 'opacity', {0.01: 0, 1.0: 1.0})
            self.lights.append(light)
        self.lights[0].color = (0.2, 0, 0)
        self.lights[1].color = (0.2, 0, 0)
        self.lights[2].color = (0.2, 0.05, 0)
        self.lights[3].color = (0.0, 0.3, 0)
        self.cases = {
            1: self._do_light1,
            2: self._do_light2,
            3: self._do_light3,
            4: self._do_light4,
        }
        self._inc_timer: bs.Timer | None = None
        self.inc_time = inc_time

    def start(self) -> None:
        self._inc_timer = bs.Timer(
            self.inc_time, bs.WeakCallStrict(self.increment), repeat=True
        )

    def _do_light1(self) -> None:
        self.lights[0].color = (1.0, 0, 0)
        self._beep1_sound.play()

    def _do_light2(self) -> None:
        self.lights[1].color = (1.0, 0, 0)
        self._beep1_sound.play()

    def _do_light3(self) -> None:
        self.lights[2].color = (1.0, 0.3, 0)
        self._beep1_sound.play()

    def _do_light4(self) -> None:
        self.lights[3].color = (0.0, 1.0, 0)
        self._beep2_sound.play()
        for light in self.lights:
            bs.animate(light, 'opacity', {0.0: 1.0, 1.0: 0.0})
            bs.timer(1.0, light.delete)
        self._inc_timer = None
        self.on_finish()

    def on_finish(self) -> None:
        pass

    def on_increment(self) -> None:
        pass

    def increment(self) -> None:
        self.pos += 1
        if self.pos in self.cases:
            self.cases[self.pos]()
        self.on_increment()


class JumpSpaz(PlayerSpaz):
    """A player spaz that can only jump and punch (to record height)."""

    def on_move_left_right(self, value: float) -> None:
        pass

    def on_move_up_down(self, value: float) -> None:
        pass

    @override
    def on_punch_press(self) -> None:
        activity = self.getactivity()
        if activity is not None:
            assert isinstance(activity, JumpingContest)
            activity.set_end_height(self)

    @override
    def on_jump_press(self) -> None:
        activity = self.getactivity()
        if activity is not None:
            assert isinstance(activity, JumpingContest)
            activity.set_start_height(self)
        super().on_jump_press()


# ba_meta export bascenev1.GameActivity
class JumpingContest(bs.TeamGameActivity[Player, Team]):
    """A game that tests jumping height. Punch to lock in your score."""

    name = 'Jumping Contest'
    description = 'Jump as high as you can.'

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings: list[bs.Setting] = [
            bs.BoolSetting('Epic Mode', default=False),
        ]
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.FreeForAllSession) or issubclass(
            sessiontype, bs.DualTeamSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        assert babase.app.classic is not None
        maps = list(babase.app.classic.getmaps('melee'))
        # Happy Thoughts has a floating mechanic that interferes with jumping
        if 'Happy Thoughts' in maps:
            maps.remove('Happy Thoughts')
        return maps

    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self._called = False
        if self.settings_raw.get('Epic Mode', False):
            self.slow_motion = True

        self._info = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'bottom',
                    'h_align': 'center',
                    'vr_depth': 0,
                    'color': (0, 0.2, 0),
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'position': (0, 0),
                    'scale': 0.8,
                    'text': 'Created by MattZ45986 on Github',
                },
            )
        )
        self._scoreboard = Scoreboard()
        self._countdown: OnScreenCountdown | None = None
        self._race_timer: RaceTimer | None = None
        self._backup_timer: bs.Timer | None = None

    @override
    def on_transition_in(self) -> None:
        super().on_transition_in()
        self.default_music = bs.MusicType.FLAG_CATCHER

    def get_instance_score_board_description(self) -> str | bs.Lstr:
        return 'Punch to lock in your score'

    @override
    def on_begin(self) -> None:
        super().on_begin()
        for team in self.teams:
            team.customdata['score'] = 0.0
        self._update_scoreboard()
        bs.timer(3.5, bs.CallStrict(self._do_race_timer))

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        pos = self.map.get_ffa_start_position(self.players)
        spaz = self.spawn_player_spaz(player, position=pos)
        # Replace with our custom JumpSpaz
        # We override spawn_player_spaz instead for cleaner approach
        return spaz

    def _spawn_jump_spaz(self, player: Player) -> JumpSpaz:
        """Spawn a JumpSpaz for the given player."""
        pos = self.map.get_ffa_start_position(self.players)
        color = player.color
        highlight = player.highlight
        spaz = JumpSpaz(
            color=color,
            highlight=highlight,
            character=player.character,
            player=player,
        )
        player.actor = spaz
        assert spaz.node
        spaz.node.name = player.getname()
        spaz.node.name_color = bs.safecolor(color, target_intensity=0.75)
        spaz.handlemessage(
            bs.StandMessage(pos, random.uniform(0, 360))
        )
        # Controls will be connected when the race countdown finishes
        return spaz

    @override
    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            bs.screenmessage(
                bs.Lstr(
                    resource='playerDelayedJoinText',
                    subs=[('${PLAYER}', player.getname(full=True))],
                ),
                color=(0, 1, 0),
            )
            return
        self._spawn_jump_spaz(player)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            if player.actor:
                player.actor.disconnect_controls_from_player()
            player.customdata['score'] = 0.0
        else:
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, round(team.customdata.get('score', 0.0), 2)
            )

    def _start_jump(self) -> None:
        """Called when countdown finishes - enable jump controls."""
        for player in self.players:
            if player.actor:
                player.actor.connect_controls_to_player(
                    enable_bomb=False,
                    enable_punch=True,
                    enable_pickup=False,
                    enable_run=False,
                    enable_fly=False,
                )
            player.customdata['jumped'] = False
        self._countdown = OnScreenCountdown(30, endcall=self.end_game)
        self._countdown.start()
        self._backup_timer = bs.Timer(30.0, self._backup_end)

    def _do_race_timer(self) -> None:
        self._race_timer = RaceTimer()
        bs.timer(1.0, bs.CallStrict(self._race_timer.start))
        self._race_timer.on_finish = bs.WeakCallStrict(self._start_jump)

    def set_start_height(self, spaz: JumpSpaz) -> None:
        """Record the player's height at the start of a jump."""
        player = spaz.getplayer(Player, False)
        if player and spaz.node:
            player.customdata['height'] = spaz.node.position[1]
            player.customdata['jumped'] = True

    def set_end_height(self, spaz: JumpSpaz) -> None:
        """Record the player's height at punch time (jump peak)."""
        player = spaz.getplayer(Player, False)
        if not player:
            return
        if not player.customdata.get('jumped', False):
            return
        if spaz.node:
            score = (
                spaz.node.position[1] - player.customdata.get('height', 0.0)
            ) * 10.0
            player.customdata['score'] = score
            team_score = player.team.customdata.get('score', 0.0)
            if score > team_score:
                player.team.customdata['score'] = score
            self._update_scoreboard()

    def _backup_end(self) -> None:
        if not self._called:
            self.end_game()

    @override
    def end_game(self) -> None:
        self._called = True
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(
                team, int(round(team.customdata.get('score', 0.0) * 100.0))
            )
        self.end(results=results)
