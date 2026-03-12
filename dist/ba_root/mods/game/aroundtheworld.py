# Released under the MIT License. See LICENSE for details.
#
"""Defines the Around The World mini-game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard

if TYPE_CHECKING:
    from typing import Any, Sequence
    from bascenev1lib.actor.onscreentimer import OnScreenTimer


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.last_point: int = 0
        self.lap: int = 0
        self.distance: float = 0.0
        self.finished: bool = False
        self.rank: int | None = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.time: float | None = None
        self.lap: int = 0
        self.finished: bool = False


# ba_meta export bascenev1.GameActivity
class AroundTheWorld(bs.TeamGameActivity[Player, Team]):
    """Race around the world by touching platforms in order."""

    name = 'Around The World'
    description = 'Race around the world.'
    scoreconfig = bs.ScoreConfig(
        label='Time',
        lower_is_better=True,
        scoretype=bs.ScoreType.MILLISECONDS,
    )

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings: list[bs.Setting] = [
            bs.IntSetting('Laps', min_value=1, default=3, increment=1),
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
            bs.BoolSetting('Epic Mode', default=False),
        ]
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(bs.BoolSetting('Entire Team Must Finish', default=False))
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.MultiTeamSession)

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Happy Thoughts']

    def __init__(self, settings: dict) -> None:
        self._race_started = False
        super().__init__(settings)

        self._scoreboard = Scoreboard()
        self._score_sound = bs.getsound('score')
        self._swip_sound = bs.getsound('swip')
        self._last_team_time: float | None = None
        self._laps = int(settings['Laps'])
        self._time_limit = float(settings['Time Limit'])
        self._epic_mode = bool(settings['Epic Mode'])
        self._entire_team_must_finish = bool(
            settings.get('Entire Team Must Finish', False)
        )

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC_RACE if self._epic_mode else bs.MusicType.RACE
        )

        self._nub_tex: bs.Texture | None = None
        self._beep_1_sound: bs.Sound | None = None
        self._beep_2_sound: bs.Sound | None = None
        self._time_text: bs.Actor | None = None
        self._timer: OnScreenTimer | None = None
        self._scoreboard_timer: bs.Timer | None = None
        self._start_lights: list[bs.Node] | None = None
        self._team_finish_pts: int = 100

        self.info = bs.NodeActor(
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

    @override
    def get_instance_description(self) -> str | Sequence:
        if (
            isinstance(self.session, bs.DualTeamSession)
            and self._entire_team_must_finish
        ):
            t_str = ' Your entire team has to finish.'
        else:
            t_str = ''

        if self._laps > 1:
            return ('${ARG1} laps.' + t_str, self._laps)
        return 'Fly 1 lap.' + t_str

    @override
    def get_instance_description_short(self) -> str | Sequence:
        if self._laps > 1:
            return ('fly ${ARG1} laps', self._laps)
        return 'fly 1 lap'

    @override
    def on_transition_in(self) -> None:
        super().on_transition_in()
        self._nub_tex = bs.gettexture('nub')
        self._beep_1_sound = bs.getsound('raceBeep1')
        self._beep_2_sound = bs.getsound('raceBeep2')

    @override
    def on_team_join(self, team: Team) -> None:
        team.time = None
        team.lap = 0
        team.finished = False
        self._update_scoreboard()

    @override
    def on_player_join(self, player: Player) -> None:
        player.last_point = 0
        player.lap = 0
        player.distance = 0.0
        player.finished = False
        player.rank = None
        super().on_player_join(player)

    @override
    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        if (
            isinstance(self.session, bs.DualTeamSession)
            and self._entire_team_must_finish
        ):
            bs.broadcastmessage(
                bs.Lstr(
                    translate=(
                        'statements',
                        '${TEAM} is disqualified because ${PLAYER} left',
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
            player.team.lap = 0
            bs.getsound('boo').play()
            for other_player in player.team.players:
                other_player.lap = 0
                other_player.finished = True
                try:
                    if other_player.actor is not None:
                        other_player.actor.handlemessage(bs.DieMessage())
                except Exception:
                    logging.exception('Error sending DieMessage.')
        bs.timer(0.001, self._check_end_game)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            distances = [player.distance for player in team.players]
            if not distances:
                team_dist = 0.0
            else:
                if (
                    isinstance(self.session, bs.DualTeamSession)
                    and self._entire_team_must_finish
                ):
                    team_dist = min(distances)
                else:
                    team_dist = max(distances)
            self._scoreboard.set_team_value(
                team,
                team_dist,
                self._laps,
                flash=(team_dist >= float(self._laps)),
                show_value=False,
            )
            if team_dist >= float(self._laps):
                self._check_end_game()

    @override
    def on_begin(self) -> None:
        from bascenev1lib.actor.onscreentimer import OnScreenTimer

        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._team_finish_pts = 100

        # Instructions text
        self._time_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'top',
                    'h_attach': 'right',
                    'h_align': 'right',
                    'color': (1, 1, 1, 0.5),
                    'flatness': 0.5,
                    'shadow': 0.5,
                    'position': (0, -75),
                    'scale': 1.4,
                    'text': (
                        'Touch\nthe\nright,\ntop,\nleft,\nand\nbottom\n'
                        'platforms\nin\norder.'
                    ),
                },
            )
        )
        self._timer = OnScreenTimer()

        self._scoreboard_timer = bs.Timer(
            0.25, self._update_scoreboard, repeat=True
        )

        if self.slow_motion:
            t_scale = 0.4
            light_y = 50
        else:
            t_scale = 1.0
            light_y = 150

        l_start = 7.1 * t_scale
        inc = 1.25 * t_scale

        bs.timer(l_start, self._do_light_1)
        bs.timer(l_start + inc, self._do_light_2)
        bs.timer(l_start + 2 * inc, self._do_light_3)
        bs.timer(l_start + 3 * inc, self._start_race)

        assert self._nub_tex is not None
        self._start_lights = []
        for i in range(4):
            lnub = bs.newnode(
                'image',
                attrs={
                    'texture': self._nub_tex,
                    'opacity': 1.0,
                    'absolute_scale': True,
                    'position': (-75 + i * 50, light_y),
                    'scale': (50, 50),
                    'attach': 'center',
                },
            )
            bs.animate(
                lnub,
                'opacity',
                {
                    4.0 * t_scale: 0,
                    5.0 * t_scale: 1.0,
                    12.0 * t_scale: 1.0,
                    12.5 * t_scale: 0.0,
                },
            )
            bs.timer(13.0 * t_scale, lnub.delete)
            self._start_lights.append(lnub)

        self._start_lights[0].color = (0.2, 0, 0)
        self._start_lights[1].color = (0.2, 0, 0)
        self._start_lights[2].color = (0.2, 0.05, 0)
        self._start_lights[3].color = (0.0, 0.3, 0)

    def _do_light_1(self) -> None:
        assert self._start_lights is not None and self._beep_1_sound is not None
        self._start_lights[0].color = (1.0, 0, 0)
        self._beep_1_sound.play()

    def _do_light_2(self) -> None:
        assert self._start_lights is not None and self._beep_1_sound is not None
        self._start_lights[1].color = (1.0, 0, 0)
        self._beep_1_sound.play()

    def _do_light_3(self) -> None:
        assert self._start_lights is not None and self._beep_1_sound is not None
        self._start_lights[2].color = (1.0, 0.3, 0)
        self._beep_1_sound.play()

    def _start_race(self) -> None:
        assert self._start_lights is not None and self._beep_2_sound is not None
        self._start_lights[3].color = (0.0, 1.0, 0)
        self._beep_2_sound.play()
        for player in self.players:
            if player.actor is not None:
                try:
                    assert isinstance(player.actor, PlayerSpaz)
                    player.actor.connect_controls_to_player()
                except Exception:
                    logging.exception('Error in race player connects.')
        assert self._timer is not None
        self._timer.start()
        self._race_started = True

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        pos_list = (
            (0, 5, 0),
            (9, 11, 0),
            (0, 12, 0),
            (-11, 11, 0),
        )
        try:
            base_pos = pos_list[player.last_point]
        except IndexError:
            base_pos = (0, 5, 0)

        position = (
            base_pos[0] + random.random() * 2 - 1,
            base_pos[1],
            base_pos[2],
        )

        spaz = self.spawn_player_spaz(player, position=position)

        # Prevent control before race starts.
        if not self._race_started:
            spaz.disconnect_controls_from_player()
            player.last_point = 0

        # Spawn light flash.
        light_color = bs.normalized_color(player.color)
        light = bs.newnode('light', attrs={'color': light_color})
        assert spaz.node
        spaz.node.connectattr('position', light, 'position')
        bs.animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0})
        bs.timer(0.5, light.delete)

        bs.timer(0.25, bs.CallStrict(self._check_pt, player))
        return spaz

    def _flash_player(self, player: Player, scale: float) -> None:
        assert isinstance(player.actor, PlayerSpaz)
        assert player.actor.node
        pos = player.actor.node.position
        light = bs.newnode(
            'light',
            attrs={
                'position': pos,
                'color': (1, 1, 0),
                'height_attenuated': False,
                'radius': 0.4,
            },
        )
        bs.timer(0.5, light.delete)
        bs.animate(light, 'intensity', {0: 0, 0.1: 1.0 * scale, 0.5: 0})

    def _check_pt(self, player: Player) -> None:
        if not player.is_alive():
            return
        assert isinstance(player.actor, PlayerSpaz)
        assert player.actor.node
        pos = player.actor.node.position_center

        # Right platform
        if 8 < pos[0] < 11 and 10.5 < pos[1] < 13:
            if player.last_point in (2, 3):
                self._kill_player(player)
                return
            elif player.last_point == 0:
                player.distance += 0.25
            player.last_point = 1

        # Top platform
        if -1 < pos[0] < 1 and 11.5 < pos[1] < 15:
            if player.last_point in (3, 0):
                self._kill_player(player)
                return
            elif player.last_point == 1:
                player.distance += 0.25
            player.last_point = 2

        # Left platform
        if -12.5 < pos[0] < -10 and 10.5 < pos[1] < 13:
            if player.last_point in (0, 1):
                self._kill_player(player)
                return
            elif player.last_point == 2:
                player.distance += 0.25
            player.last_point = 3

        # Bottom platform
        if -2 < pos[0] < 2 and 4.5 < pos[1] < 6.5:
            if player.last_point in (1, 2):
                self._kill_player(player)
                return
            elif player.last_point == 3:
                player.distance += 0.25
            player.last_point = 0

        bs.timer(0.25, bs.CallStrict(self._check_pt, player))

    def _check_end_game(self) -> None:
        for player in self.players:
            if player.distance >= self._laps:
                assert self._timer is not None
                player.team.time = bs.time() - self._timer.getstarttime()
                if player.actor is not None:
                    player.actor.handlemessage(bs.DieMessage())
                self.end_game()
                return

    def _kill_player(self, player: Player) -> None:
        if player.actor is not None:
            player.actor.handlemessage(bs.DieMessage())
        bs.broadcastmessage(
            'Killing '
            + player.getname()
            + ' for skipping part of the track.',
            color=(1, 0, 0),
        )

    @override
    def end_game(self) -> None:
        assert self._timer is not None
        if self._timer.has_started():
            self._timer.stop(
                endtime=(
                    None
                    if self._last_team_time is None
                    else (self._timer.getstarttime() + self._last_team_time)
                )
            )

        results = bs.GameResults()
        for team in self.teams:
            if team.time is not None:
                results.set_team_score(team, int(team.time * 1000.0))
            else:
                results.set_team_score(team, None)

        self.end(
            results=results,
            announce_winning_team=isinstance(self.session, bs.DualTeamSession),
        )

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            if not player.finished:
                self.respawn_player(player, respawn_time=1.0)
        else:
            super().handlemessage(msg)
