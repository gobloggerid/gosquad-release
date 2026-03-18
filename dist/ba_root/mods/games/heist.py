# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import random
import weakref
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor import spawner
from bascenev1lib.actor.bomb import BombFactory, ExplodeHitMessage
from bascenev1lib.actor.powerupbox import PowerupBox
from bascenev1lib.actor.spazbot import ExplodeyBotNoTimeLimit, SpazBotSet
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

MIN_SPHERE_SIZE = 0.01


class Blast(bs.Actor):
    def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        blast_radius: float = 2.0,
        color: Sequence[float] = (0.0, 1.0, 0.0),
    ):
        super().__init__()

        shared = SharedObjects.get()
        factory = BombFactory.get()

        self.radius = max(MIN_SPHERE_SIZE, float(blast_radius))

        rmats = (factory.blast_material, shared.attack_material)
        self.node = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': (position[0], position[1] - 0.1, position[2]),
                'scale': (self.radius, self.radius, self.radius),
                'type': 'sphere',
                'materials': rmats,
            },
        )
        bs.timer(0.05, self.node.delete)

        explosion = bs.newnode(
            'explosion',
            attrs={
                'position': position,
                'radius': self.radius * 0.8,
                'color': (color[0] * 0.3, color[1] * 0.3, color[2] * 0.3),
                'big': True,
            },
        )
        bs.timer(1.0, explosion.delete)

        light = bs.newnode(
            'light',
            attrs={
                'position': position,
                'volume_intensity_scale': 10.0,
                'color': (1, 0.3, 0.1),
            },
        )
        scl = random.uniform(0.6, 0.9) * 3.0
        scorch_radius = self.radius * 1.4
        light_radius = self.radius * 0.6
        iscale = 0.8
        bs.animate(
            light,
            'intensity',
            {
                0: 2.0 * iscale,
                scl * 0.02: 0.1 * iscale,
                scl * 0.025: 0.2 * iscale,
                scl * 0.05: 17.0 * iscale,
                scl * 0.06: 5.0 * iscale,
                scl * 0.08: 4.0 * iscale,
                scl * 0.2: 0.6 * iscale,
                scl * 2.0: 0.00 * iscale,
                scl * 3.0: 0.0,
            },
        )
        bs.animate(
            light,
            'radius',
            {
                0: light_radius * 0.2,
                scl * 0.05: light_radius * 0.55,
                scl * 0.1: light_radius * 0.3,
                scl * 0.3: light_radius * 0.15,
                scl * 1.0: light_radius * 0.05,
            },
        )
        bs.timer(scl * 3.0, light.delete)

        scorch = bs.newnode(
            'scorch',
            attrs={
                'position': position,
                'size': scorch_radius * 0.5,
                'color': (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6),
                'big': True,
            },
        )
        bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
        bs.timer(13.0, scorch.delete)

        lpos = light.position
        factory.random_explode_sound().play(position=lpos)
        factory.random_explode_sound().play(position=lpos)
        factory.debris_fall_sound.play(position=lpos)
        bs.camerashake(intensity=5.0)

        def _extra_boom() -> None:
            factory.random_explode_sound().play(position=lpos)

        bs.timer(0.25, _extra_boom)

        def _extra_debris_sound() -> None:
            factory.debris_fall_sound.play(position=lpos)
            factory.wood_debris_fall_sound.play(position=lpos)

        bs.timer(0.4, _extra_debris_sound)

        #        bs.emitfx(position=position,
        #        count=100,
        #          scale=1.8,
        #       spread=5,
        #           chunk_type='spark')
        #    bs.emitfx(position=position,
        #          count=100,
        #           spread=5,
        #             scale=2,
        #        chunk_type='ice',
        #              emit_type='stickers')
        bs.emitfx(
            position=position,
            count=1000,
            spread=500,
            scale=10,
            chunk_type='slime',
        )

    #    bs.emitfx(position=position,
    #               count=20,
    #           scale=1,
    #            spread=500,
    #          chunk_type='sweat',
    #           emit_type='tendrils')

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired

        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()

        elif isinstance(msg, ExplodeHitMessage):
            node = bs.getcollision().opposingnode
            assert self.node
            nodepos = self.node.position
            mag = 2000.0
            mag *= 2.0

            node.handlemessage(
                bs.HitMessage(
                    pos=nodepos,
                    velocity=(0, 0, 0),
                    magnitude=mag,
                    hit_type='explosion',
                    hit_subtype='normal',
                    radius=self.radius,
                )
            )
        else:
            return super().handlemessage(msg)
        return None


class TNTBox(bs.Actor):
    def __init__(
        self,
        team_id: bs.Team,
        meshtype: float = None,
        position: Sequence[float] = None,
        hitpoints: float = 1000,
        team: str = None,
    ):
        super().__init__()
        shared = SharedObjects.get()
        activity = self.getactivity()
        spaz = SpazFactory.get()

        self.team = weakref.ref(team_id)
        self.meshtype = meshtype
        self.team_str = team
        self.teamcolor = self.team().color
        self.position = position
        self.hitpoints = hitpoints
        self.hitpoints_max = hitpoints
        self._width = 240
        self._width_max = 240
        self._height = 35
        self._bar_width = 240
        self._bar_height = 35
        self._bar_tex = self._backing_tex = bs.gettexture('bar')
        self._cover_tex = bs.gettexture('uiAtlas')
        self._mesh = bs.getmesh('meterTransparent')

        if team == 'team 1':
            self.bar_posx = -200 - 120
        else:
            self.bar_posx = 200 - 120

        self.box_material = bs.Material()
        no_collide_material = bs.Material()
        self.box_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False),
        )

        if meshtype == 1:
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': (position[0], position[1] + 2.5, position[2]),
                    'mesh': bs.getmesh('tnt'),
                    'light_mesh': bs.getmesh('tnt'),
                    'body': 'crate',
                    'body_scale': 3.3,
                    'mesh_scale': 3.35,
                    'shadow_size': 0.3,
                    'color_texture': bs.gettexture('tickets'),
                    'is_area_of_interest': True,
                    'reflection': 'soft',
                    'reflection_scale': [0.23],
                    'materials': [self.box_material, shared.footing_material],
                },
            )
        elif meshtype == 2:
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': (position[0], position[1] + 1.5, position[2]),
                    'mesh': bs.getmesh('tnt'),
                    'light_mesh': bs.getmesh('tnt'),
                    'body': 'crate',
                    'body_scale': 1,
                    'mesh_scale': 1,
                    'shadow_size': 0.3,
                    'color_texture': bs.gettexture('tnt'),
                    'is_area_of_interest': True,
                    'reflection': 'soft',
                    'reflection_scale': [0.23],
                    'materials': [self.box_material, shared.footing_material],
                },
            )
        elif meshtype == 3:
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': (position[0], position[1] + 1.5, position[2]),
                    'mesh': bs.getmesh('puck'),
                    'body': 'puck',
                    'body_scale': 1,
                    'mesh_scale': 1,
                    'shadow_size': 1.0,
                    'color_texture': bs.gettexture('puckColor'),
                    'is_area_of_interest': True,
                    'reflection': 'soft',
                    'reflection_scale': [0.23],
                    'materials': [self.box_material, shared.footing_material],
                },
            )
        elif meshtype == 4:
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': (position[0], position[1] + 1.5, position[2]),
                    'mesh': bs.getmesh('frostyPelvis'),
                    'body': 'sphere',
                    'body_scale': 2.5,
                    'mesh_scale': 2.5,
                    'shadow_size': 0.3,
                    'color_texture': bs.gettexture('frostyColor'),
                    'is_area_of_interest': True,
                    'reflection': 'soft',
                    'reflection_scale': [1.0],
                    'materials': [self.box_material, shared.footing_material],
                },
            )

        bs.animate(
            self.node,
            'mesh_scale',
            {0: 0, 0.2: self.node.mesh_scale * 1.1, 0.26: self.node.mesh_scale},
        )

        light = bs.newnode(
            'light',
            owner=self.node,
            attrs={'radius': 0.28, 'color': self.teamcolor},
        )
        self.node.connectattr('position', light, 'position')

        self._scoreboard()
        self._update()

    def animate_mesh(self) -> None:
        if not self.node:
            return None
        bs.animate(
            self.node,
            'mesh_scale',
            {
                0: self.node.mesh_scale,
                0.08: self.node.mesh_scale * 0.9,
                0.15: self.node.mesh_scale,
            },
        )
        if self.meshtype in [1, 2]:
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(6 + random.random() * 10),
                scale=0.5,
                spread=0.4,
                chunk_type='splinter',
            )
        elif self.meshtype == 3:
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(4 + random.random() * 4),
                scale=0.5,
                spread=0.3,
                chunk_type='metal',
            )
        else:
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=int(4 + random.random() * 4),
                scale=0.5,
                spread=0.3,
                chunk_type='ice',
            )

    def do_damage(self, msg: Any) -> None:
        if not self.node:
            return None
        damage = msg.magnitude
        self.hitpoints -= int(damage)
        if self.hitpoints <= 0:
            self.hitpoints = 0
            Blast(
                position=self.node.position,
                blast_radius=20.0,
                color=self.teamcolor,
            ).autoretain()
            self.node.delete()

    def _update(self) -> None:
        self._score_text.node.text = str(self.hitpoints)
        self._bar_width = self.hitpoints * self._width_max / self.hitpoints_max
        cur_width = self._bar_scale.input0
        bs.animate(
            self._bar_scale, 'input0', {0.0: cur_width, 0.1: self._bar_width}
        )
        cur_x = self._bar_position.input0
        if self.team_str == 'team 1':
            bs.animate(
                self._bar_position,
                'input0',
                {0.0: cur_x, 0.1: self.bar_posx * 0.265 - self._bar_width / 2},
            )
        else:
            bs.animate(
                self._bar_position,
                'input0',
                {0.0: cur_x, 0.1: self.bar_posx + self._bar_width / 2},
            )

    def show_damage_msg(self, msg: Any) -> None:
        if not self.node:
            return None
        damage = msg.magnitude
        self.show_damage_count(
            '-' + str(int(damage)),
            self.node.position,
            (
                msg.force_direction[0] * 0.2,
                msg.force_direction[1] * 0.2,
                msg.force_direction[2] * 0.2,
            ),
        )

    def show_damage_count(
        self, damage: str, position: Sequence[float], direction: Sequence[float]
    ) -> None:
        """Pop up a damage count at a position in space.

        Category: Gameplay Functions
        """
        lifespan = 1.0
        app = babase.app

        # FIXME: Should never vary game elements based on local config.
        #  (connected clients may have differing configs so they won't
        #  get the intended results).
        do_big = app.ui.uiscale is babase.UIScale.SMALL or app.vr_mode
        txtnode = bs.newnode(
            'text',
            attrs={
                'text': damage,
                'in_world': True,
                'h_align': 'center',
                'flatness': 1.0,
                'shadow': 1.0 if do_big else 0.7,
                'color': (1, 0.25, 0.25, 1),
                'scale': 0.035 if do_big else 0.03,
            },
        )
        # Translate upward.
        tcombine = bs.newnode('combine', owner=txtnode, attrs={'size': 3})
        tcombine.connectattr('output', txtnode, 'position')
        v_vals = []
        pval = 0.0
        vval = 0.07
        count = 6
        for i in range(count):
            v_vals.append((float(i) / count, pval))
            pval += vval
            vval *= 0.5
        p_start = position[0]
        p_dir = direction[0]
        bs.animate(
            tcombine,
            'input0',
            {i[0] * lifespan: p_start + p_dir * i[1] for i in v_vals},
        )
        p_start = position[1]
        p_dir = direction[1]
        bs.animate(
            tcombine,
            'input1',
            {i[0] * lifespan: p_start + p_dir * i[1] for i in v_vals},
        )
        p_start = position[2]
        p_dir = direction[2]
        bs.animate(
            tcombine,
            'input2',
            {i[0] * lifespan: p_start + p_dir * i[1] for i in v_vals},
        )
        bs.animate(txtnode, 'opacity', {0.7 * lifespan: 1.0, lifespan: 0.0})
        bs.timer(lifespan, txtnode.delete)

    def _scoreboard(self) -> None:
        self._backing = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'position': (self.bar_posx + self._width / 2, -35),
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
        self._bar = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'opacity': 1.0,
                    'color': self.teamcolor,
                    'attach': 'topCenter',
                    'texture': self._bar_tex,
                },
            )
        )
        self._bar_scale = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self._bar_width,
                'input1': self._bar_height,
            },
        )
        self._bar_scale.connectattr('output', self._bar.node, 'scale')
        self._bar_position = bs.newnode(
            'combine',
            owner=self._bar.node,
            attrs={
                'size': 2,
                'input0': self.bar_posx + self._bar_width / 2,
                'input1': -35,
            },
        )
        self._bar_position.connectattr('output', self._bar.node, 'position')
        self._cover = bs.NodeActor(
            bs.newnode(
                'image',
                attrs={
                    'position': (self.bar_posx + 120, -35),
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
                    'position': (self.bar_posx + 120, -35),
                    'h_attach': 'center',
                    'v_attach': 'top',
                    'h_align': 'center',
                    'v_align': 'center',
                    'maxwidth': 130,
                    'scale': 0.9,
                    'text': '',
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'color': (1, 1, 1, 0.8),
                },
            )
        )

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.HitMessage):
            self.animate_mesh()
            self.do_damage(msg)
            self._update()
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            if self.node:
                self.node.position = self.position
                self.node.velocity = (0, 0, 0)
        else:
            super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0
        self.can_attack: bool = False
        self.tnt: TNTBox | None = None


# ba_meta export bascenev1.GameActivity
class HeistGame(bs.TeamGameActivity[Player, Team]):
    """Football game for teams mode."""

    name = 'Heist'
    description = 'Destroy the enemy safe box!'
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'TNT Hitpoints',
                min_value=1000,
                default=25000,
                increment=1000,
            ),
            bs.FloatChoiceSetting(
                'Model Type',
                choices=[
                    ('TNT Big', 1),
                    ('TNT', 2),
                    ('Puck', 3),
                    ('Snowball', 4),
                ],
                default=1,
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
        # We only support two-team play.
        return issubclass(sessiontype, bs.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return bs.app.classic.getmaps('team_flag')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._epic_mode = settings.get('Epic Mode', False)
        self._time_limit = float(settings['Time Limit'])
        self._tnt_hitpoints = int(settings['TNT Hitpoints'])
        self._mesh_type = float(settings['Model Type'])

        # Some base class overrides:
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )
        self.slow_motion = self._epic_mode

        self._tntbox_pos = [(-11, 2.5, 0.0), (11.0, 2.5, 0.0)]
        self.team_index = 1
        self.create_team_index = 1
        self._bots = SpazBotSet()

    def get_instance_description(self) -> str | Sequence:
        return 'Destroy the enemy safe box!'

    def get_instance_description_short(self) -> str | Sequence:
        return 'Destroy the enemy safe box!'

    def on_team_join(self, team: Team) -> None:
        # Can't do this in create_team because the team's color/etc. have
        # not been wired up yet at that point.
        self._spawn_tnt_for_team(team)

    def _spawn_tnt_for_team(self, team: Team) -> None:
        team.tnt = TNTBox(
            team_id=team,
            meshtype=self._mesh_type,
            position=self.map.get_flag_position(team.id),
            hitpoints=self._tnt_hitpoints,
            team='team ' + str(self.team_index),
        ).autoretain()
        self.team_index += 1

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        bs.timer(0.05, self._update, repeat=True)
        bs.timer(10.0, self.custom_drop, repeat=True)
        # self.setup_standard_powerup_drops()

    def custom_drop(self):
        pos = self.map.get_flag_position(None)

        def spawn_punch():
            PowerupBox(
                position=(pos[0], pos[1] + 2.0, pos[2]),
                poweruptype='punch',
                expire=False,
            ).autoretain()

        def spawn_shield():
            PowerupBox(
                position=(pos[0], pos[1] + 2.0, pos[2]),
                poweruptype='shield',
                expire=False,
            ).autoretain()

        def spawn_explodeybot():
            self._bots._spawn_bot(
                ExplodeyBotNoTimeLimit,
                pos=(pos[0], pos[1] + 1.0, pos[2]),
                on_spawn_call=None,
            )

        custom = random.choice([spawn_punch, spawn_shield, spawn_explodeybot])
        spawner.Spawner(
            pt=pos,
            spawn_time=3.0,
            send_spawn_message=False,
            spawn_callback=custom,
        )

    def _update(self) -> None:
        if not self.teams[0].tnt.node:
            self.teams[1].score = 1
        if not self.teams[1].tnt.node:
            self.teams[0].score = 1
        if self.teams[0].score > 0 or self.teams[1].score > 0:
            bs.timer(1.0, self.end_game)

    def spawn_player(self, player: Player) -> bs.Actor:
        position = self.map.get_ffa_start_position(self.players)
        spaz = self.spawn_player_spaz(player, position)
        return spaz

    def on_expire(self):
        return super().on_expire()

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            self.respawn_player(player)
        else:
            return super().handlemessage(msg)
        return None

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results, announce_delay=0.8)
