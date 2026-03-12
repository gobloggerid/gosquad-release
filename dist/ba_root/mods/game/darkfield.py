# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# Made by Froshlee14
# Ported by Freaku / @[Just] Freak#4999
# Ported to api 9 by n00bility
# Modified for gosquad server by n00bility

# ba_meta require api 9
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class DarkFieldGame(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Dark Fields'
    description = 'Get to the other side.'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[babase.Setting]:
        settings = [
            bs.IntSetting(
                'Score to Win Per Player',
                min_value=1,
                default=3,
                increment=1,
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
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
        self._score_to_win: int | None = None
        self._score_to_win_per_player = int(
            settings['Score to Win Per Player']
        )
        self._time_limit = float(settings['Time Limit'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.TO_THE_DEATH
        )

        self._block_wall_regions: list[bs.NodeActor] = []

        # Deny access to the raised safe platform.
        self._block_wall_pos = (-0.0, 4.6, 7.0)
        self._block_wall_pos_2 = (-0.0, 7.6, -6.1)
        self._block_wall_scale = (28, 12, 0.5)

        self._scoreRegionMaterial = bs.Material()
        self._scoreRegionMaterial.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._on_player_scores),
            ),
        )
        self.first_time = True

        self.block_player_region_material = bs.Material()
        self.block_player_region_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )

    def on_transition_in(self) -> None:
        super().on_transition_in()

        self._block_wall_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': self._block_wall_pos,
                        'scale': self._block_wall_scale,
                        'type': 'box',
                        'materials': [self.block_player_region_material],
                    },
                )
            )
        )
        self._block_wall_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': self._block_wall_pos_2,
                        'scale': self._block_wall_scale,
                        'type': 'box',
                        'materials': [self.block_player_region_material],
                    },
                )
            )
        )

    def get_instance_description(self) -> str | Sequence:
        return 'Get to the other side ${ARG1} times', self._score_to_win

    def get_instance_description_short(self) -> str | Sequence:
        return 'Get to the other side ${ARG1} times', self._score_to_win

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        bs.getactivity().globalsnode.tint = (0.5, 0.5, 0.5)
        a = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': (12, 0, 0.1087926362),
                'color': (5, 5, 5),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [2.0, 0.1, 11.8],
            },
        )
        b = bs.newnode(
            'locator',
            attrs={
                'shape': 'box',
                'position': (-12, 0, 0.1087926362),
                'color': (5, 5, 5),
                'opacity': 1,
                'draw_beauty': True,
                'additive': False,
                'size': [2.0, 0.1, 11.8],
            },
        )
        self.is_updating_mines = False
        self._scoreSound = bs.getsound('dingSmall')
        self.setup_standard_time_limit(self._time_limit)
        self._score_to_win = self._score_to_win_per_player * max(
            1, max((len(t.players) for t in self.teams), default=0)
        )

        self._update_scoreboard()
        for p in self.players:
            if p.actor is not None:
                try:
                    p.actor.disconnect_controls_from_player()
                except Exception as e:
                    print("Can't connect to player", e)

        self._scoreRegions = []
        defs = self.map.defs
        self._scoreRegions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': defs.boxes['goal1'][0:3],
                        'scale': defs.boxes['goal1'][6:9],
                        'type': 'box',
                        'materials': [self._scoreRegionMaterial],
                    },
                )
            )
        )
        self.mines = []
        self.spawn_mines()
        bs.timer(2.5, self.start)

    def start(self):
        bs.timer(random.randrange(3, 7), self.do_random_lighting)
        bs.animate_array(
            bs.getactivity().globalsnode,
            'tint',
            3,
            {0: (0.5, 0.5, 0.5), 2: (0.2, 0.2, 0.2)},
        )

    def do_random_lighting(self):
        bs.timer(random.randrange(3, 7), self.do_random_lighting)
        if self.is_updating_mines:
            return
        bs.animate_array(
            bs.getactivity().globalsnode,
            'tint',
            3,
            {0: (0.5, 0.5, 0.5), 0.8: (0.2, 0.2, 0.2)},
        )

    def spawn_mines(self):
        delay = 0
        xs = [10, 8, 6, 4, 2, 0, -2, -4, -6, -8, -10]
        for x in xs:
            for i in range(3):
                pos = (x, 1, random.randrange(-5, 6))
                bs.timer(delay, babase.CallStrict(self.do_mine, pos))
                delay += 0.075
        bs.timer(2.48, self.stop_update_mines)

    def stop_update_mines(self):
        self.is_updating_mines = False
        self.first_time = False

    def update_mines(self):
        if self.is_updating_mines:
            return
        self.is_updating_mines = True
        for m in self.mines:
            if m.node:
                m.node.delete()
        self.mines = []
        self.spawn_mines()

    def do_mine(self, pos):
        b = Bomb(position=pos, bomb_type='land_mine').autoretain()
        b.arm()
        self.mines.append(b)

    # overriding the default character spawning..
    def spawn_player(self, player: Player):
        if self.first_time:
            bs.timer(2.5, babase.CallStrict(self.spawn_with_delay, player))
        else:
            self.spawn_with_delay(player)

    def spawn_with_delay(self, player: Player):
        if self.has_ended() or self.expired or not player.exists():
            return None
        spaz = self.spawn_player_spaz(player)
        position = (-12.4, 1, random.randrange(-5, 5))
        spaz.connect_controls_to_player(enable_punch=False, enable_bomb=False)
        spaz.handlemessage(bs.StandMessage(position, random.uniform(0, 360)))
        return spaz

    def _on_player_scores(self):
        try:
            player = (
                bs.getcollision()
                .opposingnode.getdelegate(PlayerSpaz, True)
                .getplayer(Player, True)
            )
        except Exception:
            player = None
        if player is not None and player.is_alive():
            for team in self.teams:
                if team is player.team:
                    team.score += 1
            self._scoreSound.play()
            bs.animate_array(
                bs.getactivity().globalsnode,
                'tint',
                3,
                {0: (0.5, 0.5, 0.5), 2.8: (0.2, 0.2, 0.2)},
            )
            self._update_scoreboard()
            position = (-12.4, 1, random.randrange(-5, 5))
            player.actor.handlemessage(
                bs.StandMessage(position, random.uniform(0, 360))
            )
            self.update_mines()
            self._update_scoreboard()

            # If someone has won, set a timer to end shortly.
            # (allows the dust to clear and draws to occur if deaths are
            # close enough)
            assert self._score_to_win is not None
            if any(team.score >= self._score_to_win for team in self.teams):
                bs.timer(0.5, self.end_game)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)

            self._update_scoreboard()

            # If someone has won, set a timer to end shortly.
            # (allows the dust to clear and draws to occur if deaths are
            # close enough)
            assert self._score_to_win is not None
            if any(team.score >= self._score_to_win for team in self.teams):
                bs.timer(0.5, self.end_game)

        else:
            return super().handlemessage(msg)
        return None

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
