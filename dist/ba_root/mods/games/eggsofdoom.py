# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# Released under the MIT License. See LICENSE for details.
# Created by Mr.Smoothy -
# https://discord.gg/ucyaesh
# https://bombsquad-community.web.app/home for more mods.
#
"""DeathMatch game and support classes."""

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)
from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.game.deathmatch import DeathMatchGame, Player, Team
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class _TouchedMessage:
    pass


# ba_meta export bascenev1.GameActivity


class FireChainGame(DeathMatchGame):
    """A game type based on acquiring kills."""

    name = 'Eggs of Doom'
    description = 'Kill a set number of enemies to win.'

    # Print messages when players die since it matters here.
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[babase.Setting]:
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

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Doom Shroom']

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

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.TO_THE_DEATH
        )

        self.wtindex = 0
        self.wttimer = bs.timer(5, babase.CallStrict(self.wt_), repeat=True)
        self.wthighlights = [
            'Created by Mr.Smoothy',
            'hey smoothy youtube',
            'smoothy#multiverse',
        ]

    def wt_(self):
        node = bs.newnode(
            'text',
            attrs={
                'text': self.wthighlights[self.wtindex],
                'flatness': 1.0,
                'h_align': 'center',
                'v_attach': 'bottom',
                'scale': 0.7,
                'position': (0, 20),
                'color': (0.5, 0.5, 0.5),
            },
        )

        self.delt = bs.timer(4, node.delete)
        self.wtindex = int((self.wtindex + 1) % len(self.wthighlights))

    def get_instance_description(self) -> str | Sequence:
        return 'Crush ${ARG1} of your enemies.', self._score_to_win

    def get_instance_description_short(self) -> str | Sequence:
        return 'kill ${ARG1} enemies', self._score_to_win

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()

        # Base kills needed to win on the size of the largest team.
        self._score_to_win = self._kills_to_win_per_player * max(
            1, max(len(t.players) for t in self.teams)
        )
        self._update_scoreboard()
        RollingEgg((0.5, 2.7, -4), 1.5)
        RollingEgg((0.5, 2.7, -4), 2)
        RollingEgg((0.5, 2.7, -4), 2.5)
        RollingEgg((0.5, 2.7, -4), 3)
        RollingEgg((0.5, 2.5, -4), 3.5)
        RollingEgg((0.5, 2.5, -4), 4)
        RollingEgg((0.5, 2.5, -4), 4.5)
        RollingEgg((0.5, 2.5, -4), 5)
        RollingEgg((0.5, 2.5, -4), 5.5)

    def handlemessage(self, msg: Any) -> Any:
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

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)


class RollingEgg(bs.Actor):
    def __init__(self, position, radius):
        super().__init__()
        shared = SharedObjects.get()
        factory = SpazFactory.get()
        self._spawn_pos = position
        self.powerup_material = bs.Material()
        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _TouchedMessage()),
            ),
        )
        self.direction = (0, 0, 0)
        pmats = [shared.object_material, self.powerup_material]
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': bs.getmesh('egg'),
                'color_texture': bs.gettexture(
                    random.choice(['eggTex1', 'eggTex2', 'eggTex3'])
                ),
                'body': 'sphere',
                'reflection': 'soft',
                'reflection_scale': [0.2],
                'gravity_scale': 0.3,
                'mesh_scale': 0.5,
                'body_scale': 0.6,
                'shadow_size': 0.5,
                'is_area_of_interest': True,
                'position': position,
                'materials': pmats,
            },
        )
        self.radius = radius
        self.center = position
        self.angle = 0
        self.surroundTimer = bs.Timer(0.3, self.update, repeat=True)
        self.delta_time = 0.3
        self.angular_speed = math.pi / 2

    def update(self):
        # Calculate new angle based on time
        self.angle += self.delta_time

        # Calculate new position
        new_x = self.center[0] + self.radius * math.cos(self.angle)
        new_z = self.center[2] + self.radius * math.sin(self.angle)
        new_y = self.node.position[1]  # rotation around the Y-axis

        new_position = (new_x, new_y, new_z)

        # Calculate velocity
        self.direction = [
            new_position[i] - self.node.position[i] for i in range(3)
        ]
        velocity = [self.direction[i] / self.delta_time for i in range(3)]

        self.node.velocity = velocity

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.position = self._spawn_pos
        elif isinstance(msg, _TouchedMessage):
            node = bs.getcollision().opposingnode
            node.handlemessage(
                bs.HitMessage(
                    velocity=self.node.velocity,
                    velocity_magnitude=90,
                    radius=0,
                    srcnode=self.node,
                    force_direction=self.direction,
                    hit_type='punch',
                )
            )
        elif isinstance(msg, bs.OutOfBoundsMessage):
            assert self.node
            self.node.position = self._spawn_pos
        else:
            return super().handlemessage(msg)
