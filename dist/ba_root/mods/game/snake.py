# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# snake
# Released under the MIT License. See LICENSE for details.
#
"""Snake game by SEBASTIAN2059"""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.scoreboard import Scoreboard

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class ScoreMessage:
    """It will help us with the scores."""

    def __init__(self, player: Player):
        self.player = player

    def getplayer(self):
        return self.player


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        super().__init__()

        self.mines = []
        self.actived = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


class SnakeMine(Bomb):
    """Custom a mine :)"""

    def __init__(self, **kwargs):
        kwargs['bomb_type'] = 'land_mine'
        super().__init__(**kwargs)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if self.expired:
            return None
        if isinstance(msg, bs.HitMessage):
            return None
        else:
            return super().handlemessage(msg)
        return None


# ba_meta export bascenev1.GameActivity
class SnakeGame(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Snake'
    description = 'Survive a set number of mines to win'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Score to Win',
                min_value=40,
                default=80,
                increment=5,
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
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._score_to_win: int | None = None
        self._dingsound = bs.getsound('dingSmall')

        self._beep_1_sound = bs.getsound('raceBeep1')
        self._beep_2_sound = bs.getsound('raceBeep2')

        self._epic_mode = bool(settings['Epic Mode'])
        self._kills_to_win_per_player = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])

        self._started = False

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.TO_THE_DEATH
        )

    def get_instance_description(self) -> str | Sequence:
        return "Run and don't get killed."

    def get_instance_description_short(self) -> str | Sequence:
        return 'survive ${ARG1} mines', self._score_to_win

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        # self.setup_standard_powerup_drops()

        # Base kills needed to win on the size of the largest team.
        self._score_to_win = self._kills_to_win_per_player * max(
            1, max(len(t.players) for t in self.teams)
        )
        self._update_scoreboard()

        if self.slow_motion:
            t_scale = 0.4
            light_y = 50
        else:
            t_scale = 1.0
            light_y = 150
        lstart = 7.1 * t_scale
        inc = 1.25 * t_scale

        bs.timer(lstart, self._do_light_1)
        bs.timer(lstart + inc, self._do_light_2)
        bs.timer(lstart + 2 * inc, self._do_light_3)
        bs.timer(lstart + 3 * inc, self._start_race)

        self._start_lights = []
        for i in range(4):
            lnub = bs.newnode(
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
        assert self._start_lights is not None
        self._start_lights[0].color = (1.0, 0, 0)
        self._beep_1_sound.play()

    def _do_light_2(self) -> None:
        assert self._start_lights is not None
        self._start_lights[1].color = (1.0, 0, 0)
        self._beep_1_sound.play()

    def _do_light_3(self) -> None:
        assert self._start_lights is not None
        self._start_lights[2].color = (1.0, 0.3, 0)
        self._beep_1_sound.play()

    def _start_race(self) -> None:
        assert self._start_lights is not None
        self._start_lights[3].color = (0.0, 1.0, 0)
        self._beep_2_sound.play()

        self._started = True

        for player in self.players:
            self.generate_mines(player)

    # overriding the default character spawning..
    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player()

        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        if self._started:
            self.generate_mines(player)
        return spaz

    def generate_mines(self, player: Player):
        try:
            player.actived = bs.Timer(
                0.5, babase.CallStrict(self.spawn_mine, player), repeat=True
            )
        except Exception as e:
            print('Exception -> ' + str(e))

    def spawn_mine(self, player: Player):
        if self.has_ended():
            return

        actor = player.actor
        if actor is None or actor.node is None or not actor.node.exists():
            return
        if not actor.is_alive():
            return

        if self._score_to_win is None or player.team.score >= self._score_to_win:
            return

        pos = actor.node.position
        mine = SnakeMine(
            position=(pos[0], pos[1] + 2.0, pos[2]),
        ).autoretain()
        bs.timer(0.5, babase.WeakCallStrict(mine.arm))

        player.mines.append(mine)
        player.mines = [m for m in player.mines if m and not m.expired]
        if len(player.mines) > 15:
            old_mine = player.mines.pop(0)
            if old_mine and not old_mine.expired:
                old_mine.handlemessage(bs.DieMessage())

        self.handlemessage(ScoreMessage(player))

    def _clear_player_mines(self, player: Player) -> None:
        for mine in list(player.mines):
            if mine and not mine.expired:
                mine.handlemessage(bs.DieMessage())
        player.mines.clear()

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self._clear_player_mines(player)
            self.respawn_player(player)

            player.actived = None

        elif isinstance(msg, ScoreMessage):
            player = msg.getplayer()

            player.team.score += 1
            self._update_scoreboard()

            assert self._score_to_win is not None
            if any(team.score >= self._score_to_win for team in self.teams):
                self.end_game()  # bs.timer(0.5, self.end_game)
        else:
            return super().handlemessage(msg)
        return None

    def on_player_leave(self, player: Player) -> None:
        self._clear_player_mines(player)
        super().on_player_leave(player)

    def on_end(self) -> None:
        for player in self.players:
            self._clear_player_mines(player)
        super().on_end()

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.score, self._score_to_win
            )

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
