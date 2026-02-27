# Released under the MIT License. See LICENSE for details.
# Modified for gosquad server.
#
"""DeathMatch game and support classes."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from enum import IntEnum
from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class BombType(IntEnum):
    DEFAULT = 0
    NORMAL = 1
    STICKY = 2
    TRIGGER = 3
    ICE = 4

    @property
    def as_str(self) -> str:
        return {
            BombType.DEFAULT: 'default',
            BombType.NORMAL: 'normal',
            BombType.STICKY: 'sticky',
            BombType.TRIGGER: 'impact',
            BombType.ICE: 'ice',
        }[self]

    @staticmethod
    def from_int(value: int) -> BombType:
        return BombType(value)


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class DeathMatchGame(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Death Match'
    description = 'Kill a set number of enemies to win.'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Kills to Win Per Player',
                min_value=1,
                default=5,
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
            bs.BoolSetting('Equip Gloves', default=True),
            bs.BoolSetting('Equip Speed', default=False),
            bs.BoolSetting('Equip Shield', default=False),
            bs.BoolSetting('Equip Powers', default=False),
            bs.BoolSetting('Meteor Shower', default=False),
            bs.IntChoiceSetting(
                'Meteor Delay',
                choices=[
                    ('None', 0),
                    ('15 Seconds', 15),
                    ('30 Seconds', 30),
                    ('45 Seconds', 45),
                    ('1 Minutes', 60),
                    ('1.5 Minutes', 90),
                    ('2 Minutes', 120),
                    ('3 Minutes', 180),
                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Bomb Count',
                choices=[
                    ('Default', 0),
                    ('1', 1),
                    ('2', 2),
                    ('3', 3),
                    ('4', 4),
                    ('5', 5),
                    ('6', 6),
                ],
                default=0,
            ),
            bs.IntChoiceSetting(
                'Bomb Type',
                choices=[
                    ('Default', 0),
                    ('Normal', 1),
                    ('Sticky', 2),
                    ('Trigger', 3),
                    ('Ice', 4),
                ],
                default=0,
            ),
        ]

        # In teams mode, a suicide gives a point to the other team, but in
        # free-for-all it subtracts from your own score. By default we clamp
        # this at zero to benefit new players, but pro players might like to
        # be able to go negative. (to avoid a strategy of just
        # suiciding until you get a good drop)
        if issubclass(sessiontype, bs.FreeForAllSession):
            settings.append(
                bs.BoolSetting('Allow Negative Scores', default=False)
            )

        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        assert bs.app.classic is not None
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._score_to_win: int | None = None
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
        self._kills_to_win_per_player = int(settings['Kills to Win Per Player'])
        self._time_limit = float(settings['Time Limit'])
        self._allow_negative_scores = bool(
            settings.get('Allow Negative Scores', False)
        )
        self._equip_gloves = bool(settings.get('Equip Gloves', False))
        self._equip_speed = bool(settings.get('Equip Speed', False))
        self._equip_shield = bool(settings.get('Equip Shield', False))
        self._equip_powers = bool(settings.get('Equip Powers', False))
        self._meteor_shower = bool(settings.get('Meteor Shower', False))
        self._meteor_start_time = float(settings.get('Meteor Delay', 15))
        self._bomb_count = int(settings.get('Bomb Count', 1))
        bomb_type_raw = BombType.from_int(settings.get('Bomb Type', 0))
        self._bomb_type = str(bomb_type_raw.as_str)

        self._bomb_time = 3.0
        self._bomb_scale = 0.1

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.TO_THE_DEATH
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'Crush ${ARG1} of your enemies.', self._score_to_win

    @override
    def get_instance_description_short(self) -> str | Sequence:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        return 'kill ${ARG1} enemies', self._score_to_win

    @override
    def on_team_join(self, team: Team) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if self.has_begun():
            self._update_scoreboard()

    @override
    def on_transition_in(self) -> None:
        # (Pylint bug?) pylint: disable=missing-function-docstring

        super().on_transition_in()
        shared = SharedObjects.get()
        if self._equip_speed and (
            self.map.getname() in ('Hockey Stadium', 'Lake Frigid')
        ):
            self.map.node.materials = [shared.footing_material]
            self.map.floor.materials = [shared.footing_material]

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()

        # Base kills needed to win on the size of the largest team.
        self._score_to_win = self._kills_to_win_per_player * max(
            1, max((len(t.players) for t in self.teams), default=0)
        )
        if self._meteor_shower:
            bs.timer(self._meteor_start_time, self._initiate_bomb)

        self.bounds = list(
            self.map.get_def_bound_box('area_of_interest_bounds')
        )
        self._update_scoreboard()

    def _initiate_bomb(self) -> None:
        delay = 1.0
        bs.timer(delay, self._decrement_bomb_time, repeat=True)
        bs.timer(delay, self._increment_bomb_scale, repeat=True)

        # Kick off the first wave in a few seconds.
        self._set_bomb_timer()

    def _set_bomb_timer(self) -> None:
        bs.timer(self._bomb_time, self._drop_bomb_cluster)

    def _drop_bomb_cluster(self) -> None:
        # Random note: code like this is a handy way to plot out extents
        # and debug things.
        loc_test = False
        if loc_test:
            bs.newnode('locator', attrs={'position': (8, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (8, 6, -2.3)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -2.3)})

        # Drop several bombs in series.
        # Drop them somewhere within our bounds with velocity pointing
        # toward the opposite side.
        vel = None
        random_pos = False
        map_name = self.map.getname()
        if map_name == 'Rampage':
            pos = (random.randrange(-7, 8), 11, random.randrange(-5, -2))
        elif map_name == 'Hockey Stadium':
            pos = (random.randrange(-11, 12), 6, random.randrange(-4, 5))
        else:
            random_pos = True
            pos = (
                random.uniform(self.bounds[0], self.bounds[3]),
                self.bounds[4],
                random.uniform(self.bounds[2], self.bounds[5]),
            )
            dropdirx = -1 if pos[0] > 0 else 1
            dropdirz = -1 if pos[2] > 0 else 1
            forcex = (
                self.bounds[0] - self.bounds[3]
                if self.bounds[0] - self.bounds[3] > 0
                else -(self.bounds[0] - self.bounds[3])
            )
            forcez = (
                self.bounds[2] - self.bounds[5]
                if self.bounds[2] - self.bounds[5] > 0
                else -(self.bounds[2] - self.bounds[5])
            )
            vel = (
                (-5 + random.random() * forcex) * dropdirx,
                random.uniform(-3.066, -4.12),
                (-5 + random.random() * forcez) * dropdirz,
            )

        if not random_pos:
            dropdir = -1.0 if pos[0] > 0 else 1.0
            vel = (
                (-5.0 + random.random() * 30.0) * dropdir,
                random.uniform(-3.066, -4.12),
                0,
            )

        self._drop_bomb(pos, vel)
        self._set_bomb_timer()

    def _drop_bomb(
        self, position: Sequence[float], velocity: Sequence[float]
    ) -> None:
        bomb_type = random.choice(
            [
                'land_mine',
                'land_mine',
                'tnt',
                'tnt',
                'impact',
                'sticky',
                'power',
                'shatter',
            ]
        )
        bomb = Bomb(
            position=position,
            velocity=velocity,
            bomb_type=bomb_type,
            blast_radius=3.0 if bomb_type == 'impact' else self._bomb_scale,
            animate=False,
        ).autoretain()

        if bomb_type != 'impact':
            bs.animate(
                bomb.node,
                'mesh_scale',
                {0.0: 0.2, 0.7: 0.2, 1.0: self._bomb_scale},
            )

        if bomb_type == 'land_mine':
            bs.timer(1.2, bomb.arm)

    def _decrement_bomb_time(self) -> None:
        self._bomb_time = max(1.5, self._bomb_time * 0.95)

    def _increment_bomb_scale(self) -> None:
        self._bomb_scale = min(8.0, self._bomb_scale * 1.05)
        # Less aggresive than elimination

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)

        if self._equip_gloves:
            spaz.default_boxing_gloves = True
            spaz.equip_boxing_gloves()
        if self._equip_shield:
            spaz.default_shields = True
            spaz.equip_shields()
        if self._equip_speed:
            spaz.equip_speed()
        if self._equip_powers:
            spaz.equip_dash()
            spaz.equip_super_jump()

        bomb_count = (
            spaz.bomb_count if self._bomb_count == 0 else self._bomb_count
        )
        spaz.bomb_count = spaz._bomb_count = bomb_count
        bomb_type = (
            spaz.bomb_type if self._bomb_type == 'default' else self._bomb_type
        )
        spaz.bomb_type = spaz.bomb_type_default = bomb_type

        return spaz

    @override
    def handlemessage(self, msg: Any) -> Any:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)

            killer = msg.getkillerplayer(Player)
            if killer is None:
                return None

            # Handle team-kills.
            if killer.team is player.team:
                # In free-for-all, killing yourself loses you a point.
                if isinstance(self.session, bs.FreeForAllSession):
                    new_score = player.team.score - 1
                    if not self._allow_negative_scores:
                        new_score = max(0, new_score)
                    player.team.score = new_score

                # In teams-mode it gives a point to the other team.
                else:
                    self._dingsound.play()
                    for team in self.teams:
                        if team is not killer.team:
                            team.score += 1

            # Killing someone on another team nets a kill.
            else:
                killer.team.score += 1
                self._dingsound.play()

                # In FFA show scores since its hard to find on the scoreboard.
                if isinstance(killer.actor, PlayerSpaz) and killer.actor:
                    killer.actor.set_score_text(
                        str(killer.team.score) + '/' + str(self._score_to_win),
                        color=killer.team.color,
                        flash=True,
                    )

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

    @override
    def end_game(self) -> None:
        # (Pylint Bug?) pylint: disable=missing-function-docstring

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
