"""Made by: Sebaman2009"""

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _bascenev1
import babase
import bascenev1 as bs
from bascenev1lib.actor.playerspaz import PlayerSpaz, PlayerSpazHurtMessage
from bascenev1lib.game.elimination import Icon

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class LivesRemaining(bs.Actor):
    def __init__(self, team):
        super().__init__()
        self.team = team
        self.teamcolor = team.color
        self.bar_posx = -100 - 120
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
                        if team.id == 0
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
                        if team.id == 0
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
                        if team.id == 0
                        else (-self.bar_posx - 35, -35)
                    ),
                    'h_attach': 'center',
                    'v_attach': 'top',
                    'h_align': 'center',
                    'v_align': 'center',
                    'maxwidth': 130,
                    'scale': 0.9,
                    'text': str(len(self.team.players)),
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'color': (1, 1, 1, 0.8),
                },
            )
        )

    def update_text(self, num):
        text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'position': (
                        (self.bar_posx + 35, -35)
                        if self.team.id == 0
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
                    'color': (1, 1, 1, 0.8),
                },
            )
        )
        return text

    def flick(self):
        _bascenev1.Sound.play(bs.getsound('shieldDown'))
        bs.animate(
            self._score_text.node,
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
                1.00: 1.0,
            },
        )


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.tag_light: bs.NodeActor | None = None
        self.lives = 1
        self.time = 0


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0
        self.survival_seconds = 0


lista = []


# ba_meta export bascenev1.GameActivity
class Tag(bs.TeamGameActivity[Player, Team]):
    """A game type based on acquiring kills."""

    name = 'Tag'
    description = "Don't get caught!"
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.SECONDS
    )

    # Print messages when players die since it matters here.
    allow_mid_activity_joins = False
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
        cls, sessiontype: Type[bs.Session]
    ) -> List[babase.Setting]:
        settings = [
            bs.IntChoiceSetting(
                'Tag time',
                choices=[
                    ('Shorter', 15),
                    ('Normal', 20),
                    ('Longer', 25),
                ],
                default=20,
            ),
            bs.BoolSetting('Epic Mode', default=False),
            bs.BoolSetting('Disable Bombs', default=False),
            bs.BoolSetting('Disable Pickup', default=False),
            bs.BoolSetting('Tag explodes when time ends', default=True),
        ]

        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._dingsound = bs.getsound('dingSmall')
        self.tag_length = int(settings['Tag time'])
        self._epic_mode = bool(settings['Epic Mode'])
        self.bombs = bool(settings['Disable Bombs'])
        self.grab = bool(settings['Disable Pickup'])
        self.explode = bool(settings['Tag explodes when time ends'])
        self.alive_teams = [
            team
            for team in self.teams
            if len(team.players) > 0
            and any(player.lives > 0 for player in team.players)
        ]
        self.ended = False
        # Base class overrides.
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.RACE
        )
        self.tag = ''
        self.tag_act = ''
        self.time = self.tag_length
        self._countdownsounds: dict[int, bs.Sound] = {
            10: bs.getsound('announceTen'),
            9: bs.getsound('announceNine'),
            8: bs.getsound('announceEight'),
            7: bs.getsound('announceSeven'),
            6: bs.getsound('announceSix'),
            5: bs.getsound('announceFive'),
            4: bs.getsound('announceFour'),
            3: bs.getsound('announceThree'),
            2: bs.getsound('announceTwo'),
            1: bs.getsound('announceOne'),
        }
        self.slow_motion = self._epic_mode

    def get_instance_description(self) -> Union[str, Sequence]:
        return "Don't get tagged!"

    def get_instance_description_short(self) -> Union[str, Sequence]:
        return "Don't get tagged!"

    def tick(self):
        self.time -= 1
        if self.time == 0:
            if self.explode == True:
                self.tag_act.curse_time = 0.000000000000000000001
                self.tag_act.curse()
            else:
                self.tag_act.handlemessage(bs.DieMessage())
        if self.time in self._countdownsounds:
            self._countdownsounds[self.time].play()
            self.tag_act.set_score_text(f'{self.time}', self.color, True)
        else:
            self.tag_act.set_score_text(f'{self.time}', self.color)

    def select_tag(self):
        alive = self._get_living_teams()
        print(alive)
        self.tag = random.choice(alive) if alive else self.end_game()
        self.player_count = len(bs.getactivity().players)
        self.tag_act = self.tag.actor
        self.tag_act.invincible = True
        self.tag_act.set_score_text('Tag')
        self.color = [
            0.3 + c * 0.7 for c in bs.normalized_color(self.tag.team.color)
        ]
        light = self.tag_act.tag_light = bs.NodeActor(
            bs.newnode(
                'light',
                attrs={
                    'intensity': 0.6,
                    'height_attenuated': False,
                    'volume_intensity_scale': 0.1,
                    'radius': 0.13,
                    'color': self.color,
                },
            )
        )
        assert isinstance(self.tag_act, PlayerSpaz)
        self.tag_act.node.connectattr('position', light.node, 'position')
        self.cuenta = bs.Timer(1.0, call=self.tick, repeat=True)

    def flick(self):
        bs.animate(
            self.icon.node,
            'opacity',
            {
                0.00: 1.0,
                0.05: 0.0,
                0.10: 1.0,
                0.15: 0.2,
                0.20: 1.0,
                0.25: 0.0,
                0.30: 1.0,
            },
        )
        bs.animate(
            self.icon._name_text,
            'opacity',
            {
                0.00: 1.0,
                0.05: 0.0,
                0.10: 1.0,
                0.15: 0.2,
                0.20: 1.0,
                0.25: 0.0,
                0.30: 1.0,
            },
        )

    def on_begin(self):
        super().on_begin()
        if len(bs.getactivity().players) == 1:
            self.end_game()
        if isinstance(self.session, bs.DualTeamSession) == True:
            self.team_one_bar = LivesRemaining(self.teams[0])
            self.team_two_bar = LivesRemaining(self.teams[1])
        self._start_time = bs.time()
        self.select_tag()
        self.icon = Icon(
            player=self.tag, position=(0, 600), scale=1.0, show_lives=False
        )
        players = self._get_living_teams()
        for player in players:
            actor = player.actor
            actor.hitpoints = 20000000000000000000000000000000000
            actor.hitpoints_max = 20000000000000000000000000000000000
            if self.bombs == True and self.grab == True:
                actor.disconnect_controls_from_player()
                actor.connect_controls_to_player(
                    enable_bomb=False, enable_pickup=False
                )
            elif self.bombs == True and self.grab == False:
                actor.disconnect_controls_from_player()
                actor.connect_controls_to_player(enable_bomb=False)
            elif self.bombs == False and self.grab == True:
                actor.disconnect_controls_from_player()
                actor.connect_controls_to_player(enable_grab=False)
            else:
                pass

    def on_player_join(self, player):
        self.spawn_player(player)

    def on_player_leave(self, player):
        self.player_count -= 1
        if player == self.tag:
            self.select_tag()
        if self.check_win() != None:
            alive = self.check_win()
            print(alive)
            alive.survival_seconds += int(bs.time() - self._start_time)
            self.end_game()

    def _get_living_teams(self) -> list[Team]:
        alive = []
        for team in self.teams:
            for player in team.players:
                if player.lives > 0:
                    alive.append(player)
        return alive

    def check_win(self):
        alive_teams = [
            team
            for team in self.teams
            if len(team.players) > 0
            and any(player.lives > 0 for player in team.players)
        ]
        print(alive_teams)
        if len(alive_teams) == 1:
            alive_teams[0].survival_seconds += int(bs.time() - self._start_time)
            for player in alive_teams[0].players:
                player.team.score += 1
            self.end_game()

    def reselect_tag(self):
        if self.ended == False:
            self.select_tag()
            self.icon.node.delete()
            self.icon = Icon(
                player=self.tag, position=(0, 600), scale=1.0, show_lives=False
            )
            self.flick()

    def handlemessage(self, msg: Any) -> Any:
        super().handlemessage(msg)
        if isinstance(msg, bs.PlayerDiedMessage):
            self.player_count -= 1
            msg.getplayer(Player).lives -= 1
            alive_teams = [
                team
                for team in self.teams
                if len(team.players) > 0
                and any(player.lives > 0 for player in team.players)
            ]
            if msg.getplayer(Player).team not in alive_teams:
                msg.getplayer(Player).team.survival_seconds += int(
                    bs.time() - self._start_time
                )
            if isinstance(self.session, bs.DualTeamSession):
                if msg.getplayer(Player).team == self.teams[0]:
                    self.team_one_bar._score_text = (
                        self.team_one_bar.update_text(
                            int(self.team_one_bar._score_text.node.text) - 1
                        )
                    )
                    self.team_one_bar.flick()
                else:
                    self.team_two_bar._score_text = (
                        self.team_two_bar.update_text(
                            int(self.team_two_bar._score_text.node.text) - 1
                        )
                    )
                    self.team_two_bar.flick()
            bs.timer(1.0, self.check_win)
            if msg.getplayer(Player).node == self.tag.node:
                self.cuenta = None
                if self.tag_act:
                    self.tag_act.tag_light = None
                self.time = self.tag_length
                bs.animate(
                    self.icon.node,
                    'opacity',
                    {
                        0.00: 1.0,
                        0.05: 0.5,
                        0.10: 0.3,
                        0.15: 0.2,
                    },
                )
                bs.animate(
                    self.icon._name_text,
                    'opacity',
                    {
                        0.00: 1.0,
                        0.05: 0.5,
                        0.10: 0.3,
                        0.15: 0.2,
                    },
                )
                self.tag_act = None
                bs.timer(2.0, self.reselect_tag)
        elif isinstance(msg, PlayerSpazHurtMessage):
            player = msg.spaz
            player_act = player.getplayer(playertype=Player)
            if player.last_player_attacked_by == self.tag:
                player.last_player_attacked_by = None
                if self.tag_act:
                    self.tag_act.tag_light = None
                self.tag_act = player
                self.tag = self.tag_act.getplayer(playertype=Player)
                self.color = [
                    0.3 + c * 0.7
                    for c in bs.normalized_color(
                        self.tag_act.getplayer(playertype=Player).color
                    )
                ]
                light = self.tag_act.tag_light = bs.NodeActor(
                    bs.newnode(
                        'light',
                        attrs={
                            'intensity': 0.6,
                            'height_attenuated': False,
                            'volume_intensity_scale': 0.1,
                            'radius': 0.13,
                            'color': self.color,
                        },
                    )
                )
                assert isinstance(self.tag_act, PlayerSpaz)
                self.tag_act.node.connectattr(
                    'position', light.node, 'position'
                )
                self.icon.node.delete()
                self.icon = Icon(
                    player=self.tag,
                    position=(0, 600),
                    scale=1.0,
                    show_lives=False,
                )
                self.flick()

    def end_game(self) -> None:
        self.ended = True
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.survival_seconds)
        self.end(results=results)
