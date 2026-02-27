# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.bomb import Blast
from bascenev1lib.actor.flag import Flag, FlagPickedUpMessage
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class Player(bs.Player['Team']):
    def __init__(self) -> None:
        self.alive: bool = True
        self.tag_on: bool = True
        self.done: bool = False
        self.is_done_pos: bool = False
        self.is_using_hint: bool = False
        self.died_on_done: bool = False
        self.hints_count: int = 0
        self.chances: int = 0
        self.is_using_hint_warn: int = 0
        self.hints: int = 0
        self.colors_order: list = []
        self.last_color_picked: str = ''
        self.sorted_up_count: int = 0
        self.tag_node: bs.Node = None
        self.tag_color: int = (0, 0, 0)


class Team(bs.Team[Player]):
    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class MemoryFlagGame(bs.TeamGameActivity[Player, Team]):
    name = 'Memory Flags'
    description = (
        "Don't be the one doesn't remember the order!\nBy FluffyPal :)"
    )

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[babase.Setting]:
        settings = [
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('N', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('3 Minutes', 180),
                    ('4 Minutes', 240),
                    ('5 Minutes', 300),
                    ('6 Minutes', 360),
                    ('7 Minutes', 420),
                    ('8 Minutes', 480),
                    ('9 Minutes', 540),
                    ('10 Minutes', 600),
                ],
                default=180,
            ),
            bs.IntSetting(
                'Round Time',
                min_value=30,
                max_value=60,
                increment=3,
                default=36,
            ),
            bs.IntChoiceSetting(
                'Flag Position Type',
                choices=[
                    ('Soft Square', 1),
                    ('Circle', 2),
                ],
                default=1,
            ),
            bs.IntChoiceSetting(
                'Chances',
                choices=[
                    ('Instant Death', 1),
                    ('2 Chances', 2),
                    ('3 Chances', 3),
                ],
                default=2,
            ),
            bs.IntChoiceSetting(
                'Hints',
                choices=[
                    ('N', 0),
                    ('1 Hints', 1),
                    ('2 Hints', 2),
                    ('3 Hints', 3),
                    ('4 Hints', 4),
                    ('5 Hints', 5),
                    ('6 Hints', 6),
                ],
                default=3,
            ),
            bs.BoolSetting('Randomize Colors Each Round', default=True),
            bs.BoolSetting('One Hint Each Round', default=False),
            bs.BoolSetting('Reset Chances Each Round', default=True),
            bs.BoolSetting('Peaceful', default=True),
            bs.BoolSetting('Create Invincible Wall', default=False),
            bs.BoolSetting('Speedy', default=True),
            bs.BoolSetting('Reset Player Position', default=False),
            bs.BoolSetting('Flashing Lights', default=False),
            #           bs.BoolSetting('Credit :)', default=True),
        ]
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return [
            'Courtyard',
        ]

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.time = int(settings['Round Time'])
        #       self.credit_text = bool(settings['Credit :)'])
        self.is_speedy = bool(settings['Speedy'])
        self._time_limit = float(settings['Time Limit'])
        self.is_peaceful = bool(settings['Peaceful'])
        self._is_flashing_lights = bool(settings['Flashing Lights'])
        self.reset_player_pos = bool(settings['Reset Player Position'])
        self.flag_pos_type = int(settings['Flag Position Type'])
        self.max_hint_setting = int(settings['Hints'])
        self.one_hint_each_round = bool(settings['One Hint Each Round'])
        self.reset_chance_each_round = bool(
            settings['Reset Chances Each Round']
        )
        self.randomize_colors_each_round = bool(
            settings['Randomize Colors Each Round']
        )
        self._use_boundaries = bool(settings['Create Invincible Wall'])
        self.max_chance_setting = int(settings['Chances'])
        self.get_s = settings

        self._scoreboard = Scoreboard()

        self._textRound = bs.newnode(
            'text',
            attrs={
                'text': '',
                'position': (0, 100),
                'scale': 1,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (1.0, 0.0, 1.0),
                'opacity': 1,
                'v_attach': 'bottom',
                'h_attach': 'center',
                'h_align': 'center',
                'v_align': 'center',
            },
        )

        self.r_timer = bs.newnode(
            'text',
            attrs={
                'h_align': 'center',
                'color': (0.7, 0.88, 1.0),
                'shadow': 1.0,
                'flatness': 1.0,
                'position': (0, 3.65, -6),
                'scale': 0.01555,
                'vr_depth': 0,
                'in_world': True,
                'text': '',
            },
        )

        self.guide_color = bs.newnode(
            'text',
            attrs={
                'v_attach': 'top',
                'h_attach': 'center',
                'h_align': 'center',
                'color': (0.7, 0.88, 1.0),
                'shadow': 1.0,
                'flatness': 1.0,
                'position': (0, -310),
                'scale': 1.5,
                'text': '',
            },
        )

        self.slow_motion = False
        self.is_first_round = True
        self.game_ended = False

        self.default_music = bs.MusicType.RACE

        self.center_pos = (0, 2.35, -2)

        self.whos_alive_in_end = []

        """Flags"""
        self.red_flag: Flag | None = None
        self.green_flag: Flag | None = None
        self.blue_flag: Flag | None = None
        self.yellow_flag: Flag | None = None
        self.purple_flag: Flag | None = None
        self.cyan_flag: Flag | None = None
        self.white_flag: Flag | None = None
        self.orange_flag: Flag | None = None
        self.hint_flag: Flag | None = None
        self.hint_flag2: Flag | None = None

        Flag.tag_node = None

        """Colors"""
        self.redcolor = (1, 0, 0)
        self.greencolor = (0, 1, 0)
        self.bluecolor = (0, 0, 1)
        self.yellowcolor = (1, 1, 0)
        self.purplecolor = (0.7, 0.45, 1)
        self.cyancolor = (0.2, 1, 1)
        self.whitecolor = (1, 1, 1)
        self.orangecolor = (1, 0.5, 0)

        self.colors = [
            (1.2, 0.2, 0.2),  # Merah
            (1.3, 1.0, 0.5),  # Oranye
            (1.5, 1.3, 0.5),  # Kuning
            (1.0, 1.5, 0.5),  # Hijau Muda
            (0.5, 1.3, 0.5),  # Hijau
            (0.5, 1.3, 1.5),  # Toska
            (0.7, 1.0, 1.5),  # Biru Muda
            (0.9, 0.5, 1.5),  # Biru
            (1.2, 0.7, 1.3),  # Violet
            (1.5, 0.9, 1.1),  # Ungu
            (1.5, 0.5, 1.5),  # Magenta
            (1.25, 0.6, 0.8),  # Pink
        ]

        self.on_done_message = [
            'Sigma',
            'GigaChad',
            'Pro',
            'Gg',
            'Noice',
            'W',
            'Skilled',
            'UwU',
            'Ehe',
            '( ͡° ͜ʖ ͡°)',
        ]

        self.on_dead_message = 'DEAD T^T'

    def get_instance_description(self) -> str | Sequence:
        return 'Sort Many Colors As Much As You Can! By FluffyPal :)'

    def get_instance_description_short(self) -> str | Sequence:
        return 'Sort Many Colors As Much As You Can!'

    def add_wall(self):
        # FIXME: Chop this into vr and non-vr chunks.
        shared = SharedObjects.get()
        pwm = bs.Material()
        cwwm = bs.Material()
        pwm.add_actions(actions=('modify_part_collision', 'friction', 0.0))
        # anything that needs to hit the wall should apply this.

        pwm.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=('modify_part_collision', 'collide', True),
        )
        cmesh = bs.getcollisionmesh('courtyardPlayerWall')
        self.player_wall = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': cmesh,
                'affect_bg_dynamics': False,
                'materials': [pwm],
            },
        )
        print('Courtyard Wall Created')

    def add_hint_flag_tag(self, flag: Flag, tag_text='Hint'):
        # Create a text node to display above the flag
        def add_flag_tag():
            flag.tag_node = tag_node = bs.newnode(
                'text',
                attrs={
                    'text': tag_text,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': (1, 1, 0),
                    'scale': 0.015,
                    'h_align': 'center',
                },
            )

            bs.animate_array(
                tag_node,
                'color',
                3,
                {
                    0: (1.5, 0.85, 1),
                    1.5: random.choice(self.colors),
                    3: random.choice(self.colors),
                    4.5: random.choice(self.colors),
                    6: random.choice(self.colors),
                    7.5: random.choice(self.colors),
                    9: random.choice(self.colors),
                    10.5: random.choice(self.colors),
                    12: random.choice(self.colors),
                    13.5: random.choice(self.colors),
                    15: random.choice(self.colors),
                    16.5: random.choice(self.colors),
                    18: (1.5, 0.85, 1),
                },
                loop=True,
            )

            # Link the text node to the flag's position
            flag.node.connectattr('position', tag_node, 'position')

            # Position the tag slightly above the flag
            tag_node.position = (
                flag.node.position[0],
                flag.node.position[1] + 1,
                flag.node.position[2],
            )

        if not flag.tag_node:
            add_flag_tag()
        else:
            flag.tag_node.delete()
            add_flag_tag()

    def update_tags(self):
        if self.game_ended:
            return
        for player in self.not_done_players:
            if player not in self.not_done_players:
                player.tag_on = False
                player.tag_node = None
            else:

                def add_tag():
                    if player.actor.node:
                        spaz = player.actor
                        player_tag = bs.newnode(
                            'math',
                            owner=spaz.node,
                            attrs={
                                'input1': (0, 0.85, -0.2),
                                'operation': 'add',
                            },
                        )
                        spaz.node.connectattr(
                            'torso_position', player_tag, 'input2'
                        )

                        player.tag_node = cnode = bs.newnode(
                            'text',
                            owner=spaz.node,
                            attrs={
                                'text': f'\n\n\n\n\nSorted: {str(player.sorted_up_count)}\n{player.last_color_picked}',
                                'in_world': True,
                                'shadow': 0.5,
                                'color': player.tag_color,
                                'flatness': 1.0,
                                'scale': 0.0135,
                                'h_align': 'center',
                            },
                        )
                        player_tag.connectattr('output', cnode, 'position')
                        player.tag_on = True

                if player.tag_node:
                    player.tag_node.delete()
                    add_tag()
                else:
                    add_tag()

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            player_name = player.getname()
            bs.broadcastmessage(
                babase.Lstr(
                    resource='playerDelayedJoinText',
                    subs=[('${PLAYER}', player.getname(full=True))],
                    color=(0, 1, 0),
                    transient=True,
                )
            )
            player.alive = None
            player.done = None
            player.is_done_pos = None
            player.tag_on = None

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        pname = player.getname()
        # Ensure players removed from any list
        if player in self.not_done_players:
            self.not_done_players.remove(player)
        if player in self.done_players:
            self.done_players.remove(player)
        if player in self.whos_alive_in_end:
            self.whos_alive_in_end.remove(player)

        if player.done and player.alive:
            bs.broadcastmessage(f'{pname} left while done')

        if len(self.not_done_players) <= 0:
            if (
                not self.game_ended
                and player.alive
                and not (player.done or player.done is None)
            ):
                bs.broadcastmessage(
                    'No one in the round, Next Round...', color=(1.5, 0.85, 1)
                )
                self.loop_timer = None
                self.is_first_round = False
                self.kill_flags()
                bs.timer(1.5, self.make_round)

        # Set Players Condition To None
        player.alive = None
        player.tag_on = None
        player.done = None
        player.is_done_pos = None

        player.colors_order = []

        bs.timer(0.5, self.checkEnd)

    """Refresh Player Pos For New Round"""

    def refresh_player(self, player: Player) -> bs.Actor | None:
        def player_is_immortal():
            if player.actor and player.actor.node and not player.done:
                player.actor.node.invincible = (
                    self.is_peaceful
                )  # Berikan keabadian jika perlu

        if not player.alive or self.game_ended:
            return None  # Jangan lakukan apapun jika player sudah mati atau game berakhir

        # Jika mode peaceful, buat player tidak bisa mati sementara
        if self.is_peaceful:
            bs.timer(1, player_is_immortal)

        def spawn_player():
            # Spawn player di posisi awal
            self.spaz = self.spawn_player_spaz(player)
            player.actor.handlemessage(bs.StandMessage(self.center_pos))

            # Jika mode peaceful, buat player kebal
            if self.is_peaceful:
                bs.timer(1, player_is_immortal)

            # Berikan kontrol player
            player.actor.node.hockey = self.is_speedy
            player.actor.connect_controls_to_player(
                enable_punch=True,
                enable_bomb=False,
                enable_pickup=True,
                enable_run=True,
            )
            return self.spaz

        # Jika ini ronde pertama dan player belum selesai
        if self.is_first_round and not player.done:
            return spawn_player()

        # Jika player sudah selesai (done) dan masih hidup (actor != None), teleportasi ke posisi tengah dan berikan kontrol kembali
        if player.is_done_pos and player.actor and not player.done:
            player.actor.handlemessage(bs.StandMessage(self.center_pos))
            player.actor.node.hockey = self.is_speedy
            player.actor.node.invincible = self.is_peaceful
            player.actor.connect_controls_to_player(
                enable_punch=True,
                enable_pickup=True,
                enable_bomb=False,
                enable_run=True,
            )
            player.is_done_pos = False

        # Jika player belum selesai (done == False) di ronde selanjutnya dan player tidak memiliki actor (mati)
        elif not player.done and player.alive:
            return spawn_player()

    """On game begin"""

    def on_begin(self) -> None:
        super().on_begin()

        self.current_colors_list = []
        self.done_players = []
        self.not_done_players = []
        self.colors_order = []

        self.setup_standard_time_limit(self._time_limit)

        """Make a lovely Credit :)"""
        self.credit = bs.newnode(
            'text',
            attrs={
                'text': 'Created By FluffyPal',
                'scale': 0.7,
                'position': (0, 60),
                'shadow': 1,
                'flatness': 1.2,
                'color': (1.5, 0.85, 1),
                'h_align': 'center',
                'v_attach': 'bottom',
            },
        )
        bs.animate_array(
            self.credit,
            'color',
            3,
            {
                0: (1.5, 0.85, 1),
                1.5: self.colors[1],
                3: self.colors[2],
                4.5: self.colors[3],
                6: self.colors[4],
                7.5: self.colors[5],
                9: self.colors[6],
                10.5: self.colors[7],
                12: self.colors[8],
                13.5: self.colors[9],
                15: self.colors[10],
                16.5: self.colors[11],
                18: (1.5, 0.85, 1),
            },
            loop=True,
        )

        self.roundNum = 0
        self._textRound.text = 'Round/Colors: ' + str(self.roundNum) + ''

        for player in self.players:
            self.not_done_players.append(player)
            self.whos_alive_in_end.append(player)
            player.tag_color = player.team.color
            player.hints = self.max_hint_setting
            player.chances = self.max_chance_setting

        if self._use_boundaries:
            self.add_wall()
        bs.timer(3, self.make_round)
        bs.timer(2, self.checkEnd)

        #     bs.chatmessage('This Game Using Scoreboard Now Instead Using Last Living Players.')
        bs.chatmessage('Get high scores by sorting quickly!')

    def set_flag_pos(self):
        if self.flag_pos_type == 2:
            self.flag_pos1 = (-2.5, 2.75, -2)  # Red
            self.flag_pos2 = (0.0, 2.75, -4.5)  # Green
            self.flag_pos3 = (2.5, 2.75, -2)  # Blue
            self.flag_pos4 = (0.0, 2.75, 0.5)  # Yellow
            self.flag_pos5 = (-1.5, 2.75, -3.5)  # Purple
            self.flag_pos6 = (1.5, 2.75, -3.5)  # Cyan
            self.flag_pos7 = (1.5, 2.75, -0.5)  # White
            self.flag_pos8 = (-1.5, 2.75, -0.5)  # Orange
        else:
            self.flag_pos1 = (-2.5, 2.75, -0.75)  # Red
            self.flag_pos2 = (-2.5, 2.75, -3.25)  # Green
            self.flag_pos3 = (2.5, 2.75, -3.25)  # Blue
            self.flag_pos4 = (2.5, 2.75, -0.75)  # Yellow
            self.flag_pos5 = (-1, 2.75, -4.5)  # Purple
            self.flag_pos6 = (1, 2.75, -4.5)  # Cyan
            self.flag_pos7 = (1, 2.75, 0.5)  # White
            self.flag_pos8 = (-1, 2.75, 0.5)  # Orange
        self.flag_pos_hint = (-3.7675, 2.75, -5.85)
        self.flag_pos_hint2 = (3.7675, 2.75, -5.85)

    def spawn_flags(self):
        if self.roundNum <= 4:
            self.red_flag = Flag(position=self.flag_pos1, color=self.redcolor)
            self.red_flag.name = 'red_flag'
            self.green_flag = Flag(
                position=self.flag_pos2, color=self.greencolor
            )
            self.green_flag.name = 'green_flag'
            self.blue_flag = Flag(position=self.flag_pos3, color=self.bluecolor)
            self.blue_flag.name = 'blue_flag'
            self.yellow_flag = Flag(
                position=self.flag_pos4, color=self.yellowcolor
            )
            self.yellow_flag.name = 'yellow_flag'
        elif self.roundNum <= 6:
            self.red_flag = Flag(position=self.flag_pos1, color=self.redcolor)
            self.red_flag.name = 'red_flag'
            self.green_flag = Flag(
                position=self.flag_pos2, color=self.greencolor
            )
            self.green_flag.name = 'green_flag'
            self.blue_flag = Flag(position=self.flag_pos3, color=self.bluecolor)
            self.blue_flag.name = 'blue_flag'
            self.yellow_flag = Flag(
                position=self.flag_pos4, color=self.yellowcolor
            )
            self.yellow_flag.name = 'yellow_flag'
            self.purple_flag = Flag(
                position=self.flag_pos5, color=self.purplecolor
            )
            self.purple_flag.name = 'purple_flag'
            self.cyan_flag = Flag(position=self.flag_pos6, color=self.cyancolor)
            self.cyan_flag.name = 'cyan_flag'
        elif self.roundNum > 6:
            self.red_flag = Flag(position=self.flag_pos1, color=self.redcolor)
            self.red_flag.name = 'red_flag'
            self.green_flag = Flag(
                position=self.flag_pos2, color=self.greencolor
            )
            self.green_flag.name = 'green_flag'
            self.blue_flag = Flag(position=self.flag_pos3, color=self.bluecolor)
            self.blue_flag.name = 'blue_flag'
            self.yellow_flag = Flag(
                position=self.flag_pos4, color=self.yellowcolor
            )
            self.yellow_flag.name = 'yellow_flag'
            self.purple_flag = Flag(
                position=self.flag_pos5, color=self.purplecolor
            )
            self.purple_flag.name = 'purple_flag'
            self.cyan_flag = Flag(position=self.flag_pos6, color=self.cyancolor)
            self.cyan_flag.name = 'cyan_flag'
            self.white_flag = Flag(
                position=self.flag_pos7, color=self.whitecolor
            )
            self.white_flag.name = 'white_flag'
            self.orange_flag = Flag(
                position=self.flag_pos8, color=self.orangecolor
            )
            self.orange_flag.name = 'orange_flag'
        if not self.max_hint_setting == 0 and not self.is_first_round:
            self.hint_flag = Flag(
                position=self.flag_pos_hint, color=random.choice(self.colors)
            )
            self.hint_flag.name = 'hint'
            self.add_hint_flag_tag(self.hint_flag)
            self.hint_flag2 = Flag(
                position=self.flag_pos_hint2, color=random.choice(self.colors)
            )
            self.hint_flag2.name = 'hint'
            self.add_hint_flag_tag(self.hint_flag2)

    def spawn_all_flags(self):
        self.red_flag = Flag(position=self.flag_pos1, color=self.redcolor)
        self.red_flag.name = 'red_flag'
        self.green_flag = Flag(position=self.flag_pos2, color=self.greencolor)
        self.green_flag.name = 'green_flag'
        self.blue_flag = Flag(position=self.flag_pos3, color=self.bluecolor)
        self.blue_flag.name = 'blue_flag'
        self.yellow_flag = Flag(position=self.flag_pos4, color=self.yellowcolor)
        self.yellow_flag.name = 'yellow_flag'
        self.purple_flag = Flag(position=self.flag_pos5, color=self.purplecolor)
        self.purple_flag.name = 'purple_flag'
        self.cyan_flag = Flag(position=self.flag_pos6, color=self.cyancolor)
        self.cyan_flag.name = 'cyan_flag'
        self.white_flag = Flag(position=self.flag_pos7, color=self.whitecolor)
        self.white_flag.name = 'white_flag'
        self.orange_flag = Flag(position=self.flag_pos8, color=self.orangecolor)
        self.orange_flag.name = 'orange_flag'
        if not self.max_hint_setting == 0 and not self.is_first_round:
            self.hint_flag = Flag(
                position=self.flag_pos_hint, color=random.choice(self.colors)
            )
            self.hint_flag.name = 'hint'
            self.add_hint_flag_tag(self.hint_flag)
            self.hint_flag2 = Flag(
                position=self.flag_pos_hint2, color=random.choice(self.colors)
            )
            self.hint_flag2.name = 'hint'
            self.add_hint_flag_tag(self.hint_flag2)

    def change_hint_flag_color(self):
        if self.hint_flag and self.hint_flag2:
            if self.hint_flag.node and self.hint_flag2.node:
                self.hint_flag.node.color = random.choice(self.colors)
                self.hint_flag2.node.color = random.choice(self.colors)

    """Make a lovely round"""

    def make_round(self):
        self.roundNum += 1
        self.r_timer.color = (0.7, 0.88, 1.0)
        self.r_timer.position = (0, 3.65, -6)
        self._textRound.text = 'Round/Colors: ' + str(self.roundNum) + ''
        self.guide_color.text = '  '
        self.loop_timer = None

        if not self.game_ended:
            self.r_timer.text = ''
            self.r_timer.text = 'Round ' + str(self.roundNum) + ''

        for player in (
            self.not_done_players if self.is_first_round else self.done_players
        ):
            player.alive = True
            player.done = False
            player.is_using_hint = False
            player.is_using_hint_warn = 0
            player.last_color_picked = ''
            player.sorted_up_count = 0
            player.died_on_done = False
            if self.is_first_round:
                player.is_done_pos = False

            def player_done_pos_is_false():
                player.is_done_pos = False

            self.tag_text = f'\n\n\n\n\nSorted: {str(player.sorted_up_count)}\n{player.last_color_picked}'
            if self.reset_chance_each_round:
                player.chances = self.max_chance_setting

            if self.roundNum <= 3:
                delay = 1.5
                bs.timer(delay, babase.CallStrict(self.refresh_player, player))
                bs.timer(delay, self.start_choosing_timer)
                bs.timer(delay + 0.05, self.update_tags)
            else:
                spawn_time = 0.5 * len(self.current_colors_list) + 1
                bs.timer(
                    spawn_time, babase.CallStrict(self.refresh_player, player)
                )
                bs.timer(spawn_time + 0.05, self.update_tags)
                bs.timer(spawn_time + 0.05, self.start_choosing_timer)
                bs.timer(spawn_time + 0.1, player_done_pos_is_false)

            if not self.is_first_round:
                self.not_done_players.append(player)

        #     if not self.is_first_round and not self.max_hint_setting == 0:
        #        self.hint_flag.tag_node.text = ''
        #       self.hint_flag2.tag_node.text = ''

        self.done_players = []

        # Reset players' flag order tracking
        for player in self.not_done_players:
            player.colors_order = []

        self.set_flag_pos()

        self.spawn_flags()
        #       self.spawn_all_flags() # For testing

        bs.timer(1, self.master_colors_order)
        bs.timer(2, self.checkEnd)

    """Colors Order"""

    def master_colors_order(self):
        # Tentukan warna yang tersedia berdasarkan ronde
        if self.roundNum < 5:
            self.available_colors = ['RED', 'GREEN', 'BLUE', 'YELLOW']
        elif self.roundNum <= 6:
            self.available_colors = [
                'PURPLE',
                'CYAN',
                'PURPLE',
                'CYAN',
                'RED',
                'GREEN',
                'BLUE',
                'YELLOW',
            ]
        else:
            self.available_colors = [
                'WHITE',
                'ORANGE',
                'WHITE',
                'ORANGE',
                'PURPLE',
                'CYAN',
                'RED',
                'GREEN',
                'BLUE',
                'YELLOW',
            ]

        # Jika randomize_colors_each_round aktif, ambil warna acak sebanyak jumlah ronde
        if self.randomize_colors_each_round:
            num_colors = min(self.roundNum, len(self.available_colors))
            self.current_colors_list = random.sample(
                self.available_colors, num_colors
            )
        else:
            # Jika tidak, tambahkan satu warna acak ke daftar seperti sebelumnya
            self.current_colors_list.append(
                random.choice(self.available_colors)
            )

        # Fungsi untuk menampilkan pesan warna
        def display_color_message(i: int):
            if self.game_ended:
                return
            color_name = self.current_colors_list[i]
            if color_name == 'RED':
                color = self.redcolor
            elif color_name == 'GREEN':
                color = self.greencolor
            elif color_name == 'BLUE':
                color = self.bluecolor
            elif color_name == 'YELLOW':
                color = self.yellowcolor
            elif color_name == 'PURPLE':
                color = self.purplecolor
            elif color_name == 'CYAN':
                color = self.cyancolor
            elif color_name == 'WHITE':
                color = self.whitecolor
            elif color_name == 'ORANGE':
                color = self.orangecolor

            try:
                self.guide_color.color = color
                bs.animate(
                    self.guide_color,
                    'opacity',
                    {
                        0: 1,
                        1.25: 0,
                    },
                )
                if self._is_flashing_lights:
                    bs.animate_array(
                        bs.getactivity().globalsnode,
                        'tint',
                        3,
                        {0: color, 0.5: (1.2, 1.2, 1.2)},
                    )
                bs.getsound('pop01').play(1.5)
                bs.broadcastmessage(color_name, color)
                """
                PopupText(
                    position=self.center_pos,
                    text=f"{color_name}",
                    color=color, scale=2).autoretain()
                """
            except Exception:
                pass

        # Tampilkan setiap warna yang ada di current_colors_list
        for i in range(len(self.current_colors_list)):
            if not self.game_ended:
                bs.timer(
                    0.8 * i if self.roundNum <= 3 else 0.5 * i,
                    babase.CallStrict(display_color_message, i),
                )

    def check_respawn(self, player):
        if player.alive:
            pos = self.center_pos
            self.spawn_player(player)
            bs.timer(2, self.checkEnd)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)

            # Jika player sudah selesai tetapi masih alive, tandai bahwa mereka mati setelah done
            if player.alive and player.done:
                player.died_on_done = True

            # Jika player masih alive dan belum selesai (belum done), refresh player
            if player.alive and not player.done:
                bs.timer(0.25, babase.CallStrict(self.refresh_player, player))

            # Pengecekan akhir permainan dan pembaruan status tag
            bs.timer(0.5, self.checkEnd)
            bs.timer(0.5, self.update_tags)

        if isinstance(msg, FlagPickedUpMessage):
            player = msg.node.getdelegate(PlayerSpaz, True).getplayer(
                Player, True
            )
            xpos = [-3, -2.5, -2, -1.5, -1, -0.5, 0, 3, 2.5, 2, 1.5, 1, 0.5]
            zpos = [-9, -8.5, -8, -7.7525]
            self.done_pos = (random.choice(xpos), 3.75, random.choice(zpos))

            #           player.sorted_up_count += 1 # It should be added if player sort it correctly

            # Define flag properties
            flag_properties = {
                'red_flag': {
                    'color': 'RED',
                    'tag_color': self.redcolor,
                    'position': self.flag_pos1,
                },
                'green_flag': {
                    'color': 'GREEN',
                    'tag_color': self.greencolor,
                    'position': self.flag_pos2,
                },
                'blue_flag': {
                    'color': 'BLUE',
                    'tag_color': self.bluecolor,
                    'position': self.flag_pos3,
                },
                'yellow_flag': {
                    'color': 'YELLOW',
                    'tag_color': self.yellowcolor,
                    'position': self.flag_pos4,
                },
                'purple_flag': {
                    'color': 'PURPLE',
                    'tag_color': self.purplecolor,
                    'position': self.flag_pos5,
                },
                'cyan_flag': {
                    'color': 'CYAN',
                    'tag_color': self.cyancolor,
                    'position': self.flag_pos6,
                },
                'white_flag': {
                    'color': 'WHITE',
                    'tag_color': self.whitecolor,
                    'position': self.flag_pos7,
                },
                'orange_flag': {
                    'color': 'ORANGE',
                    'tag_color': self.orangecolor,
                    'position': self.flag_pos8,
                },
                'hint': {
                    'color': player.last_color_picked,
                    'tag_color': random.choice(self.colors),
                },
            }

            flag_name = msg.flag.name
            if flag_name in flag_properties:
                color_data = flag_properties[flag_name]
                color = color_data['color']
                player.last_color_picked = color
                player.tag_color = color_data['tag_color']

                if flag_name != 'hint':
                    setattr(
                        self,
                        f'{color.lower()}_flag',
                        Flag(
                            position=color_data['position'],
                            color=color_data['tag_color'],
                        ),
                    )
                    getattr(self, f'{color.lower()}_flag').name = flag_name
                    if color and not player.done:
                        self.check_color_order(player, color)
                else:
                    self.handle_hint_flag(player)
                    color = None

    def handle_hint_flag(self, player):
        self.hint_flag.tag_node.delete()
        self.hint_flag2.tag_node.delete()
        self.hint_flag = Flag(
            position=self.flag_pos_hint, color=random.choice(self.colors)
        )
        self.hint_flag2 = Flag(
            position=self.flag_pos_hint2, color=random.choice(self.colors)
        )
        self.hint_flag.name = 'hint'
        self.hint_flag2.name = 'hint'
        self.add_hint_flag_tag(self.hint_flag)
        self.add_hint_flag_tag(self.hint_flag2)

        def check_flag_hint():
            if player.hints_count < self.max_hint_setting:
                color_hint = self.current_colors_list[len(player.colors_order)]
                player.hints_count += 1
                player.hints -= 1
                hint_message = (
                    f'{player.getname()}, Your Next Color Is > {color_hint} < You Have [{str(player.hints)}] Hints Left'
                    if player.hints > 0
                    else f'{player.getname()}, Your Next Color Is > {color_hint} < You Have No Hints Now'
                )
                bs.chatmessage(hint_message)
                if not player.last_color_picked == '':
                    player.tag_node.text = f'\n\n\n\n\nSorted:{str(player.sorted_up_count)}\n{player.last_color_picked}\nHint: {color_hint}'
                else:
                    player.tag_node.text = f'\n\n\n\n\nSorted:{str(player.sorted_up_count)}\nHint: {color_hint}'
            else:
                player.is_using_hint_warn += 1
                self.display_hint_warning(player)

        if not player.done:
            if not player.is_using_hint:
                player.is_using_hint = True
                check_flag_hint()
            elif self.one_hint_each_round:
                player.is_using_hint_warn += 1
                self.display_hint_warning(player)
            else:
                check_flag_hint()

    def display_hint_warning(self, player):
        # Check if the player has exceeded the hint usage warning limit
        warns = player.is_using_hint_warn

        def handle_spam():
            if warns <= 4:
                warning_message = f'{player.getname()}, Stop...'
                bs.broadcastmessage(warning_message, color=(1, 0.5, 0))
            elif warns == 5 or warns == 6:
                warning_message = f"{player.getname()}, Don't.. Or Else"
                bs.broadcastmessage(warning_message, color=(1, 0.5, 0))
            else:
                msg = f'{player.getname()} Is Spamming'
                self.handle_wrong_order(player, msg)

        if not self.one_hint_each_round:
            if warns <= 2:
                warning_message = (
                    f"{player.getname()}, You Don't Have Any Hints"
                )
                bs.broadcastmessage(warning_message, color=(1, 0.4, 0.7))

                # Optional: You could also deduct points or apply other penalties here if needed
                # Example: self.stats.player_scored(player, -10, big_message=False)
            else:
                handle_spam()
        else:
            if warns <= 2:
                bs.broadcastmessage('You can only use it once each round')
            else:
                handle_spam()

    def check_color_order(self, player, color):
        try:
            expected_color = self.current_colors_list[len(player.colors_order)]

            # If the color order are correct
            if color == expected_color:
                if not self.game_ended:
                    player.colors_order.append(color)
                    player.sorted_up_count += 1
                    if self.time > 2:
                        score = round(self.time / 2)
                        player.team.score += score  # Add team score based by timer but divided by 2

                        if not len(player.colors_order) == len(
                            self.current_colors_list
                        ):
                            PopupText(
                                position=player.actor.node.position,
                                text=f'+{score}',
                                color=player.tag_color,
                                scale=1,
                            ).autoretain()
                    for team in self.teams:
                        self._scoreboard.set_team_value(team, team.score)

                if len(player.colors_order) == len(self.current_colors_list):
                    self.handle_successful_order(player)
            else:
                if self.max_chance_setting == 1:
                    msg = f'{player.getname()} picked the wrong flag order! -> [{color}]'
                    self.handle_wrong_order(player, msg)
                else:
                    player.chances -= 1

                    # Give them a chance :) and keep show their hints if they're using hints
                    if not any(
                        word in player.tag_node.text
                        for word in ['Hint', 'hint']
                    ):
                        player.last_color_picked = f'Wrong! -> {color}'
                    else:
                        player.last_color_picked = f'Wrong! -> {color}\nHint: {self.current_colors_list[len(player.colors_order)]}'

                    if player.chances > 1:
                        PopupText(
                            position=player.actor.node.position,
                            text=f'Wrong Flag, {player.getname()}!\nYou Have [{str(player.chances)}] Chances Left',
                            color=player.tag_color,
                            scale=1.5,
                        ).autoretain()
                    elif player.chances == 1:
                        PopupText(
                            position=player.actor.node.position,
                            text=f'Wrong Flag, {player.getname()}!\n[{str(player.chances)}] Last Chance!',
                            color=self.redcolor,
                            scale=1.5,
                        ).autoretain()
                    elif player.chances == 0:
                        msg = f'{player.getname()} picked the wrong flag! -> [{color}]'
                        self.handle_wrong_order(player, msg)

            if (
                not len(player.colors_order) == len(self.current_colors_list)
                and not player.chances == 0
            ):
                player.tag_node.text = f'\n\n\n\n\nSorted:{str(player.sorted_up_count)}\n{player.last_color_picked}'
                player.tag_node.color = player.tag_color

        except Exception as e:
            bs.chatmessage(str(e))

    def handle_successful_order(self, player):
        if not self.game_ended:
            self.stats.player_scored(player, self.time + 1, big_message=False)
            player.team.score += self.time + 1  # Add team score based by timer
            for team in self.teams:
                self._scoreboard.set_team_value(team, team.score)
            self.done_players.append(player)
            self.not_done_players.remove(player)

            player.is_done_pos = True
            player.actor.node.invincible = False
            player.actor.handlemessage(bs.StandMessage(self.done_pos))
            player.tag_node.text = '\n\n\n' + random.choice(
                self.on_done_message
            )
            player.tag_node.color = random.choice(self.colors)
            player.actor.disconnect_controls_from_player()

            if self.time > 20:
                timer_decrease = 4
                self.time -= timer_decrease
            elif self.time > 10:
                timer_decrease = 2
                self.time -= timer_decrease

            if len(self.not_done_players) > 0:
                if self.time > 10:
                    self.time += 1
                    self.decrease()
                    bs.animate_array(
                        self.r_timer,
                        'color',
                        3,
                        {
                            0: self.orangecolor,
                            0.6: (0.7, 0.88, 1.0),
                        },
                    )
            else:
                self.loop_timer = None

            player.done = True
            player.tag_color = player.team.color
            bs.getsound('dingSmallHigh').play(2)

            # Make round
            if len(self.not_done_players) <= 0:
                self.loop_timer = None
                self.is_first_round = False
                self.kill_flags()
                bs.timer(1, self.checkEnd)
                bs.timer(2, self.make_round)

    def handle_wrong_order(self, player, msg):
        try:
            player.alive = False
            player.done = None
            player.actor.node.invincible = False
            self.not_done_players.remove(player)
            self.whos_alive_in_end.remove(player)
            PopupText(
                position=player.actor.node.position,
                text=msg,
                color=self.redcolor,
                scale=1.5,
            ).autoretain()
            player.actor.handlemessage(bs.DieMessage())
            player.actor.handlemessage(bs.ShouldShatterMessage())
            player.tag_node.text = self.on_dead_message
            player.tag_node.color = (1.5, 0.85, 1)
            bs.getactivity().globalsnode.slow_motion = True
            bs.timer(0.3, self.slow_motion_death)
            bs.animate_array(
                self.r_timer,
                'color',
                3,
                {0: self.redcolor, 0.6: (0.7, 0.88, 1.0)},
            )
            bs.animate_array(
                bs.getactivity().globalsnode,
                'tint',
                3,
                {0: (1.2, 0.6, 0.6), 1.25: (1.2, 1.2, 1.2)},
            )
            explosion_sounds = [
                'explosion01',
                'explosion02',
                'explosion03',
                'explosion04',
                'explosion05',
            ]
            bs.getsound(random.choice(explosion_sounds)).play(2)
            Blast(position=player.position, blast_radius=1.5)
            bs.timer(1, babase.CallStrict(self.checkEnd))
            if len(self.not_done_players) <= 0:
                if not self.game_ended:
                    bs.broadcastmessage(
                        f'{player.getname()} Got it wrong, Next Round...',
                        color=(1.5, 0.85, 1),
                    )
                    self.loop_timer = None
                    self.is_first_round = False
                    self.kill_flags()
                    bs.timer(1.5, self.make_round)
            if self.time > 20:
                timer_decrease = 4
                self.time -= timer_decrease
            elif self.time > 10:
                timer_decrease = 2
                self.time -= timer_decrease

            if len(self.not_done_players) > 0:
                if self.time > 10:
                    self.time += 1
                    self.decrease()
                    bs.animate_array(
                        self.r_timer,
                        'color',
                        3,
                        {
                            0: self.orangecolor,
                            0.6: (0.7, 0.88, 1.0),
                        },
                    )
        except Exception as e:
            bs.chatmessage(f'Error In Handling Wrong Order: ({str(e)})')
            try:
                player.alive = False
                player.done = None
            except:
                pass

    def checkEnd(self) -> None:
        alive_players = [
            player for player in self.whos_alive_in_end if player.alive
        ]

        # Check if all players are dead
        if len(alive_players) == 0:
            self.end_game()
            self.r_timer.text = 'Game Ends'
            self.r_timer.position = (0, -300)
            self.r_timer.color = (1, 0.35, 0.5)
            return

        # Check if there is only one player left
        if len(alive_players) == 1:
            last_player_team = alive_players[0].team
            other_teams = [
                team for team in self.teams if team is not last_player_team
            ]

            # Check if player in the team have HIGHER Score than other team
            if all(last_player_team.score > team.score for team in other_teams):
                self.end_game()
                self.r_timer.text = 'Game Ends'
                self.r_timer.position = (0, -300)
                self.r_timer.color = (1, 0.35, 0.5)
                return

        # Check if all Players in A Team DIED
        for team in self.teams:
            team_players = [
                player
                for player in self.whos_alive_in_end
                if player.team is team
            ]
            if all(not player.alive for player in team_players):
                other_teams = [t for t in self.teams if t is not team]
                leading_team = max(other_teams, key=lambda t: t.score)

                # Check whether the opposing Team that is still ALIVE has a HIGHER Score Than the Team that is DEAD
                if leading_team.score > team.score:
                    self.end_game()
                    self.r_timer.text = 'Game Ends'
                    self.r_timer.color = (1, 0.35, 0.5)
                    return

    def kill_flags(self) -> None:
        if self.red_flag:
            self.red_flag.node.delete()
        if self.green_flag:
            self.green_flag.node.delete()
        if self.blue_flag:
            self.blue_flag.node.delete()
        if self.yellow_flag:
            self.yellow_flag.node.delete()
        if self.purple_flag:
            self.purple_flag.node.delete()
        if self.cyan_flag:
            self.cyan_flag.node.delete()
        if self.white_flag:
            self.white_flag.node.delete()
        if self.orange_flag:
            self.orange_flag.node.delete()
        if self.hint_flag:
            self.hint_flag.tag_node.delete()
            self.hint_flag.node.delete()
        if self.hint_flag2:
            self.hint_flag2.tag_node.delete()
            self.hint_flag2.node.delete()
        self.guide_color.position = (0, -220)

    def end_game(self) -> None:
        results = bs.GameResults()
        for player in self.whos_alive_in_end:
            if not self.game_ended:
                self.stats.player_scored(player, 100, big_message=False)
                if player.is_done_pos and player.actor.node:
                    player.actor.handlemessage(bs.StandMessage(self.center_pos))
                    player.actor.connect_controls_to_player()
                    player.actor.node.invincible = self.is_peaceful
                    player.is_done_pos = None

        self.game_ended = True
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
        self.r_timer.text = 'Game Ends'
        self.r_timer.position = (0, 3.5, -6)

    #       self.r_timer.scale = 1.2

    def slow_motion_death(self):
        if bs.getactivity().globalsnode.slow_motion:
            bs.getactivity().globalsnode.slow_motion = False

    def start_choosing_timer(self):
        self.time = self.get_s['Round Time']
        self.loop_timer = (
            bs.Timer(1, babase.CallStrict(self.decrease), repeat=True)
            if not self.game_ended
            else None
        )  # Timer decrease logic = call each seconds

    def decrease(self):
        time_message = ['No Flag', 'Ended', 'Ends', 'Preparing', 'LL']
        if any(word in f'{self.r_timer.text}' for word in time_message):
            return  # Round Timer Killer :O
        else:
            if int(self.time) != 0:
                self.change_hint_flag_color()
                self.time -= 1
                self.r_timer.text = 'Sorting Time' + '\n' + str(self.time + 1)

                # Timer icons ♪(´▽｀)
                time_limit = self.get_s['Round Time']
                if time_limit >= 22:
                    time_boundary1 = 18
                    time_boundary2 = 12
                    time_boundary3 = 6

                elif time_limit >= 18:
                    time_boundary1 = 15
                    time_boundary2 = 10
                    time_boundary3 = 5

                elif time_limit >= 12:
                    time_boundary1 = 10
                    time_boundary2 = 6
                    time_boundary3 = 3

                if int(self.time) < time_boundary1:
                    self.r_timer.text = self.r_timer.text.replace('', '')
                if int(self.time) < time_boundary2:
                    self.r_timer.text = self.r_timer.text.replace('', '')
                if int(self.time) < time_boundary3:
                    self.r_timer.text = self.r_timer.text.replace('', '')

                if int(self.time) > 3:
                    bs.getsound('tick').play(2)
                elif int(self.time) == 3:
                    bs.getsound('orchestraHit').play(2)
                elif int(self.time) == 2:
                    bs.getsound('orchestraHit2').play(2)
                elif int(self.time) == 1:
                    bs.getsound('orchestraHit3').play(2)
                elif int(self.time) == 0:
                    bs.getsound('orchestraHit4').play(2)
            else:
                self.loop_timer = None
                self.eliminate_players_timer = bs.Timer(
                    0.05, babase.CallStrict(self.eliminate_players), repeat=True
                )
                self.r_timer.position = (0, 3.5, -6)
                self.r_timer.text = 'Time Out!'

    def eliminate_players(self):
        if not len(self.not_done_players) <= 0:
            for player in self.not_done_players:
                try:
                    player.alive = False
                    player.done = None
                    player.actor.node.invincible = False
                    self.not_done_players.remove(player)
                    self.whos_alive_in_end.remove(player)
                    bs.broadcastmessage(
                        f'{player.getname()} Timed Out!', color=(1, 0, 0)
                    )
                    player.actor.handlemessage(bs.DieMessage())
                    player.actor.handlemessage(bs.ShouldShatterMessage())
                    player.tag_node.text = self.on_dead_message
                    player.tag_node.color = (1.5, 0.85, 1)
                    explosion_sounds = [
                        'explosion01',
                        'explosion02',
                        'explosion03',
                        'explosion04',
                        'explosion05',
                    ]
                    bs.getsound(random.choice(explosion_sounds)).play(2)
                    Blast(position=player.position, blast_radius=1.5)
                    bs.timer(0.1, self.update_tags)
                except Exception as e:
                    print(str(e))
                    try:
                        player.alive = False
                        player.done = None
                    except:
                        pass
                    self.is_first_round = False
                    self.kill_flags()
                    self.eliminate_players_timer = None
                    bs.timer(2, self.make_round)
        else:
            self.eliminate_players_timer = None
            self.is_first_round = False
            self.kill_flags()
            bs.timer(2, self.make_round)
