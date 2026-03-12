# Released under the MIT License. See LICENSE for details.
#
from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs
from babase import InputType
from bascenev1lib.actor.bomb import Bomb
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    pass


class Floater(bs.Actor):
    def __init__(self, bounds):
        super().__init__()
        shared = SharedObjects.get()
        self.is_controlled = False
        self.owner = None
        self.floater_material = bs.Material()
        self.floater_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_node_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )

        self.floater_material.add_actions(
            conditions=(
                ('they_have_material', shared.object_material),
                'or',
                ('they_have_material', shared.footing_material),
                'or',
                ('they_have_material', self.floater_material),
            ),
            actions=('modify_part_collision', 'physical', False),
        )

        self.pos = bounds
        self.px = 'random.uniform(self.pos[0],self.pos[3])'
        self.py = 'random.uniform(self.pos[1],self.pos[4])'
        self.pz = 'random.uniform(self.pos[2],self.pos[5])'

        self.node = bs.newnode(
            'prop',
            delegate=self,
            owner=None,
            attrs={
                'position': (eval(self.px), eval(self.py), eval(self.pz)),
                'mesh': bs.getmesh('landMine'),
                'light_mesh': bs.getmesh('landMine'),
                'body': 'landMine',
                'body_scale': 3,
                'mesh_scale': 3.1,
                'shadow_size': 0.25,
                'density': 10,
                'gravity_scale': 0.0,
                'color_texture': bs.gettexture('achievementFlawlessVictory'),
                'reflection': 'powerup',
                'reflection_scale': [0.25],
                'materials': [shared.footing_material, self.floater_material],
            },
        )
        self.node2 = bs.newnode(
            'prop',
            owner=self.node,
            attrs={
                'position': (0, 0, 0),
                'body': 'sphere',
                'mesh': None,
                'color_texture': bs.gettexture('null'),
                'body_scale': 1.0,
                'reflection': 'powerup',
                'density': 10,
                'reflection_scale': [1.0],
                'mesh_scale': 1.0,
                'gravity_scale': 0,
                'shadow_size': 0.1,
                'is_area_of_interest': True,
                'materials': [shared.object_material, self.floater_material],
            },
        )
        self.node.connectattr('position', self.node2, 'position')

    def can_control(self):
        if not self.node.exists():
            return False
        if not self.owner.is_alive():
            self.disconnect()
            return False
        return True

    def connect(self):
        self.is_controlled = True
        self.check_player_die()

    def up(self):
        if not self.can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], 5, v[2])

    def down(self):
        if not self.can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], -5, v[2])

    def vertical_release(self):
        v = self.node.velocity
        self.node.velocity = (v[0], 0, v[2])

    def leftright(self, value):
        if not self.can_control():
            return
        v = self.node.velocity
        self.node.velocity = (5 * value, v[1], v[2])

    def updown(self, value):
        if not self.can_control():
            return
        v = self.node.velocity
        self.node.velocity = (v[0], v[1], -5 * value)

    def disconnect(self):
        if self.node.exists():
            self.is_controlled = False
            self.node.velocity = (0, 0, 0)
            self.move()

    def check_player_die(self):
        if not self.is_controlled:
            return
        if self.owner is None:
            return
        if self.owner.is_alive():
            bs.timer(1, self.check_player_die)
            return
        else:
            self.disconnect()

    def distance(self, x1, y1, z1, x2, y2, z2):
        d = math.sqrt(
            math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2) + math.pow(z2 - z1, 2)
        )
        return d

    def drop(self):
        try:
            np = self.node.position
        except Exception:
            np = (0, 0, 0)
        bomb = Bomb(
            bomb_type=random.choice(['sticky', 'impact', 'land_mine']),
            source_player=self.owner,
            position=(np[0], np[1] - 1, np[2]),
            velocity=(0, -1, 0),
        ).autoretain()
        if bomb.bomb_type in ['impact', 'land_mine']:
            bomb.arm()

    def move(self):
        px = eval(self.px)
        py = eval(self.py)
        pz = eval(self.pz)
        if self.node.exists() and not self.is_controlled:
            pn = self.node.position
            dist = self.distance(pn[0], pn[1], pn[2], px, py, pz)
            self.node.velocity = (
                (px - pn[0]) / dist,
                (py - pn[1]) / dist,
                (pz - pn[2]) / dist,
            )
            t = dist - 1 if dist - 1 >= 0 else 0.1
            bs.timer(t, bs.WeakCallStrict(self.move))

    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            self.node2.delete()
            self.is_controlled = False
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)


def assign_floater(index, clid):
    activity = bs.get_foreground_host_activity()
    player: bs.Player = activity.players[index]

    floaters = activity.customdata.setdefault('floaters', [])
    with activity.context:
        floater = Floater(
            activity.map.get_def_bound_box('map_bounds')
        ).autoretain()
        floaters.append(floater)

        def disconnect():
            player.actor.node.invincible = False
            player.resetinput()
            player.actor.connect_controls_to_player()
            floater.disconnect()

        try:
            ps = player.actor.node.position
        except Exception:
            return

        floater.node.position = (ps[0], ps[1] + 1.0, ps[2])
        player.actor.node.invincible = True
        player.actor.node.hold_node = floater.node2
        player.resetinput()
        if player.actor._connected_to_player:
            player.actor.disconnect_controls_from_player()

        floater.owner = player
        floater.connect()

        bs.broadcastmessage(
            message=(
                "Don't stop moving to keep controlling to floater.\n "
                'Press Bomb to throw bombs and Punch to release.'
            ),
            clients=[clid],
            transient=True,
            color=(0, 1, 1),
        )

        player.assigninput(InputType.PICK_UP_PRESS, floater.up)
        player.assigninput(InputType.PICK_UP_RELEASE, floater.vertical_release)
        player.assigninput(InputType.JUMP_PRESS, floater.down)
        player.assigninput(InputType.JUMP_RELEASE, floater.vertical_release)
        player.assigninput(InputType.BOMB_PRESS, floater.drop)
        player.assigninput(InputType.PUNCH_PRESS, bs.CallStrict(disconnect))
        player.assigninput(InputType.UP_DOWN, floater.updown)
        player.assigninput(InputType.LEFT_RIGHT, floater.leftright)
