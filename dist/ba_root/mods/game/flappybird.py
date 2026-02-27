# Released under the MIT License. See LICENSE for details.
#
"""Defines a bomb-dodging mini-game."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.bomb import Blast, Bomb, BombFactory
from bascenev1lib.actor.onscreentimer import OnScreenTimer
from bascenev1lib.game.meteorshower import MeteorShowerGame, Player
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


# ba_meta export bascenev1.GameActivity
class FlappyBirdGame(MeteorShowerGame):
    """."""

    name = 'Flappy Bird'
    description = 'Be Alive'
    available_settings = [bs.BoolSetting('Epic Mode', default=False)]
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.MILLISECONDS, version='B'
    )

    # Print messages when players die (since its meaningful in this game).
    announce_player_deaths = True

    # Don't allow joining after we start
    # (would enable leave/rejoin tomfoolery).
    allow_mid_activity_joins = False

    # We're currently hard-coded for one map.
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Creative Thoughts']

    # We support teams, free-for-all, and co-op sessions.
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return (
            issubclass(sessiontype, bs.DualTeamSession)
            or issubclass(sessiontype, bs.FreeForAllSession)
            or issubclass(sessiontype, bs.CoopSession)
        )

    def __init__(self, settings: dict):
        super().__init__(settings)

        self._epic_mode = settings.get('Epic Mode', False)
        self._last_player_death_time: float | None = None
        self._meteor_time = 2.0
        self._timer: OnScreenTimer | None = None

        # Some base class overrides:
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )
        if self._epic_mode:
            self.slow_motion = True
        shared = SharedObjects.get()
        self._real_wall_material = bs.Material()

        self._real_wall_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )
        self._fake_wall_material = bs.Material()

        self._fake_wall_material.add_actions(
            conditions=(
                ('they_are_younger_than', 9000),
                'and',
                ('they_have_material', shared.player_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )

        self.blocksLeft = bs.newnode(
            'region',
            attrs={
                'position': (-11.75152479, 6.057427485, -5.52),
                'scale': (9, 3, 6),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    self._fake_wall_material,
                ],
            },
        )
        self.blocksRight = bs.newnode(
            'region',
            attrs={
                'position': (5.75152479, 6.057427485, -5.52),
                'scale': (9, 3, 6),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    self._fake_wall_material,
                ],
            },
        )
        factory = BombFactory.get()
        self.bomb_material = factory.impact_blast_material
        self.collide_with_bomb_material = bs.Material()
        self.collide_with_bomb_material.add_actions(
            conditions=('they_have_material', factory.impact_blast_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
                ('call', 'at_connect', babase.CallStrict(self._handle_impact)),
            ),
        )
        self.left_region_material = bs.Material()
        self.left_region_material.add_actions(
            conditions=('they_have_material', factory.impact_blast_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
                (
                    'call',
                    'at_connect',
                    babase.CallStrict(self._handle_impact_with_wall),
                ),
            ),
        )

        self.left_end_Region = bs.newnode(
            'region',
            attrs={
                'position': (-18.75152479, 21.057427485, -5.52),
                'scale': (2, 42, 6),
                'type': 'box',
                'materials': [self.left_region_material],
            },
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

    def on_begin(self) -> None:
        super().on_begin()

        # Drop a wave every few seconds.. and every so often drop the time
        # between waves ..lets have things increase faster if we have fewer
        # players.
        # delay = 5.0 if len(self.players) > 2 else 2.5
        # if self._epic_mode:
        #     delay *= 0.25
        # bs.timer(delay, self._decrement_meteor_time, repeat=True)

        # # Kick off the first wave in a few seconds.
        # delay = 3.0
        # if self._epic_mode:
        #     delay *= 0.25
        self._meteor_time = 3
        self._set_meteor_timer()
        # self.spawn_meteors()
        # self.spawn_meteors()
        # self.spawn_meteors()
        bs.get_foreground_host_activity().globalsnode.tint = (0.5, 0.7, 1.0)
        self._timer = OnScreenTimer()
        self._timer.start()

        # Check for immediate end (if we've only got 1 player, etc).
        bs.timer(5.0, self._check_end_game)

    def on_player_leave(self, player: Player) -> None:
        # Augment default behavior.
        super().on_player_leave(player)

        # A departing player may trigger game-over.
        self._check_end_game()

    def spawn_player_spaz(
        self,
        player: Player,
        position: Sequence[float] = None,
        angle: float = None,
    ):
        """Intercept new spazzes and add our team material for them."""

        position = (-11.35152479, 7.057427485, -5.52)

        spaz = super().spawn_player_spaz(player, position, angle)
        spaz.node.materials = list(spaz.node.materials) + [
            self.collide_with_bomb_material
        ]
        spaz.node.roller_materials = list(spaz.node.roller_materials) + [
            self.collide_with_bomb_material
        ]
        return spaz

    # overriding the default character spawning..

    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)

        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player(
            enable_punch=False, enable_bomb=False, enable_pickup=True
        )

        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    # Various high-level game events come through this method.
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)

            curtime = bs.time()

            # Record the player's moment of death.
            # assert isinstance(msg.spaz.player
            msg.getplayer(Player).death_time = curtime

            # In co-op mode, end the game the instant everyone dies
            # (more accurate looking).
            # In teams/ffa, allow a one-second fudge-factor so we can
            # get more draws if players die basically at the same time.
            if isinstance(self.session, bs.CoopSession):
                # Teams will still show up if we check now.. check in
                # the next cycle.
                babase.pushcall(self._check_end_game)

                # Also record this for a final setting of the clock.
                self._last_player_death_time = curtime
            else:
                bs.timer(1.0, self._check_end_game)

        else:
            # Default handler:
            return super().handlemessage(msg)
        return None

    def _check_end_game(self) -> None:
        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break

        # In co-op, we go till everyone is dead.. otherwise we go
        # until one team remains.
        if isinstance(self.session, bs.CoopSession):
            if living_team_count <= 0:
                self.end_game()
        else:
            if living_team_count <= 1:
                self.end_game()

    def _set_meteor_timer(self) -> None:
        bs.timer(self._meteor_time, self._drop_bomb_cluster)

    def _drop_bomb_cluster(self) -> None:
        # Random note: code like this is a handy way to plot out extents
        # and debug things.
        loc_test = False
        if loc_test:
            bs.newnode('locator', attrs={'position': (8, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (8, 6, -2.3)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -5.5)})
            bs.newnode('locator', attrs={'position': (-7.3, 6, -2.3)})

        if self._meteor_time > 1:
            self._meteor_time -= 0.02

        self.spawn_meteors()

        self._set_meteor_timer()

    def _drop_bomb(
        self, position: Sequence[float], velocity: Sequence[float]
    ) -> None:
        Bomb(position=position, velocity=velocity).autoretain()

    def _decrement_meteor_time(self) -> None:
        self._meteor_time = max(0.1, self._meteor_time * 0.9)

    def end_game(self) -> None:
        cur_time = bs.time()
        assert self._timer is not None
        start_time = self._timer.getstarttime()

        # Mark death-time as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:
                survived = False

                # Throw an extra fudge factor in so teams that
                # didn't die come out ahead of teams that did.
                if player.death_time is None:
                    survived = True
                    player.death_time = cur_time + 1

                # Award a per-player score depending on how many seconds
                # they lasted (per-player scores only affect teams mode;
                # everywhere else just looks at the per-team score).
                score = int(player.death_time - self._timer.getstarttime())
                if survived:
                    score += 50  # A bit extra for survivors.
                self.stats.player_scored(player, score, screenmessage=False)

        # Stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endtime=self._last_player_death_time)

        # Ok now calc game results: set a score for each team and then tell
        # the game to end.
        results = bs.GameResults()

        # Remember that 'free-for-all' mode is simply a special form
        # of 'teams' mode where each player gets their own team, so we can
        # just always deal in teams and have all cases covered.
        for team in self.teams:
            # Set the team score to the max time survived by any player on
            # that team.
            longest_life = 0.0
            for player in team.players:
                assert player.death_time is not None
                longest_life = max(longest_life, player.death_time - start_time)

            # Submit the score value in milliseconds.
            results.set_team_score(team, int(1000.0 * longest_life))

        self.end(results=results)

    def _handle_impact(self):
        try:
            bomb = bs.getcollision().opposingnode
            pos = bomb.position
            Blast(position=pos)
            bomb.delete()

        except bs.NotFoundError:
            # This can happen if the flag stops touching us due to being
            # deleted; that's ok.
            return

    def _handle_impact_with_wall(self):
        try:
            bomb = bs.getcollision().opposingnode
            pos = bomb.position

            bomb.delete()

        except bs.NotFoundError:
            # This can happen if the flag stops touching us due to being
            # deleted; that's ok.
            return

    def generate_hurdles(self):
        pass

    def spawn_meteors(self):
        y = random.randrange(4, 21)
        factory = BombFactory.get()

        node1 = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': (17, y, -5.506),
                'velocity': (0, 0, 0),
                'body': 'sphere',
                'body_scale': 1.0,
                'mesh': factory.impact_bomb_mesh,
                'shadow_size': 0.3,
                'color_texture': factory.impact_tex,
                'reflection': 'powerup',
                'reflection_scale': [1.5],
                'materials': [
                    self.bomb_material,
                ],
            },
        )

        bs.animate_array(
            node1, 'position', 3, {0: (17, y, -5.506), 19: (-19, y, -5.506)}
        )
        # y = random.randrange(4, 21)

        # node2 = bs.newnode('prop',
        #                    delegate=self,
        #                    attrs={
        #                        'position': (17, y, -5.506),
        #                        'velocity': (0, 0, 0),
        #                        'body': 'sphere',
        #                                'body_scale': 1.0,
        #                                'mesh': factory.impact_bomb_mesh,
        #                                'shadow_size': 0.3,
        #                                'color_texture': factory.impact_tex,
        #                                'reflection': 'powerup',
        #                                'reflection_scale': [1.5],
        #                                'materials': [self.bomb_material,]
        #                    })

        # bs.animate_array(node2, 'position', 3, {
        #                  0: (17, y, -5.506), 19: (-19, y, -5.506)})
        # y = random.randrange(4, 21)

        # node3 = bs.newnode('prop',
        #                    delegate=self,
        #                    attrs={
        #                        'position': (17, y, -5.506),
        #                        'velocity': (0, 0, 0),
        #                        'body': 'sphere',
        #                                'body_scale': 1.0,
        #                                'mesh': factory.impact_bomb_mesh,
        #                                'shadow_size': 0.3,
        #                                'color_texture': factory.impact_tex,
        #                                'reflection': 'powerup',
        #                                'reflection_scale': [1.5],
        #                                'materials': [self.bomb_material,]
        #                    })

        # bs.animate_array(node3, 'position', 3, {
        #                  0: (17, y, -5.506), 19: (-19, y, -5.506)})
