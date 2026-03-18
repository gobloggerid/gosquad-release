# ba_meta require api 9
# A simple game, like ping-pong?

# Started: 29 June 2025
# Continued: 6 July 2025, 7 July 2025, 8 July 2025
# Release: 8 July 2025

from __future__ import annotations

from typing import TYPE_CHECKING
import random

########### Ballistica Modules ###########
import babase
import bascenev1 as bs

from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.onscreentimer import OnScreenTimer

from bascenev1lib.actor.bomb import Blast
from bascenev1lib.actor.playerspaz import PlayerSpaz

if TYPE_CHECKING:
    from typing import Any, Type, Union, Sequence, Optional

class Icon(bs.Actor):
    """Creates Live PLayer Character Spaz in-game icon on screen."""

    def __init__(
        self,
        player: Player,
        position: tuple[float, float],
        scale: float,
        show_lives: bool = True,
        show_death: bool = True,
        name_scale: float = 1,
        name_maxwidth: float = 115.0,
        flatness: float = 1,
        shadow: float = 1,
    ):
        super().__init__()

        self._player = player
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._outline_tex = bs.gettexture('characterIconMask')

        icon = player.get_icon()
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'vr_depth': 400,
                'tint2_color': icon['tint2_color'],
                'mask_texture': self._outline_tex,
                'opacity': 1,
                'absolute_scale': True,
                'attach': 'bottomCenter',
            },
        )
        self._name_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': babase.Lstr(value=player.getname()),
                'color': babase.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        if self._show_lives:
            self._lives_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': 'x0',
                    'color': (1, 1, 0.5),
                    'h_align': 'left',
                    'vr_depth': 430,
                    'shadow': 1,
                    'flatness': 1,
                    'h_attach': 'center',
                    'v_attach': 'bottom',
                },
            )
        self.set_position_and_scale(position, scale)

    def set_position_and_scale(
        self, position: tuple[float, float], scale: float
    ) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._name_text.scale = 1 * scale * self._name_scale
        if self._show_lives:
            self._lives_text.position = (
                position[0] + scale * 10.0,
                position[1] - scale * 43.0,
            )
            self._lives_text.scale = 1 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        if not self.node or not self.node.exists():
            return

        if self._player:
            lives = self._player.lives
        else:
            lives = 0

        if (
            self._show_lives
            and hasattr(self, '_lives_text')
            and self._lives_text.exists()
        ):
            if lives > 0:
                self._lives_text.text = 'x' + str(lives - 1)
            else:
                self._lives_text.text = babase.charstr(babase.SpecialChar.SKULL)

        if lives == 0 and self._name_text.exists():
            self._name_text.opacity = 0.2
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2

    def handle_player_spawned(self) -> None:
        """Our player spawned; hooray!"""
        if not self.node:
            return
        self.node.opacity = 1
        self.update_for_lives()

    def handle_player_died(self) -> None:
        """Well poo; our player died."""
        if not self.node:
            return
        if self._show_death:
            bs.animate(
                self.node,
                'opacity',
                {
                    0.00: 1,
                    0.05: 0.0,
                    0.10: 1,
                    0.15: 0.0,
                    0.20: 1,
                    0.25: 0.0,
                    0.30: 1,
                    0.35: 0.0,
                    0.40: 1,
                    0.45: 0.0,
                    0.50: 1,
                    0.55: 0.2,
                },
            )
            lives = self._player.lives
            if lives == 0:
                bs.timer(0.6, bs.WeakCallStrict(self.update_for_lives))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.delete()
            return None
        return super().handlemessage(msg)

    def delete(self) -> None:
        if self.node:
            self.node.delete()
        self._player = None



Translate_Texts: dict[str, dict[str, str]] = {
'gameEnds': { # >> 
    'id': 'Permainan Berakhir',
    'en': 'Game Ends',
},
'gameName': { 
    'id': 'Strike Ball',
    'en': 'Strike Ball',
},
'gameDescBIG': { 
    'id': 'Pantulkan Bolanya tanpa henti',
    'en': 'Don\'t stop bouncing the Ball',
},
'gameDescInGame': { 
    'id': 'Jangan biarkan bola melewati Paddle Anda',
    'en': 'Don\'t let the ball pass your Paddle',
},
'settingPlayerLives': { # Player Lives
    'id': 'Nyawa Pemain',
    'en': 'Player Lives',
},
'settingBalanceLives': { # Balance Player Lives
    'id': 'Nyawa Seimbang',
    'en': 'Balance Total Lives',
},
'settingTimeLimit': { # Time Limit
    'id': 'Batas Waktu (Detik)',
    'en': 'Time Limit (Seconds)',
},
'settingEpicMode': { # Epic Mode
    'id': 'Mode Epik',
    'en': 'Epic Mode',
},
'': { 
    'id': '',
    'en': '',
},
}
"""Global Langs"""


def get_app_lang_as_id():
    """
    Returns The Language `ID`.
    Such as: `id`, `en`, `hi`, `...`
    """
    App_Lang = bs.app.lang.language
    lang_id = 'en'
    if App_Lang == 'Indonesian':
        lang_id = 'id'
    elif App_Lang == 'English':
        lang_id = 'en'
    else:
        lang_id = 'en'
    return lang_id
app_lang = get_app_lang_as_id()

def get_lang_text(key: str) -> str:
    """
    Return Translated Text From `Str` Key Given.
    """
    # text key: lang -> text
    text = Translate_Texts.get(key, {}).get(app_lang, '')
    if not text.strip() or text.strip() == '':
        return f"EmptyText: '*[{key}]'"
    return text

"""############################### Game Management ###############################"""
class Player(bs.Player['Team']):
    def __init__(self) -> None:
        super().__init__()
        self.lives = 0 # For counting player Lives
        self.icons: list[Icon] = [] # Their icons
        self.attached_ball: Ball | None = None
        self.attached_paddle: Paddle | None = None

class Team(bs.Team[Player]):
    def __init__(self) -> None:
        super().__init__()
        self.survival_seconds: int | None = None
        self.spawn_order: list[Player] = []
"""############################### Game Management ###############################"""

# ba_meta export bascenev1.GameActivity
class FluffysGame6_SB(bs.TeamGameActivity[Player, Team]):
    name = get_lang_text('gameName')
    description = f"{get_lang_text('gameDescBIG')}"
    scoreconfig = bs.ScoreConfig(
        label='Survived',
        scoretype=bs.ScoreType.SECONDS,
        none_is_winner=True
    )
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[bs.Session]) -> list[babase.Setting]: # type: ignore
        settings = [
            bs.IntSetting(get_lang_text('settingTimeLimit'),
                min_value=0,
                max_value=600,
                increment=60,
                default=600
            ),
            bs.IntSetting(get_lang_text('settingPlayerLives'),
                min_value=1,
                max_value=5,
                increment=1,
                default=2
            ),
            bs.BoolSetting(get_lang_text('settingBalanceLives'), default=True),
            bs.BoolSetting(get_lang_text('settingEpicMode'), default=False),
        ]
        return settings
        
    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> list[str]:
        return [
            'Strike Map',
        ]

    def get_instance_description(self) -> Union[str, Sequence]:
        """Description On Big Message On Begin"""
        return f"{get_lang_text('gameDescBIG')}! By FluffyPal :)\n"

    def get_instance_description_short(self) -> Union[str, Sequence]:
        """Description In Game On Top Left"""
        return f"{get_lang_text('gameDescInGame')}!\nBy FluffyPal"

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._round_timer: OnScreenTimer | None = None

        self._time_limit = int(settings[get_lang_text('settingTimeLimit')])
        self._player_lives = int(settings[get_lang_text('settingPlayerLives')])
        self._balance_total_lives = bool(settings[get_lang_text('settingBalanceLives')])
        self._epic_mode = bool(settings[get_lang_text('settingEpicMode')])

        self._solo_mode = True

        self.shared = SharedObjects.get()

        musics: list[bs.MusicType] = [
           bs.MusicType.MENU, bs.MusicType.FOOTBALL
        ]

        """Default Configurations"""
        self.default_music = random.choice(musics)
        self.slow_motion = self._epic_mode

        """For End Game Logic"""
        self._last_player_death_time: Optional[float] = None
        self._begin_round: bool = True
        self._start_time: float | None = None

        self.player_scored: bool = False
        """Handle if the round is player_scored condition; preventing unwanted bugs"""
        self.suicide_score: bool = False
        """Determines if its a suicide ball"""

        # Player leaving handler
        self.active_player_leave: list[Player] = []
        """Detect if player leaving is an active player"""
        self.active_player_leave_paddle: Paddle | None = None

        self.whos_alive_in_end: list[Player] = []
        """For scoring"""

        """Game Utils"""
        self.active_players: dict[Player, Paddle] = {}
        self.active_paddles: dict[Paddle, Player] = {}
        self.paddles: list[Paddle] = []# Paddle1: bottom, Paddle2: top

        self.last_chosen_paddle: Paddle | None = None

        player_x_offset = 3.65
        player_z_offset = 6.5
        self.player_pos1 = (player_x_offset, 1, player_z_offset+0.5)
        self.player_pos2 = (-player_x_offset, 1, -player_z_offset+1.45)

        # Game score logic
        self.victim_player: Player | None = None
        self.winning_player: Player | None = None

        self.wall_x_bound = 2.5
        self.wall_z_bound = 7.5
        self.set_materials()

    def on_begin(self) -> None:
        """On Game Begin"""
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)

        self._start_time = bs.time()

        for player in self.players:
            player.lives = self._player_lives
            self.whos_alive_in_end.append(player)
        
        if (self._balance_total_lives
            and self.teams[0].players
            and self.teams[1].players
        ):
            if self._get_total_team_lives(
                self.teams[0]
            ) < self._get_total_team_lives(self.teams[1]):
                lesser_team = self.teams[0]
                greater_team = self.teams[1]
            else:
                lesser_team = self.teams[1]
                greater_team = self.teams[0]
            add_index = 0
            while self._get_total_team_lives(
                lesser_team
            ) < self._get_total_team_lives(greater_team):
                lesser_team.players[add_index].lives += 1
                add_index = (add_index + 1) % len(lesser_team.players)

        self.setup_goal_and_wall_region()
        try:
            self.setup_map()
        except Exception as e:
            print(e)
        self.make_round()

        #bs.broadcastmessage("Game is still at test, report any bugs to the minigame creator.", color=(0.25, 0.65, 0.5))

    #### Game Utils
    def bounce_ball_wall(self):
        self.ball.bounce_wall()

    def bounce_ball_paddle(self):
        collision = bs.getcollision() # We got the collision from Paddle Node
        self.ball.bounce_paddle(collision)

    def set_materials(self):
        # Materials for collision
        self.ball_material = bs.Material()
        self.ball_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', self.shared.player_material)
            ),
            actions=(('modify_part_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True),
                     ('call', 'at_connect', self.kill_player)
            )
        )
        self.ball_material.add_actions(
            actions=(('modify_part_collision', 'friction', 9999)
            )
        )

        self.paddle_material = bs.Material()
        self.paddle_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', self.ball_material)
            ),
            actions=(('modify_part_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True),
                     ('call', 'at_connect', self.bounce_ball_paddle)
            )
        )
        self.paddle_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', self.shared.player_material)
            ),
            actions=(('modify_part_collision', 'collide', False),
                     ('modify_part_collision', 'physical', False)
            )
        )

        self.wall_material = bs.Material()
        self.wall_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', self.ball_material)
            ),
            actions=(('modify_part_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True),
                     ('call', 'at_connect', self.bounce_ball_wall)
            )
        )
        self.wall_material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', self.shared.player_material)
            ),
            actions=(('modify_part_collision', 'collide', True),
                     ('modify_part_collision', 'physical', True)
            )
        )

        self.goal_material = bs.Material()
        self.goal_material.add_actions(
            conditions=(('they_are_different_node_than_us',),
                        'and',
                        ('they_have_material', self.ball_material)
            ),
            actions=(('modify_part_collision', 'physical', False),
                     ('modify_part_collision', 'collide', True),
                     ('call', 'at_connect', self.handle_goal)
            )
        )

    def setup_goal_and_wall_region(self):
        # Wall regions
        for x in [-self.wall_x_bound, self.wall_x_bound]:
            wall_node = bs.newnode('region', attrs={
                'position': (x, 0, -self.wall_z_bound),
                'scale': (0.2, 1.35, self.wall_z_bound*5.5),
                'type': 'box',
                'materials': [self.wall_material, self.shared.footing_material]
            })

        # Goal regions
        self.goal_top = GoalRegion((0, 0, -self.wall_z_bound-0.1))
        self.goal_bottom = GoalRegion((0, 0, self.wall_z_bound+0.5))

    def setup_map(self):
        self.map.player_ground(self.player_pos1) # type: ignore
        self.map.player_ground(self.player_pos2) # type: ignore

        self.map.ground() # type: ignore
        self.map.walls_x() # type: ignore

    def spawn_paddles(self):
        paddle_y_pos = 0.3
        if self.paddles or self.active_paddles:
            print(f"Paddles already exist in {self.getname()}; this shouldn't happen:\n"
                  f"Paddles count: {len(self.paddles)} | Active paddles: {len(self.active_paddles)}")
            return
        self.paddles = [
            Paddle(position=(0, paddle_y_pos, -self.wall_z_bound+0.75)), # Bottom
            Paddle(position=(0, paddle_y_pos, self.wall_z_bound-0.5)) # Top
        ]

    def serve_ball(self, serving_player: Player):
        if self.ball and self.ball.node and self.ball.node.exists():
            self.ball.node.position = (0, 1, 0)
        else:
            self.ball = Ball()

        server_player = serving_player
        server_paddle = self.active_players[serving_player]

        server_player.attached_ball = self.ball
        self.ball.last_player_hit = serving_player

        server_paddle.attach_ball(self.ball)

    def handle_goal(self):
        if self.player_scored:
            return

        collision = bs.getcollision() # We get the collision from GoalRegion Node

        ball = collision.opposingnode
        ball_delegate = ball.getdelegate(Ball, True)

        # Get goal region owner
        goal_region = collision.sourcenode # Our goal region Node
        goal_region_delegate = goal_region.getdelegate(GoalRegion, True) # Get its delegeate
        goal_owner = goal_region_delegate.owner # In here, we can get their owner, means the one who goaled aka lose
        opposing_goal_region = self.goal_top if self.goal_top is not goal_region_delegate else self.goal_bottom

        player_goaler = ball_delegate.last_player_hit

        if ball is not self.ball.node:
            print(f"Oops, not a ball node: {ball}")
            return

        # Check if goal owner is different from last player hit
        assert goal_owner
        if goal_owner is not player_goaler:
            self.victim_player = goal_owner
            self.winning_player = player_goaler
        else:
            self.victim_player = player_goaler
            self.winning_player = opposing_goal_region.owner
            self.suicide_score = True

        #assert self._round_timer
        #self._round_timer.stop()

        ball_delegate.stop_normalize_velocity()
        ball_delegate.stop_normalize_position()
        ball_delegate.zero_gravity()
        ball_delegate.slows_ball(goal_region_delegate.node.position[2])

        if not self.victim_player:
            print(f"Victim player not found in {self.getname()}; this shouldn't happen:\n"
                  f"PlayerGoaler: {player_goaler} | {player_goaler.getname(True, False) if player_goaler else player_goaler}\n"
                  f"GoalRegion: {goal_region_delegate} | {goal_region_delegate.pos_str}; Owner: {goal_owner} | {goal_owner.getname(True, False)}."
            )
            return

        bs.timer(1, bs.CallStrict(ball_delegate.aim_player, self.victim_player))

    def kill_player(self):
        if self.has_ended():
            return

        if self.player_scored:
            #print(f"Kill player called while player scored: {self.player_scored}; this shouldn't happen")
            return

        collision = bs.getcollision() # We get the collision from Ball Node

        player = collision.opposingnode
        player.handlemessage(bs.ShouldShatterMessage())
        player.handlemessage(bs.DieMessage())
        Blast(position=player.position, velocity=self.ball.node.velocity, blast_radius=1)

        if not self.suicide_score and self.winning_player:
            self.stats.player_scored(
                self.winning_player,
                base_points=10,
                kill=True,
                display=True,
                screenmessage=True,
                victim_player=self.victim_player,
            )

            assert isinstance(self.winning_player.actor, PlayerSpaz)
            self.winning_player.actor.on_jump_press()
            self.winning_player.actor.on_jump_release()
            self.winning_player.actor.node.handlemessage(
                "celebrate", (2500 if not self.globalsnode.slow_motion else 2500*0.5))

        self.ball.reset()

        self.player_scored = True
        self.suicide_score = False

        self.checkEnd()
    #### Game Utils

    ### Game Functionality
    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = self.spawn_player_spaz(player)
        spaz.disconnect_controls_from_player()

        # Standard
        for icon in player.icons:
            icon.handle_player_spawned()
        if player.lives <= 1:
            spaz.play_big_death_sound = True

        if self.active_player_leave:
            self.last_chosen_paddle = self.active_player_leave_paddle if self.active_player_leave_paddle else self._get_next_paddle()
            self.last_chosen_paddle.set_owner(player)
            self.last_chosen_paddle.connect_input()
            self.active_players[player] = self.last_chosen_paddle
            self.active_paddles[self.last_chosen_paddle] = player
            self.set_player_goal_pos(spaz, self.last_chosen_paddle)
            self.serve_ball(player)

            self.active_player_leave_paddle = None
            self.active_player_leave.pop()

        elif not self.active_players or self._begin_round:
            self.last_chosen_paddle = self._get_next_paddle()
            self.last_chosen_paddle.set_owner(player)
            self.last_chosen_paddle.connect_input()
            self.active_players[player] = self.last_chosen_paddle
            self.active_paddles[self.last_chosen_paddle] = player
            self.set_player_goal_pos(spaz, self.last_chosen_paddle)

        elif self.player_scored:
            assert self.victim_player 

            if len(self.active_players) == 2 and all(p.is_alive() for p in self.active_players):
                print(f"There are still both player alive in the round {self.getname()}; this shouldn't happen\n"
                      f"Player: {player} | {player.getname(True, False)}")
                spaz.handlemessage(bs.DieMessage())
                return spaz
            self.refresh_next_round()

            # Update paddle ownership and connections
            # Died teammate
            self.last_chosen_paddle = self._get_next_paddle()
            self.last_chosen_paddle.set_owner(player)
            self.last_chosen_paddle.connect_input()
            self.active_players[player] = self.last_chosen_paddle
            self.active_paddles[self.last_chosen_paddle] = player
            self.set_player_goal_pos(spaz, self.last_chosen_paddle)

            # Ball goaler / Winning teammate
            assert self.winning_player
            self.last_chosen_paddle = self._get_next_paddle()
            self.last_chosen_paddle.set_owner(self.winning_player)
            self.last_chosen_paddle.connect_input()
            self.active_players[self.winning_player] = self.last_chosen_paddle
            self.active_paddles[self.last_chosen_paddle] = self.winning_player

            assert isinstance(self.winning_player.actor, PlayerSpaz)
            self.set_player_goal_pos(self.winning_player.actor, self.last_chosen_paddle)

            # Serve the ball to start the round for current player spawned
            self.serve_ball(player)

        elif len(self.active_players) == 1:
            self.last_chosen_paddle = self._get_next_paddle()
            self.last_chosen_paddle.set_owner(player)
            self.last_chosen_paddle.connect_input()
            self.active_players[player] = self.last_chosen_paddle
            self.active_paddles[self.last_chosen_paddle] = player
            self.set_player_goal_pos(spaz, self.last_chosen_paddle)

        self.winning_player = None
        self.victim_player = None
        self.player_scored = False
        self.suicide_score = False

        self._update_icons()

        return spaz

    def set_player_goal_pos(self, spaz: PlayerSpaz, paddle: Paddle):
        # Bottom
        assert isinstance(spaz._player, Player)
        if paddle.initial_z_pos > 0:
            pos = self.player_pos1
            angle = 225
            self.goal_bottom.set_owner(spaz._player)
        # Top
        else:
            pos = self.player_pos2
            angle = 45
            self.goal_top.set_owner(spaz._player)
        spaz.handlemessage(bs.StandMessage(pos, angle=angle))

    def refresh_next_round(self):
        self.reset_active_paddles()
        self.spawn_paddles()

    def reset_active_paddles(self):
        for paddle in self.paddles:
            paddle.delete()
        self.active_paddles.clear()
        self.paddles.clear()

    def _cleanup_game_objects(self) -> None:
        if hasattr(self, 'ball') and self.ball is not None:
            self.ball.delete()
            self.ball = None

        for paddle in list(self.paddles):
            paddle.delete()
        self.paddles.clear()
        self.active_paddles.clear()
        self.active_players.clear()

        for goal in (
            getattr(self, 'goal_top', None),
            getattr(self, 'goal_bottom', None),
        ):
            if goal is not None:
                goal.delete()

        self.goal_top = None
        self.goal_bottom = None
        self.last_chosen_paddle = None
        self.active_player_leave.clear()
        self.active_player_leave_paddle = None

    def _cleanup_player_refs(self) -> None:
        for player in self.players:
            for icon in list(player.icons):
                icon.delete()
            player.icons.clear()
            player.attached_ball = None
            player.attached_paddle = None

        self.whos_alive_in_end.clear()

    def on_expire(self) -> None:
        self._cleanup_game_objects()
        self._cleanup_player_refs()
        super().on_expire()

    def get_active_players(self):
        return [p for p in self.active_players]

    def make_round(self):
        self.ball = Ball()

        self.spawn_paddles()
        bs.timer(3.5, self._update)

    def on_player_join(self, player: Player) -> None:
        """Main Func To Handle Player Joins Logic"""
        if self.has_begun(): # Check if the game has begun
            p_cl = player.sessionplayer.inputdevice.client_id
            bs.broadcastmessage(babase.Lstr(resource='playerDelayedJoinText',
                                subs=[('${PLAYER}', player.getname(full=True))]),
                                color=(0.25, 0.65, 0.65), transient=True, clients=[p_cl])
            player.icons = []
            player.lives = 0

            if player in self.whos_alive_in_end:
                self.whos_alive_in_end.remove(player)
            return

        player.team.spawn_order.append(player)

    def on_player_leave(self, player: Player) -> None:
        """Main Func To Handle Player Leaves Logic"""
        super().on_player_leave(player)
        player_name = player.getname()

        if player in self.active_players:
            del self.active_players[player]
            self.active_player_leave.append(player)
            self.active_player_leave_paddle = player.attached_paddle

            assert player.attached_paddle
            if player.attached_paddle.attached_ball:
                player.attached_paddle.detach_ball()

            self.ball.reset()

            if player is self.victim_player:
                self.ball.stop_normalize_velocity()

                assert self.winning_player
                self.stats.player_scored(
                    self.winning_player,
                    base_points=10,
                    kill=True,
                    display=True,
                    screenmessage=True,
                    victim_player=self.victim_player,
                )

                #assert self._round_timer
                #self._round_timer.stop()

        if player in self.whos_alive_in_end:
            self.whos_alive_in_end.remove(player)

        if player in player.team.spawn_order:
            player.team.spawn_order.remove(player)

        while player.lives > 0:
            for p in player.team.players:
                if player.lives <= 0:
                    break
                if p in self.whos_alive_in_end:
                    p.lives += 1
                    player.lives -= 1

            if player.lives <= 0 or len(player.team.players) <= 1:
                break

        player.attached_ball = None
        player.attached_paddle = None
        player.lives = 0

        if self._get_total_team_lives(player.team) == 0:
            assert self._start_time
            player.team.survival_seconds = int(bs.time() - self._start_time)

        self._update_icons()
        bs.timer(3, self._update)
        bs.timer(1.5, self.checkEnd)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            player = msg.getplayer(Player)

            if player in self.active_players:
                del self.active_players[player]
            else:
                print(f"Can't remove died player as active in {self.getname()}; this shouldn't happen\n"
                      f"Player: {player} | {player.getname(True, False)}")
                return

            player.lives -= 1
            if player.lives < 0:
                print(
                    f"Got lives < 0 in {self.getname()}; this shouldn't happen"
                )
                player.lives = 0

            player.team.spawn_order.remove(player)
            player.team.spawn_order.append(player)
            player.attached_ball = None
            player.attached_paddle = None

            for icon in player.icons:
                icon.handle_player_died()

            # If we hit zero lives, we're dead (and our team might be too).
            if player.lives == 0:
                if player in self.whos_alive_in_end:
                    self.whos_alive_in_end.remove(player)

                if self._get_total_team_lives(player.team) == 0:
                    assert self._start_time
                    player.team.survival_seconds = int(
                        bs.time() - self._start_time
                    )

                for icon in player.icons:
                    icon.delete()
                player.icons = []

            player.resetinput()

            bs.timer(2.5, self._update)
        else:
            # Default handler:
            return super().handlemessage(msg)
        return None

    def _get_player_paddle(self, player: Player):
        return self.active_players.get(player)

    def _get_next_paddle(self):
        if not self.paddles:
            raise RuntimeError(f"No paddles are available in {self.getname()}.")

        unowned_paddles = [paddle for paddle in self.paddles if paddle.owner is None]
        if unowned_paddles:
            if self.last_chosen_paddle in unowned_paddles and len(unowned_paddles) > 1:
                return next(
                    paddle
                    for paddle in unowned_paddles
                    if paddle is not self.last_chosen_paddle
                )
            return unowned_paddles[0]

        if self.last_chosen_paddle is None:
            return self.paddles[0]

        next_paddles = [
            paddle for paddle in self.paddles if paddle is not self.last_chosen_paddle
        ]
        return next_paddles[0] if next_paddles else self.last_chosen_paddle

    def _update_solo_mode(self) -> None:
        # For both teams, find the first player on the spawn order list with
        # lives remaining and spawn them if they're not alive.
        for team in self.teams:
            # Prune dead players from the spawn order.
            team.spawn_order = [p for p in team.spawn_order if p.lives]
            for player in team.spawn_order:
                if player.lives > 0:
                    if not player.is_alive():
                        self.spawn_player(player)
                    break


    def _update(self) -> None:
        if self.has_ended():
            return

        is_player_update = False
        if self._solo_mode:
            # For both teams, find the first player on the spawn order
            # list with lives remaining and spawn them if they're not alive.
            for team in self.teams:
                # Prune dead players from the spawn order.
                team.spawn_order = [p for p in team.spawn_order if p]
                for player in team.spawn_order:
                    assert isinstance(player, Player)
                    if player.lives > 0:
                        if not player.is_alive():
                            self.spawn_player(player)
                            self._update_icons()
                            is_player_update = True
                        break

        # If we're down to 1 or fewer living teams, start a timer to end
        # the game (allows the dust to settle and draws to occur if deaths
        # are close enough).
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = bs.Timer(2.5, self.end_game)

        if self._begin_round:
            self.serve_ball(random.choice(list(self.active_players.keys())))

        #if is_player_update:
            #if not self._round_timer:
                #self._round_timer = OnScreenTimer()
            #else:
               #self._round_timer.stop(0)

        self._begin_round = False

    def _update_icons(self) -> None:
        # First off, clear out all icons.
        for player in self.whos_alive_in_end:
            for icon in player.icons:
                icon.delete()
            player.icons = []

        # Now for each team, cycle through our available players
        # adding icons.
        y_pos = 20
        for team in self.teams:
            if team.id == 0:
                xval = -60
                x_offs = -78
            else:
                xval = 60
                x_offs = 78
            is_first = True
            test_lives = 1
            while True:
                players_with_lives = [
                    p
                    for p in team.spawn_order
                    if p and p.lives >= test_lives
                ]
                if not players_with_lives:
                    break
                for player in players_with_lives:
                    player.icons.append(
                        Icon(
                            player,
                            position=(xval, (y_pos if is_first else y_pos-15)+20),
                            scale=1 if is_first else 0.5,
                            name_maxwidth=130 if is_first else 75,
                            name_scale=0.8 if is_first else 1,
                            flatness=0.0 if is_first else 1,
                            shadow=0.5 if is_first else 1,
                            show_death=is_first,
                            show_lives=False,
                        )
                    )
                    xval += x_offs * (0.8 if is_first else 0.56)
                    is_first = False
                test_lives += 1

    def _get_living_teams(self) -> list[Team]:
        return [
            team
            for team in self.teams
            if len(team.players) > 0
            and any(player.lives > 0 for player in team.players)
        ]

    def _get_total_team_lives(self, team: Team) -> int:
        return sum(player.lives for player in team.players)

    def checkEnd(self):
        """Basic check end logic for mostly all lives-based games"""
        alive_teams = 0
        end_time = 2.5
        for team in self.teams:
            for player in team.players:
                if player.lives:
                    alive_teams += 1
                    break

        if alive_teams <= 1:
            bs.timer(end_time, self.end_game)

            for player in self.active_players:
                assert isinstance(player.actor, PlayerSpaz)
                player.actor.node.handlemessage(bs.StandMessage((0, 0.5, 0)))
                player.actor.connect_controls_to_player(enable_fly=False)

            self.player_scored = True

    def end_game(self) -> None:
        """End game logic for lives based games"""
        if self.has_ended(): return

        results = bs.GameResults()

        for player in self.whos_alive_in_end:
            self.stats.player_scored(player, 100, big_message=False)

        for team in self.teams:
            results.set_team_score(team, team.survival_seconds)

        self._cleanup_game_objects()
        self._cleanup_player_refs()
        self.end(results=results)
    ### Game Functionality

"""################################ Game Utils ################################"""
class GoalRegion(bs.Actor):
    def __init__(self, position: tuple[float, float, float]) -> None:
        super().__init__()

        self.owner: Player | None = None
        """Related player to its Goal zone"""

        self.pos_str = "Bottom" if position[2] > 0 else "Top"

        self.activity: FluffysGame6_SB

        self.node = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': position,
                'scale': (5.5, 6, 0.1),
                'type': 'box',
                'materials': [self.activity.goal_material],
            }
        )

    def set_owner(self, player: Player):
        self.owner = player

    def delete(self) -> None:
        self.owner = None
        if self.node:
            self.node.delete(True)


class Paddle(bs.Actor):
    def __init__(self, position: tuple[float, float, float] = (0, 0.35, 0)):
        super().__init__()
        self.owner: Player | None = None
        self.attached_ball: Ball | None = None

        self.attached_ball_delay = 17.5

        self.scale = 1.6
        self.speed = 3.5
        self.activity: FluffysGame6_SB

        self.max_pos_offset = self.activity.wall_x_bound-self.scale*0.5

        self.initial_y_pos = position[1]
        self.initial_z_pos = position[2]
        self.pos_str = "Bottom" if position[2] > 0 else "Top"

        mesh = bs.getmesh('powerupSimple')
        tex = bs.gettexture('egg2')
        self.node = bs.newnode('prop',
            delegate=self, 
            attrs={
                'position': position,
                'mesh': mesh,
                'light_mesh': mesh,
                'color_texture': tex,
                'body': 'box',
                'reflection': 'soft',
                'density': 9999,
                'mesh_scale': self.scale,
                'body_scale': self.scale,
                'gravity_scale': 0,
                'reflection_scale': [0.3],
                'is_area_of_interest': True,
                'materials': [self.activity.shared.object_material, self.activity.paddle_material]
            }
        )
        self.node.velocity = (0, -1, 0)

        self.ball_math_node: bs.Node | None = None
        self.region_node: bs.Node | None = None
        self.region_math_node: bs.Node | None = None
        self.locator_node: bs.Node | None = None

        self._normalize_position_timer = bs.Timer(
            0.1, bs.CallStrict(self._normalize_position), repeat=True
        )

        self._create_collision_region(position)

    def _create_collision_region(self, position: tuple[float, float, float]):
        """Create collision region and locator nodes for proper bouncing"""
        region_scale = (0.5, 0.05, 0.005)
        self.region_node = bs.newnode('region',
            delegate=self,
            owner=self.node,
            attrs={
                'position': position,
                'scale': region_scale,
                'type': 'sphere',
                'materials': [self.activity.paddle_material]
            }
        )

        # Create math node to connect region to paddle
        z_offset = 8.5
        z_pos = (position[2] - z_offset + 1 if position[2] >= 0 else position[2] + z_offset - 0.25)
        self.region_math_node = bs.newnode('math',
            delegate=self,
            owner=self.region_node,
            attrs={
                'input1': (0, 0.1, z_pos),
                'operation': 'add'
            }
        )

        # Connect nodes: paddle position → math node → region position
        self.node.connectattr('position', self.region_math_node, 'input2')
        self.region_math_node.connectattr('output', self.region_node, 'position')

        # Create locator node for visual reference of collision region
        self.locator_node = bs.newnode('locator',
            delegate=self,
            owner=self.region_node,
            attrs={
                'shape': 'circle',
                'position': position,
                'color': (0, 1, 0.5),
                'opacity': 0.75,
                'draw_beauty': True,
                'additive': True,
                'size': (1.35, 0.1, 0.1)
            }
        )

        # Connect locator to region
        self.region_node.connectattr('position', self.locator_node, 'position')

    def reset_x_position(self):
        pos = self.node.position
        self.node.position = (0, 1, pos[2])

    def set_owner(self, owner: Player):
        self.reset_input()
        self.owner = owner
        owner.attached_paddle = self

    def connect_input(self):
        if self.owner:
            self.owner.assigninput(bs.InputType.LEFT_RIGHT, self.move)
            self.owner.assigninput(bs.InputType.PUNCH_PRESS, self.release_ball)
        else:
            print(f"Owner is invalid in {self.activity.getname()} Paddle {self}; this shouldn't happen\n"
                  f"Owner:- {self.owner} | {self.owner.getname(True, False) if self.owner else self.owner}\n"
                  f"Paddle:- Pos: {self.node.position} | Is ball attached: {self.attached_ball}")

    def reset_input(self):
        if self.owner: self.owner.resetinput()

    def release_ball(self):
        self.detach_ball(True)

    def attach_ball(self, ball: Ball):
        self.attached_ball = ball
        pos = self.node.position
        z_offset = 8.5
        #x_pos = (pos[0] + 0.25 if pos[2] <= 0 else pos[0] - 0.25)
        z_pos = (pos[2] - z_offset if pos[2] >= 0 else pos[2] + z_offset + 0.75)

        if not self.ball_math_node:
            # Create math node to handle position calculations
            self.ball_math_node = bs.newnode('math', delegate=self,
                owner=self.node,
                attrs={
                    'input1': (0, ball.initial_y_pos, z_pos),  # Offset position
                    'operation': 'add'
                }
            )
        # Idk how, but it works. I guess??
        self.node.connectattr('position', self.ball_math_node, 'input2')
        self.ball_math_node.connectattr('output', ball.node, 'position')

        bs.timer(self.attached_ball_delay*0.5, self.check_attached_ball)
        bs.timer(self.attached_ball_delay, bs.CallStrict(self.detach_ball, True))

    def detach_ball(self, fire: bool = False):
        if self.ball_math_node:
            self.ball_math_node.delete(True)
            self.ball_math_node = None

        if self.attached_ball and fire:
            paddle_x_velo = self.node.velocity[0] # Lets add paddle's x velo
            direction = ((paddle_x_velo, 0, -10) if self.activity.ball.node.position[2] >= 0 else
                        (paddle_x_velo, 0, 10))
            self.attached_ball.launch(direction)

            self.attached_ball = None
            #assert self.activity._round_timer
            #self.activity._round_timer.start()

    def check_attached_ball(self):
        if self.attached_ball:
            assert self.owner
            client = self.owner.sessionplayer.inputdevice.client_id
            msg = "Press punch to release the Ball"
            bs.broadcastmessage(msg, color=(0, 1, 0.5), transient=True, clients=[client])

    def get_paddle_position(self):
        pos = self.node.position
        return pos[0], pos[1], pos[2]

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.delete()
            return None
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            return super().handlemessage(msg)

    """ Movement Logic """
    def move(self, value: float):
        if self.owner and not self.owner.is_alive():
            return
        if value > 0:
            if self.node.position[0] >= self.max_pos_offset:
                return
            self.move_timer = bs.Timer(
                0.1, bs.CallStrict(self._normalize, value), repeat=True
            )
        elif value < 0:
            if self.node.position[0] <= -self.max_pos_offset:
                return
            self.move_timer = bs.Timer(
                0.1, bs.CallStrict(self._normalize, value), repeat=True
            )
        else:
            self.move_timer = None

        self._move(value)
        bs.timer(0.02, bs.CallStrict(self._check_move, value)) # Prevent the node still doesn't move

    def delete(self):
        self.reset_input()
        self.move_timer = None
        self._normalize_position_timer = None
        if self.owner is not None and self.owner.attached_paddle is self:
            self.owner.attached_paddle = None
        self.owner = None
        self.attached_ball = None
        if self.node:
            self.node.delete(True)
        if self.ball_math_node:
            self.ball_math_node.delete(True)
            self.ball_math_node = None
        if self.region_node:
            self.region_node.delete(True)
            self.region_node = None
        if self.region_math_node:
            self.region_math_node.delete(True)
            self.region_math_node = None
        if self.locator_node:
            self.locator_node.delete(True)
            self.locator_node = None

    def _move(self, value: float):
        if value > 0:
            direction = bs.Vec3(value, 0, 0) * self.speed
            if not self.node.velocity[0]:
                self._impulse(direction)

            self.node.velocity = direction
            self.node.position = (self.node.position[0], self.initial_y_pos, self.initial_z_pos)
        elif value < 0:
            direction = bs.Vec3(value, 0, 0) * self.speed
            if not self.node.velocity[0]:
                self._impulse(direction)

            self.node.velocity = direction
            self.node.position = (self.node.position[0], self.initial_y_pos, self.initial_z_pos)

        elif value == 0:
            self.node.velocity = (0, 0, 0)
            self.node.position = (self.node.position[0], self.initial_y_pos, self.initial_z_pos)

    def _normalize_position(self):
        self.node.velocity = (self.node.velocity[0], 0, 0)
        self.node.position = (self.node.position[0], self.initial_y_pos, self.initial_z_pos)

    def _check_move(self, value: float):
        if not all(self.node.velocity):
            direction = bs.Vec3(value, 0, 0) * self.speed
            self._impulse(direction)
            self._move(value)

    def _impulse(self, direction: bs.Vec3):
        # We should impulse the node if its sleeping💤
        self.node.handlemessage(
            "impulse",
            self.node.position[0],  # posX
            self.node.position[1],  # posY
            self.node.position[2],  # posZ
            direction.x * 0.1,  # velocityX
            0.0,                # velocityY
            direction.z * 0.1,  # velocityZ
            0.1,  # magnitude
            0.1,  # velocity_magnitude
            0,  # radius
            0,  # knockback
            direction.x,  # force_directionX
            direction.y,  # force_directionY
            direction.z   # force_directionZ
        )

    def _normalize(self, value: float):
        if value > 0:
            if self.node.position[0] >= self.max_pos_offset:
                self.node.velocity = (0, 0, 0)
        else:
            if self.node.position[0] <= -self.max_pos_offset:
                self.node.velocity = (0, 0, 0)

    def _move_old(self, value: float):
        if value > 0:
            if self.node.position[0] >= self.max_pos_offset:
                return
            self.node.position = (self.node.position[0]+self.speed*0.1, self.initial_y_pos, self.initial_z_pos)
        else:
            if self.node.position[0] <= -self.max_pos_offset:
                return
            self.node.position = (self.node.position[0]-self.speed*0.1, self.initial_y_pos, self.initial_z_pos)
        self.node.velocity = (0, 0, 0)


class Ball(bs.Actor):
    def __init__(self, position: tuple[float, float, float] = (0, 0.3, 0)):
        super().__init__()
        self.velocity = (0, 0, 0)
        self.speed = 5
        self.initial_speed = self.speed

        self.last_player_hit_time = bs.time()

        self.bounced = 0
        self.bounced_wall = 0

        self.initial_y_pos = position[1]

        self.activity: FluffysGame6_SB
        self.initial_gravity_scale = 0

        self.last_player_hit: Player | None = None
        self._spark_timer: bs.Timer | None = None

        mesh = bs.getmesh('shield')
        self.node = bs.newnode('prop',
            delegate=self,
            attrs={
                'position': position,
                'mesh': mesh,
                'light_mesh': mesh,
                'color_texture': bs.gettexture('touchArrowsActions'),
                'mesh_scale': 0.25,
                'body': 'sphere',
                'body_scale': 0.8,
                'density': 0,
                'reflection': 'soft',
                'reflection_scale': [0.1],
                'gravity_scale': self.initial_gravity_scale,
                'is_area_of_interest': True,
                'materials': [self.activity.ball_material, self.activity.shared.object_material]
            }
        )
        self._normalize_position()
        self._add_sparks()

    def start_normalize_velocity(self):
        self._normalize_velocity()
        self.normalize_velocity_timer = bs.Timer(
            0.05, bs.WeakCallStrict(self._normalize_velocity), repeat=True
        )

    def start_normalize_position(self):
        self._normalize_position()
        self.normalize_position_timer = bs.Timer(
            0.2, bs.WeakCallStrict(self._normalize_position), repeat=True
        )

    def stop_normalize_velocity(self):
        self.normalize_velocity_timer = None

    def stop_normalize_position(self):
        self.normalize_position_timer = None

    def aim_player(self, player: Player):
        if not self.node or not self.node.exists() or not player.is_alive():
            return

        direction = (babase.Vec3(player.node.position) - babase.Vec3(self.node.position)).normalized()
        self.node.velocity = (direction * 22.5)
        bs.timer(0.2, bs.WeakCallStrict(self.aim_player, player))

    def slows_ball(self, goal_z_position: float):
        positive_vel = goal_z_position > 0
        def slows():
            if (positive_vel and self.node.velocity[2] <= 0.2) or (not positive_vel and self.node.velocity[2] >= -0.2):
                return

            vel = bs.Vec3(self.node.velocity)
            self.node.velocity = vel.normalized() * 0.75

            #bs.timer(1, slows)
        slows()

    def zero_gravity(self):
        self.node.gravity_scale = 0

    def restore_gravity(self):
        self.node.gravity_scale = self.initial_gravity_scale

    def reset_position(self):
        self.node.position = (0, self.initial_y_pos, 0)

    def reset_velocity(self, delay=2):
        def reset():
            self.node.velocity = (0, 0, 0)
        timer = bs.Timer(0.01, reset, repeat=True)

        def stop():
            nonlocal timer
            timer = None
        bs.timer(delay, stop)

    def reset_speed(self):
        self.speed = self.initial_speed

    def reset(self, reset_speed: bool = True):
        if reset_speed:
            self.reset_speed()
        self.reset_position()
        self.reset_velocity()
        self.restore_gravity()
        self.stop_normalize_position()
        self.bounced_wall = 0

    def launch(self, direction: Sequence[float]):
        """Launch the ball to given direction"""
        velo = self._get_velocity(direction)
        if hasattr(self.node, 'velocity'):
            if not all(self.node.velocity):
                self._impulse(velo)
            self.node.velocity = velo
        else:
            self.node.velocity = velo
            if not all(self.node.velocity):
                self._impulse(velo)
        self.start_normalize_velocity()
        self.start_normalize_position()
    def bounce_wall(self) -> None:
        self.bounced += 1
        if self.speed < 15:
            self.speed += 0.05
        self.bounced_wall += 1
        if self.bounced_wall > 15:
            self.reset(reset_speed=False)
            self._serve_ball()
        #self.bounce()
        #print(f"Ball wall bounced: {self.bounced}")

    def bounce_paddle(self, collision: bs.Collision):
        self.bounced += 1
        if self.speed < 10:
            self.speed += 0.10
        self.bounced_wall = 0
        player = collision.sourcenode.getdelegate(Paddle, True).owner; assert player
        self.last_player_hit = player

        time = bs.time()
        delay = 2 if self.activity.globalsnode.slow_motion else 2*0.3
        if (time - self.last_player_hit_time) > delay:
            self.activity.stats.player_scored(
                player,
                base_points=5,
                screenmessage=False
            )

        self.last_player_hit_time = time
        #self.bounce()
        #print(f"Ball paddle bounced: {self.bounced}")

    def bounce(self):
        self.stop_normalize_velocity()
        bs.timer(0.01, bs.WeakCallStrict(self.start_normalize_velocity))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.delete()
            return None
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.stop_normalize_velocity()
            self.reset()
            bs.timer(1, bs.WeakCallStrict(self._serve_ball))
        else:
            return super().handlemessage(msg)

    def delete(self):
        self.normalize_velocity_timer = None
        self.normalize_position_timer = None
        self._spark_timer = None
        self.last_player_hit = None
        if self.node:
            self.node.delete(True)

    def _impulse(self, direction: bs.Vec3):
        # We should impulse the node if its sleeping💤
        self.node.handlemessage(
            "impulse",
            self.node.position[0],  # posX
            self.node.position[1],  # posY
            self.node.position[2],  # posZ
            direction.x * 0.01,  # velocityX
            direction.y * 0.01,  # velocityY
            direction.z * 0.01,  # velocityZ
            0.0,  # magnitude
            0.0,  # velocity_magnitude
            0,  # radius
            0,  # knockback
            direction.x,  # force_directionX
            direction.y,  # force_directionY
            direction.z  # force_directionZ
        )

    def _normalize_velocity(self):
        vel = self.node.velocity
        direction = bs.Vec3((vel[0], 0, vel[2])).normalized()

        self.node.velocity = (direction * self.speed)

    def _normalize_position(self):
        self.node.position = (self.node.position[0], self.initial_y_pos, self.node.position[2])

    def _serve_ball(self):
        if self.last_player_hit:
            self.activity.serve_ball(self.last_player_hit)
        else:
            self.activity.serve_ball(random.choice(self.activity.get_active_players()))

    def _add_sparks(self):
        delay = 0.075
        self._emit_sparks()
        self._spark_timer = bs.Timer(
            delay, bs.WeakCallStrict(self._emit_sparks), repeat=True
        )

    def _emit_sparks(self):
        if not self.node or not self.node.exists():
            return

        bs.emitfx(
            position=self.node.position,
            velocity=(
                -self.node.velocity[0]*0.65,
                0,
                -self.node.velocity[2]*0.65
            ),
            count=random.randint(50, 75),
            scale=random.random(),
            spread=0.05,
            chunk_type='spark'
        )

    def _get_velocity(self, direction: Sequence[float]):
        return bs.Vec3((direction[0], 0, direction[2])).normalized() * self.speed
"""################################ Game Utils ################################"""

# After a mental breakdown
