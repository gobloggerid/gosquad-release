# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# Made by MattZ45986 on GitHub
# Ported by: Freaku / @[Just] Freak#4999
#
# Edited by goblogger
# Join BCS:
# https://discord.gg/ucyaesh
#
# ba_meta require api 9

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.flag import Flag, FlagPickedUpMessage
from bascenev1lib.actor.playerspaz import PlayerSpaz

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class Player(bs.Player['Team']):
    def __init__(self) -> None:
        self.done: bool = False
        self.survived: bool = True


class Team(bs.Team[Player]):
    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class NonMusicalFlagGame(bs.TeamGameActivity[Player, Team]):
    name = 'Non-Musical Flags'
    description = "Don't be the one stuck without a flag!"

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Max Round Time',
                min_value=10,
                default=15,
                increment=5,
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
                default=0.5,
            ),
            bs.BoolSetting('Enable Dash', default=True),
            bs.BoolSetting('Enable Super Jump', default=True),
            bs.BoolSetting('Epic Mode', default=False),
            bs.BoolSetting('Enable Running', default=True),
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
        self.nodes = []
        self._dingsound = bs.getsound('dingSmall')
        self._enable_dash = bool(settings['Enable Dash'])
        self._enable_super_jump = bool(settings['Enable Super Jump'])
        self._epic_mode = bool(settings['Epic Mode'])
        self.is_run = bool(settings['Enable Running'])
        # self._shared_spawn_point = (0, 0, 0)

        self._text_round = bs.newnode(
            'text',
            attrs={
                'text': '',
                'position': (0, -20),
                'scale': 1,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (1.0, 0.0, 1.0),
                'opacity': 1,
                'v_attach': 'top',
                'h_attach': 'center',
                'h_align': 'center',
                'v_align': 'center',
            },
        )
        self.round_time = int(settings['Max Round Time'])
        self.reset_round_time = int(settings['Max Round Time'])
        self.should_die_occur = True
        self.round_time_textnode = bs.newnode(
            'text',
            attrs={
                'text': '',
                'flatness': 1.0,
                'h_align': 'center',
                'h_attach': 'center',
                'v_attach': 'top',
                'v_align': 'center',
                'position': (0, -50),
                'scale': 0.9,
                'color': (0, 1.0, 1.0),
            },
        )

        self.slow_motion = self._epic_mode
        # A cool music, matching our gamemode theme
        self.default_music = bs.MusicType.FLAG_CATCHER

        # stuff
        self.round_num = 0
        self.num_pickedup = 0
        self.flag_count = 0
        self.nodes = []
        self.flags = []
        self.spawned = []
        self.flag_spawn_position = []
        self.spawned_positions = []
        self.keepcalling: bs.Timer | None = None

    def get_instance_description(self) -> str | Sequence:
        return 'Catch Flag for yourself'

    def get_instance_description_short(self) -> str | Sequence:
        return 'Catch Flag for yourself'

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            bs.broadcastmessage(
                babase.Lstr(
                    resource='playerDelayedJoinText',
                    subs=[('${PLAYER}', player.getname(full=True))],
                ),
                color=(0, 1, 0),
                transient=True,
            )
            player.survived = False
            return
        self.spawn_player(player)

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        # A departing player may trigger game-over.
        bs.timer(0.25, self.check_end)

    def on_begin(self) -> None:
        super().on_begin()
        self.collect_spawn_points()
        self.setup_standard_powerup_drops()
        self.start_round()
        self._text_round.text = f'Round {str(self.round_num)}'
        bs.timer(3, self.check_end)
        self.keepcalling = bs.timer(1, self._timeround, True)
        bs.timer(15.0, self.credit_text, repeat=True)

    def credit_text(self) -> None:
        credit = bs.newnode(
            'text',
            attrs={
                'text': 'Modded Musical Flags | Author: MattZ45986, Freaku',
                'scale': 0.7,
                'position': (0, 0),
                'shadow': 0.5,
                'flatness': 1.0,
                'color': (0.5, 1.0, 0.5),
                'h_align': 'center',
                'v_attach': 'bottom',
            },
        )
        bs.timer(10.0, credit.delete)

    def _timeround(self):
        if self.round_time == 0 and self.should_die_occur:
            self.should_die_occur = False
            self.round_time_textnode.opacity = 0
            bs.broadcastmessage(
                'You guys should catch the flag!', color=(0.8, 0.0, 0.8)
            )
            for player in self.spawned:
                if not player.done:
                    try:
                        player.survived = False
                        flag_pos = self.map.get_flag_position(None)
                        pos = (flag_pos[0], flag_pos[1] + 1.5, flag_pos[2])
                        player.actor.handlemessage(bs.StandMessage(pos))
                        bs.timer(
                            0.5,
                            bs.CallStrict(
                                player.actor.handlemessage, bs.FreezeMessage()
                            ),
                        )
                        bs.timer(
                            1.5,
                            bs.CallStrict(
                                player.actor.handlemessage, bs.FreezeMessage()
                            ),
                        )
                        bs.timer(
                            2.5,
                            bs.CallStrict(
                                player.actor.handlemessage, bs.FreezeMessage()
                            ),
                        )
                        bs.timer(
                            3,
                            bs.CallStrict(
                                player.actor.handlemessage,
                                bs.ShouldShatterMessage(),
                            ),
                        )
                    except Exception:
                        pass
            bs.timer(3.5, self.kill_round)
            bs.timer(3.55, self.start_round)
            self.round_time_textnode.opacity = 0
            self.round_time = self.reset_round_time
        else:
            self.round_time_textnode.text = 'Time Left: ' + str(self.round_time)
            self.round_time -= 1

    def start_round(self):
        for player in self.players:
            if player.survived:
                player.team.score += 1
        self.round_num += 1
        self._text_round.text = f'Round {str(self.round_num)}'
        self.spawned_positions = self.flag_spawn_position.copy()
        self.flags.clear()
        self.spawned.clear()
        self.should_die_occur = True
        self.round_time = self.reset_round_time
        self.round_time_textnode.opacity = 1

        for player in self.players:
            player.done = False
            if player.survived:
                if not player.is_alive():
                    self.spawn_player(player)
                self.spawned.append(player)

        colors = [
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (1, 1, 0),
            (1, 0, 1),
            (0, 1, 1),
            (0, 0, 0),
            (0.5, 0.8, 0),
            (0, 0.8, 0.5),
            (0.8, 0.25, 0.7),
            (0, 0.27, 0.55),
            (2, 2, 0.6),
            (0.4, 3, 0.85),
        ]

        p_count = len([p for p in self.players if p.survived])
        # Add support for more than 13 players
        if p_count > 12:
            for i in range(p_count - 12):
                colors.append(
                    (
                        random.uniform(0.1, 1),
                        random.uniform(0.1, 1),
                        random.uniform(0.1, 1),
                    )
                )

        flag_count = p_count - 1
        self.flag_count = flag_count
        for i in range(flag_count):
            color = colors[i % len(colors)]
            bs.timer(0.5 * i, bs.CallStrict(self.spawn_flag, color))

    def spawn_flag(self, color: tuple = (0, 0, 0)) -> None:
        try:
            fpos = (
                random.choice(self.spawned_positions)
                if self.spawned_positions
                else self.map.get_ffa_start_position(self.spawned)
            )
            pos = (fpos[0], fpos[1] + 2.0, fpos[2])
            flag = Flag(position=pos, color=color).autoretain()
            if fpos in self.spawned_positions:
                self.spawned_positions.remove(fpos)
            self.flags.append(flag)
        except Exception as e:
            logging.exception(f'Failed to spawn flag: {e}')

    def collect_spawn_points(self):
        self._collect_spawn_points(points_name='powerup_spawn')
        self._collect_spawn_points(points_name='ffa_spawn')
        self._collect_spawn_points(points_name='flag')
        self._collect_spawn_points(points_name='spawn')
        self._collect_spawn_points(points_name='tnt')

    def _collect_spawn_points(self, points_name: str):
        points = self.map.get_def_points(points_name)
        if points:
            points = [p[:3] for p in points]
            self.flag_spawn_position.extend(points)

    def kill_round(self):
        self.num_pickedup = 0
        for player in self.players:
            if player.is_alive():
                player.actor.handlemessage(bs.DieMessage())
        for flag in self.flags:
            flag.node.delete()
        for light in self.nodes:
            light.delete()

    def spawn_player(self, player: Player, pos: tuple = (0, 0, 0)) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)
        if pos == (0, 0, 0):
            flag_pos = self.map.get_flag_position(None)
            pos = (flag_pos[0], flag_pos[1] + 1.5, flag_pos[2])

        spaz.connect_controls_to_player(enable_run=self.is_run)
        spaz.handlemessage(bs.StandMessage(pos))
        if self._enable_dash:
            spaz.equip_dash()
        if self._enable_super_jump:
            spaz.equip_super_jump()
        return spaz

    def check_respawn(self, player):
        if not player.done and player.survived:
            self.respawn_player(player, 2.5)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            bs.timer(0.1, bs.CallStrict(self.check_respawn, player))
            bs.timer(0.5, self.check_end)
        elif isinstance(msg, FlagPickedUpMessage):
            self.num_pickedup += 1
            msg.node.getdelegate(PlayerSpaz, True).getplayer(
                Player, True
            ).done = True
            l = bs.newnode(
                'light',
                owner=None,
                attrs={
                    'color': msg.node.color,
                    'position': (msg.node.position_center),
                    'intensity': 1,
                },
            )
            self.nodes.append(l)
            msg.flag.handlemessage(bs.DieMessage())
            msg.node.handlemessage(bs.DieMessage())
            msg.node.delete()
            if self.num_pickedup == self.flag_count:
                self.round_time_textnode.opacity = 0
                self.round_time = self.reset_round_time
                for player in self.spawned:
                    if not player.done:
                        try:
                            message = [
                                f'You should have been faster, {player.getname(full=True)}!',
                                f'You are too slow, {player.getname(full=True)}!',
                                f'You are too slow to catch the flag, {player.getname(full=True)}!',
                                f'Why did you not catch the flag, {player.getname(full=True)}?',
                                f'Is it your first time playing, {player.getname(full=True)}?',
                                f'Do you understand the game, {player.getname(full=True)}?',
                                f"Maybe you're just unlucky, {player.getname(full=True)}.",
                                f'Better luck next time, {player.getname(full=True)}.',
                                f'You should be more prepared next time, {player.getname(full=True)}.',
                                f"Catch the flag. It's not that hard, {player.getname(full=True)}!",
                            ]
                            player.survived = False
                            (
                                bs.broadcastmessage(
                                    random.choice(message),
                                    color=(0.8, 0.0, 0.8),
                                ),
                            )
                            flag_pos = self.map.get_flag_position(None)
                            pos = (flag_pos[0], flag_pos[1] + 2.5, flag_pos[2])
                            player.actor.handlemessage(bs.StandMessage(pos))
                            bs.timer(
                                0.5,
                                bs.CallStrict(
                                    player.actor.handlemessage,
                                    bs.FreezeMessage(),
                                ),
                            )
                            bs.timer(
                                3.0,
                                bs.CallStrict(
                                    player.actor.handlemessage,
                                    bs.ShouldShatterMessage(),
                                ),
                            )
                        except:
                            pass
                bs.timer(3.5, self.kill_round)
                bs.timer(3.55, self.start_round)
        else:
            return super().handlemessage(msg)
        return None

    def check_end(self):
        # For team mode, check if any team has been completely eliminated
        if isinstance(self.session, bs.DualTeamSession):
            teams_alive = set()
            for player in self.players:
                if player.survived:
                    teams_alive.add(player.team)
            # If not all teams have surviving players, end the game
            if len(teams_alive) < len(self.teams):
                for team in self.teams:
                    if team in teams_alive:
                        team.score += 10
                bs.timer(2.5, self.end_game)
                return

        i = 0
        for player in self.players:
            if player.survived:
                i += 1
        if i <= 1:
            for player in self.players:
                if player.survived:
                    player.team.score += 10
            bs.timer(2.5, self.end_game)

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
