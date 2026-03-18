"""Made by Sebaman2009"""

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor import powerupbox
from bascenev1lib.actor.playerspaz import PlayerSpaz, PlayerSpazHurtMessage
from bascenev1lib.actor.powerupbox import PowerupBox
from bascenev1lib.game.elimination import Icon

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any
session = ''


class LivesRemaining(bs.Actor):
    def __init__(self, team):
        super().__init__()
        self.team = team
        self.teamcolor = team.color
        self.bar_posx = (
            -100 - 120
            if isinstance(session, bs.DualTeamSession) == True
            else 85 - 120
        )
        self._height = 35
        self._width = 70
        self._bar_tex = self._backing_tex = bs.gettexture('bar')
        self._cover_tex = bs.gettexture('uiAtlas')
        self._mesh = bs.getmesh('meterTransparent')
        self._backing = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'position': (
                        (self.bar_posx + self._width / 2, -35)
                        if self.team.id == 0
                        or isinstance(session, bs.DualTeamSession) == False
                        else (-self.bar_posx + -self._width / 2, -35)
                    ),
                    'scale': (self._width, self._height),
                    'opacity': 0.7,
                    'color': (
                        self.teamcolor[0] * 0.2,
                        self.teamcolor[1] * 0.2,
                        self.teamcolor[2] * 0.2,
                    ),
                    'vr_depth': -3,
                    'attach': 'topCenter',
                    'texture': self._backing_tex,
                },
            )
        )
        self._cover = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'position': (
                        (self.bar_posx + 35, -35)
                        if self.team.id == 0
                        or isinstance(session, bs.DualTeamSession) == False
                        else (-self.bar_posx - 35, -35)
                    ),
                    'scale': (self._width * 1.15, self._height * 1.6),
                    'opacity': 1.0,
                    'color': (
                        self.teamcolor[0] * 1.1,
                        self.teamcolor[1] * 1.1,
                        self.teamcolor[2] * 1.1,
                    ),
                    'vr_depth': 2,
                    'attach': 'topCenter',
                    'texture': self._cover_tex,
                    'mesh_transparent': self._mesh,
                },
            )
        )
        self._score_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'position': (
                        (self.bar_posx + 35, -35)
                        if self.team.id == 0
                        or isinstance(session, bs.DualTeamSession) == False
                        else (-self.bar_posx - 35, -35)
                    ),
                    'h_attach': 'center',
                    'v_attach': 'top',
                    'h_align': 'center',
                    'v_align': 'center',
                    'maxwidth': 130,
                    'scale': 0.9,
                    'text': '',
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'color': (1.00, 1.00, 1.00, 0.8),
                },
            )
        )

    def update_text(self, num, color=(1, 1, 1, 0.8)):
        text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'position': (
                        (self.bar_posx + 35, -35)
                        if self.team.id == 0
                        or isinstance(session, bs.DualTeamSession) == False
                        else (-self.bar_posx - 35, -35)
                    ),
                    'h_attach': 'center',
                    'v_attach': 'top',
                    'h_align': 'center',
                    'v_align': 'center',
                    'maxwidth': 130,
                    'scale': 0.9,
                    'text': str(num),
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'color': color,
                },
            )
        )
        return text

    def flick(self):
        bs.animate(
            self._score_text.node,
            'opacity',
            {
                0.00: 1.0,
                0.05: 0.0,
                0.10: 1.0,
                0.15: 0.2,
                0.20: 1.0,
            },
        )

    def flick_two(self):
        bs.animate(
            self._score_text.node,
            'opacity',
            {
                0.00: 1.0,
                0.05: 0.0,
                0.10: 1.0,
            },
        )


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.jagg_light: bs.NodeActor | None = None
        self.lives = 1
        self.icon = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0
        self.survival_seconds = 0


lista = []


# ba_meta export bascenev1.GameActivity
class Jaggernaut(bs.TeamGameActivity[Player, Team]):
    name = 'Jaggernaut'
    description = 'Kill the jagger!.'
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.SECONDS
    )

    # Print messages when players die since it matters here.
    announce_player_deaths = True
    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
        cls, sessiontype: Type[bs.Session]
    ) -> List[babase.Setting]:
        settings = [
            bs.IntChoiceSetting(
                "Jaggers's Health",
                choices=[
                    ('Normal (1x)', 1000),
                    ('Stronger (1.5x)', 1500),
                    ('Much Stronger (2x)', 2000),
                ],
                default=1000,
            ),
            bs.IntChoiceSetting(
                "Jaggers's Bombs",
                choices=[
                    ('Normal', 1),
                    ('Double', 2),
                    ('Triple', 3),
                ],
                default=3,
            ),
            bs.BoolSetting('Jagger has boxing gloves', default=False),
            bs.BoolSetting('Spawn powerups', default=True),
            bs.BoolSetting('Epic Mode', default=False),
        ]

        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.FreeForAllSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
        self.boxing = bool(settings['Jagger has boxing gloves'])
        self.health = int(settings["Jaggers's Health"])
        self.bombs = int(settings["Jaggers's Bombs"])
        self.powerups = bool(settings['Spawn powerups'])

        # Base class overrides.
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.TO_THE_DEATH
        )
        self.player_count = len(bs.getactivity().players)

    def get_instance_description(self) -> Union[str, Sequence]:
        return (
            'Kill the titan!'
            if isinstance(self.session, bs.DualTeamSession) == False
            else 'Kill the oposing titan!'
        )

    def get_instance_description_short(self) -> Union[str, Sequence]:
        return (
            f'Kill {self.jagg.team.name}!'
            if isinstance(self.session, bs.DualTeamSession) == False
            else 'Kill the oposing titan!'
        )

    def tick(self) -> None:
        if self.powerups:
            factory = powerupbox.PowerupBoxFactory()
            powerup = factory.get_random_powerup_type(
                excludetypes=['ice_bombs', 'curse', 'health']
            )
            lugar = random.choice(self.map.powerup_spawn_points)
            PowerupBox((lugar[0], lugar[1], lugar[2]), powerup).autoretain()

    def dissapear(self):
        if isinstance(self.session, bs.DualTeamSession) == True:
            bs.animate(
                self.jagg.icon.node,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 0.2,
                    0.55: 1.0,
                    0.60: 0.0,
                    0.65: 0.2,
                    0.70: 1.0,
                    0.75: 0.0,
                    0.80: 0.2,
                    0.85: 1.0,
                    0.90: 0.0,
                    0.95: 0.2,
                    1.00: 0,
                },
            )
            bs.animate(
                self.jagg.icon._name_text,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 0.2,
                    0.55: 1.0,
                    0.60: 0.0,
                    0.65: 0.2,
                    0.70: 1.0,
                    0.75: 0.0,
                    0.80: 0.2,
                    0.85: 1.0,
                    0.90: 0.0,
                    0.95: 0.2,
                    1.00: 0,
                },
            )
            bs.animate(
                self.jag.icon.node,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 0.2,
                    0.55: 1.0,
                    0.60: 0.0,
                    0.65: 0.2,
                    0.70: 1.0,
                    0.75: 0.0,
                    0.80: 0.2,
                    0.85: 1.0,
                    0.90: 0.0,
                    0.95: 0.2,
                    1.00: 0,
                },
            )
            bs.animate(
                self.jag.icon._name_text,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 0.2,
                    0.55: 1.0,
                    0.60: 0.0,
                    0.65: 0.2,
                    0.70: 1.0,
                    0.75: 0.0,
                    0.80: 0.2,
                    0.85: 1.0,
                    0.90: 0.0,
                    0.95: 0.2,
                    1.00: 0,
                },
            )
        else:
            bs.animate(
                self.jagg.icon.node,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 0.2,
                    0.55: 1.0,
                    0.60: 0.0,
                    0.65: 0.2,
                    0.70: 1.0,
                    0.75: 0.0,
                    0.80: 0.2,
                    0.85: 1.0,
                    0.90: 0.0,
                    0.95: 0.2,
                    1.00: 0,
                },
            )
            bs.animate(
                self.jagg.icon._name_text,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 0.2,
                    0.55: 1.0,
                    0.60: 0.0,
                    0.65: 0.2,
                    0.70: 1.0,
                    0.75: 0.0,
                    0.80: 0.2,
                    0.85: 1.0,
                    0.90: 0.0,
                    0.95: 0.2,
                    1.00: 0,
                },
            )

    def on_begin(self):
        super().on_begin()
        global session
        session = self.session
        if isinstance(self.session, bs.DualTeamSession) == False:
            powerupbox.DEFAULT_POWERUP_INTERVAL = 12.0
            self._start_time = bs.time()
            jagg = random.choice(bs.getactivity().players)
            self.player_count = len(bs.getactivity().players)
            jaggy = jagg.actor
            jaggy.hitpoints = self.health * len(bs.getactivity().players)
            jaggy.hitpoints_max = self.health * len(bs.getactivity().players)
            if self.boxing:
                jaggy.equip_boxing_gloves()
            jaggy.set_score_text('Jaggernaut')
            jaggy.bomb_count = 3
            bs.timer(12.0, self.tick, True)
            color = [
                0.3 + c * 0.7 for c in bs.normalized_color(jagg.team.color)
            ]
            light = jaggy.jagg_light = bs.NodeActor(
                bs.newnode(
                    'light',
                    attrs={
                        'intensity': 0.6,
                        'height_attenuated': False,
                        'volume_intensity_scale': 0.1,
                        'radius': 0.13,
                        'color': color,
                    },
                )
            )
            assert isinstance(jaggy, PlayerSpaz)
            jaggy.node.connectattr('position', light.node, 'position')
            self.jagg = jagg
            self.jaggy = jaggy
            self.jagg.icon = Icon(
                player=self.jagg, position=(0, 550), scale=1.0, show_lives=False
            )
            self.text_jagg = LivesRemaining(self.jagg.team)
            self.text_jagg.position = 0 - 120
            self.text_jagg._score_text = self.text_jagg.update_text(
                round(self.jaggy.hitpoints // 10)
            )
            bs.timer(8.0, self.dissapear)
            return jaggy
        else:
            powerupbox.DEFAULT_POWERUP_INTERVAL = 12.0
            self._start_time = bs.time()
            alive = self._get_living_teams()
            print(alive)
            self.jagg = random.choice(alive[0].players)
            self.jag = random.choice(alive[1].players)
            self.jaggy = self.jagg.actor
            self.jagy = self.jag.actor
            self.jaggy.hitpoints = self.health * len(bs.getactivity().players)
            self.jaggy.hitpoints_max = self.health * len(
                bs.getactivity().players
            )
            self.jagy.hitpoints = self.health * len(bs.getactivity().players)
            self.jagy.hitpoints_max = self.health * len(
                bs.getactivity().players
            )
            if self.boxing:
                self.jaggy.equip_boxing_gloves()
                self.jagy.equip_boxing_gloves()
            self.jaggy.set_score_text('Jaggernaut', self.jagg.color)
            self.jagy.set_score_text('Jaggernaut', self.jag.color)
            self.jaggy.bomb_count = 3
            self.jagy.bomb_count = 3
            bs.timer(12.0, self.tick, True)
            color1 = [
                0.3 + c * 0.7 for c in bs.normalized_color(self.jagg.team.color)
            ]
            light1 = self.jaggy.jagg_light = bs.NodeActor(
                bs.newnode(
                    'light',
                    attrs={
                        'intensity': 0.6,
                        'height_attenuated': False,
                        'volume_intensity_scale': 0.1,
                        'radius': 0.13,
                        'color': color1,
                    },
                )
            )
            assert isinstance(self.jaggy, PlayerSpaz)
            self.jaggy.node.connectattr('position', light1.node, 'position')
            color2 = [
                0.3 + c * 0.7 for c in bs.normalized_color(self.jag.team.color)
            ]
            light2 = self.jagy.jagg_light = bs.NodeActor(
                bs.newnode(
                    'light',
                    attrs={
                        'intensity': 0.6,
                        'height_attenuated': False,
                        'volume_intensity_scale': 0.1,
                        'radius': 0.13,
                        'color': color2,
                    },
                )
            )
            assert isinstance(self.jagy, PlayerSpaz)
            self.jagy.node.connectattr('position', light2.node, 'position')
            self.jagg.icon = Icon(
                player=self.jagg,
                position=(-185, 550),
                scale=1.0,
                show_lives=False,
            )
            self.jag.icon = Icon(
                player=self.jag,
                position=(185, 550),
                scale=1.0,
                show_lives=False,
            )
            self.text_jagg = LivesRemaining(self.jagg.team)
            self.text_jag = LivesRemaining(self.jag.team)
            self.text_jagg._score_text = self.text_jagg.update_text(
                round(self.jaggy.hitpoints // 10)
            )
            self.text_jag._score_text = self.text_jag.update_text(
                round(self.jagy.hitpoints // 10)
            )
            bs.timer(8.0, self.dissapear)

    def on_player_join(self, player):
        self.spawn_player(player)

    def on_player_leave(self, player):
        self.player_count -= 1
        if player == self.jagg:
            self.end_game()
        alive_teams = self._get_living_teams()
        if len(alive_teams) == 1:
            for team in alive_teams:
                team.survival_seconds += int(bs.time() - self._start_time)
            self.end_game()

    def _get_living_teams(self) -> list[Team]:
        return [
            team
            for team in self.teams
            if len(team.players) > 0
            and any(player.lives > 0 for player in team.players)
        ]

    def check_win(self):
        alive_teams = self._get_living_teams()
        if self.player_count == 0:
            self.end_game()
        elif (
            self.msg.getkillerplayer(Player) == self.jagg
            and self.msg.getplayer(Player) == self.jagg
        ):
            self.msg.getkillerplayer(Player).team.survival_seconds = 0
            for team in alive_teams:
                team.survival_seconds += int(bs.time() - self._start_time)
            self.end_game()
        elif self.msg.getplayer(Player) == self.jagg:
            self.msg.getkillerplayer(Player).team.survival_seconds += 1
            self.jagg.team.survival_seconds = 0
            for team in alive_teams:
                team.survival_seconds += int(bs.time() - self._start_time)
            self.end_game()
        elif self.player_count == 1:
            self.jagg.team.survival_seconds += int(bs.time() - self._start_time)
            self.end_game()

    def check_win_teams(self):
        if (
            self.player_count == 0
            or self.jagy.is_alive() == False
            and self.jaggy.is_alive() == False
        ):
            self.end_game()
        elif (
            self.msg.getplayer(Player) == self.jagg
            or self.msg.getplayer(Player) == self.jag
        ):
            self.msg.getplayer(Player).team.score -= 1
            self.end_game()

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            msg.getplayer(Player).team.survival_seconds += int(
                bs.time() - self._start_time
            )
            msg.getplayer(Player).lives -= 1
            self.player_count -= 1
            self.msg = msg
            if msg.getplayer(Player).actor == self.jaggy:
                self.jaggy.jagg_light = None
                self.text_jagg._score_text = self.text_jagg.update_text(
                    0, (1.00, 0.15, 0.15)
                )
            if isinstance(self.session, bs.DualTeamSession) == True:
                if msg.getplayer(Player).actor == self.jagy:
                    self.jagy.jagg_light = None
                    self.text_jag._score_text = self.text_jag.update_text(
                        0, (1.00, 0.15, 0.15)
                    )
            if isinstance(self.session, bs.DualTeamSession) == False:
                bs.timer(1.0, self.check_win)
            else:
                bs.timer(1.0, self.check_win_teams)
        if isinstance(msg, PlayerSpazHurtMessage):
            if isinstance(self.session, bs.DualTeamSession) == True:
                if msg.spaz == self.jaggy:
                    self.text_jagg._score_text = self.text_jagg.update_text(
                        round(self.jaggy.hitpoints // 10)
                    )
                    self.text_jagg.flick()
                    if self.jaggy.hitpoints == 0:
                        self.text_jagg._score_text = self.text_jagg.update_text(
                            round(self.jaggy.hitpoints // 10),
                            (1.00, 0.15, 0.15),
                        )
                        self.timertwo = None
                    elif self.jaggy.hitpoints <= (
                        self.jaggy.hitpoints_max // 4
                    ):
                        self.text_jagg._score_text = self.text_jagg.update_text(
                            round(self.jaggy.hitpoints // 10),
                            (1.00, 0.15, 0.15),
                        )
                        self.timertwo = None
                        self.timertwo = bs.Timer(
                            0.1, self.text_jagg.flick_two, True
                        )
                    elif self.jaggy.hitpoints <= (
                        self.jaggy.hitpoints_max // 2
                    ):
                        self.text_jagg._score_text = self.text_jagg.update_text(
                            round(self.jaggy.hitpoints // 10),
                            (1.00, 0.50, 0.00),
                        )
                        self.text_jagg.flick()
                elif msg.spaz == self.jagy:
                    self.text_jag._score_text = self.text_jag.update_text(
                        round(self.jagy.hitpoints // 10)
                    )
                    self.text_jag.flick()
                    if self.jagy.hitpoints == 0:
                        self.text_jag._score_text = self.text_jag.update_text(
                            round(self.jagy.hitpoints // 10), (1.00, 0.15, 0.15)
                        )
                        self.timer = None
                    elif self.jagy.hitpoints <= (self.jagy.hitpoints_max // 4):
                        self.text_jag._score_text = self.text_jag.update_text(
                            round(self.jagy.hitpoints // 10), (1.00, 0.15, 0.15)
                        )
                        self.timer = None
                        self.timer = bs.Timer(
                            0.1, self.text_jag.flick_two, True
                        )
                    elif self.jagy.hitpoints <= (self.jagy.hitpoints_max // 2):
                        self.text_jag._score_text = self.text_jag.update_text(
                            round(self.jagy.hitpoints // 10), (1.00, 0.50, 0.00)
                        )
                        self.text_jag.flick()
            elif msg.spaz == self.jaggy:
                self.text_jagg._score_text = self.text_jagg.update_text(
                    round(self.jaggy.hitpoints // 10)
                )
                self.text_jagg.flick()
                if self.jaggy.hitpoints == 0:
                    self.text_jagg._score_text = self.text_jagg.update_text(
                        round(self.jaggy.hitpoints // 10), (1.00, 0.15, 0.15)
                    )
                    self.timer = None
                elif self.jaggy.hitpoints <= (self.jaggy.hitpoints_max // 4):
                    self.text_jagg._score_text = self.text_jagg.update_text(
                        round(self.jaggy.hitpoints // 10), (1.00, 0.15, 0.15)
                    )
                    self.timer = None
                    self.timer = bs.Timer(0.1, self.text_jagg.flick_two, True)
                elif self.jaggy.hitpoints <= (self.jaggy.hitpoints_max // 2):
                    self.text_jagg._score_text = self.text_jagg.update_text(
                        round(self.jaggy.hitpoints // 10), (1.00, 0.50, 0.00)
                    )
                    self.text_jagg.flick()

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            if isinstance(self.session, bs.DualTeamSession) == False:
                results.set_team_score(team, team.survival_seconds)
            else:
                results.set_team_score(team, team.score)
        self.end(results=results)
