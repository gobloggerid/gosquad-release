"""BombSquad Game by Jetz"""


# ba_meta require api 9

from __future__ import annotations
from typing import TYPE_CHECKING

import bascenev1 as ba
import random
from bascenev1lib.actor.bomb import Blast
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Type, List, Sequence, Optional


class Egg(ba.Actor):
    """A tiny egg that it will burst"""
    
    def __init__(self,
                 position: Sequence[float] = (0, 1, 0),
                 velocity: Sequence[float] = (0, 0, 0)):
        super().__init__()
        activity = self.activity
        assert isinstance(activity, EggOfDeathGame)
        shared = SharedObjects.get()
        
        self.position = position
        self.velocity = velocity
        
        model = ba.getmesh('egg')
        tex = ba.gettexture('eggTex1')
        
        self.egg_material = ba.Material()
        self.player_egg_material = ba.Material()
        
        self.egg_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False))
        self.player_egg_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=('call', 'at_connect', activity._on_egg_player_collide))
        
        materials = [shared.footing_material,
                     shared.object_material,
                     self.egg_material,
                     self.player_egg_material]
        
        self.node = ba.newnode(
            'prop',
            delegate=self,
            attrs={
                'position': self.position,
                'velocity': self.velocity,
                'mesh': model,
                'color_texture': tex,
                'body': 'capsule',
                'mesh_scale': 0.7,
                'body_scale': 0.9,
                'damping': 999999999999999999999999,
                'flashing': True,
                'shadow_size': 0.5,
                'materials': materials
            })
    
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
            Egg(position=self.position,
                velocity=self.velocity).autoretain()
        elif isinstance(msg, ba.HitMessage):
            self.node.handlemessage('impulse',
                                    msg.pos[0], msg.pos[1], msg.pos[2],
                                    msg.velocity[0], msg.velocity[1], msg.velocity[2],
                                    msg.magnitude, msg.velocity_magnitude, msg.radius, 0,
                                    msg.velocity[0], msg.velocity[1], msg.velocity[2])
        else:
            super().handlemessage(msg)


class Player(ba.Player['Team']):
    """Our player type for this game."""


class Team(ba.Team[Player]):
    """Our team type for this game."""
    
    def __init__(self):
        self.score = 0


# ba_meta export bascenev1.GameActivity
class EggOfDeathGame(ba.TeamGameActivity[Player, Team]):
    """Be careful! The egg is deadly!"""
    
    name = 'Egg Of Death'
    description = 'Touch the deadly egg first before the others.'
    available_settings = [
        ba.IntSetting('Score to Win', min_value=1, default=5, increment=1),
        ba.IntChoiceSetting(
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
        ba.FloatChoiceSetting(
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
        ba.BoolSetting('Epic Mode', default=False),
    ]
    
    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ['Football Stadium']
    
    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.FreeForAllSession)
                or issubclass(sessiontype, ba.DualTeamSession))
    
    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._time_limit = float(settings['Time Limit'])
        self._score_to_win = int(settings['Score to Win'])
        self._epic_mode = bool(settings['Epic Mode'])
        
        if self._epic_mode:
            self.slow_motion = True
        self.default_music = (ba.MusicType.EPIC if self._epic_mode else ba.MusicType.ONSLAUGHT)
    
    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()
    
    def spawn_player(self, player: Player) -> None:
        spaz = self.spawn_player_spaz(player, position=(random.choice([-11, 11]), 1.2, random.uniform(-5, 5)), angle=90)
        return spaz
    
    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self._spawn_egg()
        
        assert self._score_to_win is not None
        if any(team.score >= self._score_to_win for team in self.teams):
            ba.timer(0.5, self.end_game)
    
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ba.PlayerDiedMessage):
            self.respawn_player(msg.getplayer(Player))
        else:
            return super().handlemessage(msg)
        return None
    
    def _on_egg_player_collide(self) -> None:
        if self.has_ended():
            return
        collision = ba.getcollision()
        
        try:
            egg = collision.sourcenode.getdelegate(Egg, True)
            player = collision.opposingnode.getdelegate(PlayerSpaz,
                                                        True).getplayer(
                                                            Player, True)
            node = collision.opposingnode
        
        except ba.NotFoundError:
            return
        
        player.team.score += 1
        self.stats.player_scored(player, 1, screenmessage=False)
        Blast(position=egg.position,
              blast_radius=100.0,
              blast_type='tnt')
        PopupText(
                    position=(-0.0, -2.5, -3.5),
                    text='FAAAAAAAAAAAAAAAAAAAAAHHHHHHH!',
                    random_offset=0.0,
                    scale=5.0,
                    color=(1, 0, 0),
                ).autoretain()
        node.handlemessage(ba.StandMessage(position=(random.choice([-11, 11]), 20.2, random.uniform(-5, 5)),
                                           angle=90))

        self._update_scoreboard()
        
        assert self._score_to_win is not None
        if any(team.score >= self._score_to_win for team in self.teams):
            ba.timer(0.5, self.end_game)
    
    def _spawn_egg(self) -> None:
        Egg(position=(0, 1.0, 0),
            velocity=(0, 0, 0))
    
    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score,
                                            self._score_to_win)
    
    def end_game(self) -> None:
        results = ba.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)