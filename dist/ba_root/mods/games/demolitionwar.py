# ba_meta require api 9
"""
DemolitionWar - BombFight on wooden floor flying in air.
Author: Mr.Smoothy
Discord: https://discord.gg/ucyaesh
Youtube: https://www.youtube.com/c/HeySmoothy
Website: https://bombsquad-community.web.app
Github:  https://github.com/bombsquad-community
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.actor.bomb import BombFactory
from bascenev1lib.game.elimination import EliminationGame, Player
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    pass

# ba_meta export bascenev1.GameActivity


class DemolitionWarGame(EliminationGame):
    name = 'DemolitionWar'
    description = 'Last remaining alive wins.'
    scoreconfig = bs.ScoreConfig(
        label='Survived', scoretype=bs.ScoreType.SECONDS, none_is_winner=True
    )
    # Show messages when players die since it's meaningful here.
    announce_player_deaths = True

    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[babase.Setting]:
        settings = [
            bs.IntSetting(
                'Lives Per Player',
                default=1,
                min_value=1,
                max_value=10,
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
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(bs.BoolSetting('Solo Mode', default=False))
            settings.append(
                bs.BoolSetting('Balance Total Lives', default=False)
            )
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Wooden Floor']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._lives_per_player = 1
        self._solo_mode = False
        self._balance_total_lives = False

    def spawn_player(self, player: Player) -> bs.Actor:
        p = [-6, -4.3, -2.6, -0.9, 0.8, 2.5, 4.2, 5.9]
        q = [-4, -2.3, -0.6, 1.1, 2.8, 4.5]

        x = random.randrange(0, len(p))
        y = random.randrange(0, len(q))
        spaz = self.spawn_player_spaz(player, position=(p[x], 1.8, q[y]))
        spaz.bomb_type = 'impact'
        # Let's reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up.
        spaz.connect_controls_to_player(
            enable_punch=False, enable_bomb=True, enable_pickup=True
        )

        # Also lets have them make some noise when they die.
        spaz.play_big_death_sound = True
        return spaz

    def on_begin(self) -> None:
        super().on_begin()
        self.map_extend()

    def on_blast(self):
        node = bs.getcollision().sourcenode
        bs.emitfx(
            (node.position[0], 0.9, node.position[2]),
            (0, 2, 0),
            30,
            1,
            spread=1,
            chunk_type='splinter',
        )
        bs.timer(0.1, babase.CallStrict(node.delete))

    def map_extend(self):
        # TODO need to improve here , so we can increase size of map easily with settings
        p = [-6, -4.3, -2.6, -0.9, 0.8, 2.5, 4.2, 5.9]
        q = [-4, -2.3, -0.6, 1.1, 2.8, 4.5]
        factory = BombFactory.get()
        self.ramp_bomb = bs.Material()
        self.ramp_bomb.add_actions(
            conditions=('they_have_material', factory.bomb_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
                ('call', 'at_connect', babase.CallStrict(self.on_blast)),
            ),
        )
        self.ramps = []
        for i in p:
            for j in q:
                self.ramps.append(self.create_ramp(i, j))

    def create_ramp(self, x, z):
        shared = SharedObjects.get()
        self._real_collied_material = bs.Material()

        self._real_collied_material.add_actions(
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            )
        )
        self.mat = bs.Material()
        self.mat.add_actions(
            actions=(
                ('modify_part_collision', 'physical', False),
                ('modify_part_collision', 'collide', False),
            )
        )
        pos = (x, 0, z)
        ud_1_r = bs.newnode(
            'region',
            attrs={
                'position': pos,
                'scale': (1.5, 1, 1.5),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    self._real_collied_material,
                    self.ramp_bomb,
                ],
            },
        )

        node = bs.newnode(
            'prop',
            owner=ud_1_r,
            attrs={
                'mesh': bs.getmesh('image1x1'),
                'light_mesh': bs.getmesh('powerupSimple'),
                'position': (2, 7, 2),
                'body': 'puck',
                'shadow_size': 0.0,
                'velocity': (0, 0, 0),
                'color_texture': bs.gettexture('tnt'),
                'mesh_scale': 1.5,
                'reflection_scale': [1.5],
                'materials': [
                    self.mat,
                    shared.object_material,
                    shared.footing_material,
                ],
                'density': 9000000000,
            },
        )
        # node.changerotation(1, 0, 0)
        mnode = bs.newnode(
            'math',
            owner=ud_1_r,
            attrs={'input1': (0, 0.6, 0), 'operation': 'add'},
        )
        ud_1_r.connectattr('position', mnode, 'input2')
        mnode.connectattr('output', node, 'position')
        return ud_1_r
