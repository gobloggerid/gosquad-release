# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# Author: goblogger
#
# Derived from Dodge The Ball game (Work of EmperoR#4098)
#
# ba_meta require api 9

from __future__ import annotations

import random
from enum import Enum
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.actor.bomb import Blast, Bomb
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor.powerupbox import PowerupBox
from bascenev1lib.game.elimination import EliminationGame, Player

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, NoReturn


# Type of bomb in this game
class BombType(Enum):
    """Types of bombs"""

    EASY = 0
    MEDIUM = 1
    ADVANCE = 2
    ULTRA = 4


# this dict decide the bomb_type spawning rate
bomb_type_dict: dict[BombType, int] = {
    BombType.EASY: 4,
    BombType.MEDIUM: 3,
    BombType.ADVANCE: 2,
    BombType.ULTRA: 1,
}


class Box(bs.Actor):
    """A box that spawn middle of map as a decoration purpose"""

    def __init__(
        self,
        position: Sequence[float],
        velocity: Sequence[float],
    ) -> NoReturn:
        super().__init__()

        not_collide = bs.Material()
        not_collide.add_actions(
            actions=(('modify_part_collision', 'collide', False))
        )

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'position': position,
                'velocity': velocity,
                'mesh': bs.getmesh('powerup'),
                'light_mesh': bs.getmesh('powerupSimple'),
                'shadow_size': 0.5,
                'body_scale': 1.4,
                'density': 9999999,
                'gravity_scale': 0.0,
                'mesh_scale': 1.4,
                'color_texture': bs.gettexture('achievementCrossHair'),
                'is_area_of_interest': True,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (not_collide,),
            },
        )
        # light
        self.light = bs.newnode(
            'light',
            owner=self.node,
            attrs={
                'radius': 0.2,
                'intensity': 0.8,
                'color': (0.0, 1.0, 0.0),
            },
        )
        self.node.connectattr('position', self.light, 'position')

        # Drawing circle and circleOutline in radius of 3
        circle = bs.newnode(
            'locator',
            owner=self.node,
            attrs={
                'shape': 'circle',
                'color': (1.0, 0.0, 0.0),
                'opacity': 0.1,
                'size': (6.0, 0.0, 6.0),
                'draw_beauty': False,
                'additive': True,
            },
        )
        self.node.connectattr('position', circle, 'position')

        circle_outline = bs.newnode(
            'locator',
            owner=self.node,
            attrs={
                'shape': 'circleOutline',
                'color': (1.0, 1.0, 0.0),
                'opacity': 0.1,
                'size': (6.0, 0.0, 6.0),
                'draw_beauty': False,
                'additive': True,
            },
        )
        self.node.connectattr('position', circle_outline, 'position')

        # # Box movement attributes
        # self._init_pos = babase.Vec3(*self.node.position)
        # self._direction = random.choice([-1, 1])
        # self._distance = 10.0
        # self._speed = 1.0  # units per second
        # self._target_x = self._init_pos.x + self._direction * self._distance

        # all bomb attributes
        self.bomb_type: BombType = BombType.EASY
        self.shoot_timer: bs.Timer | None = None
        self.start_shoot_timer: bs.Timer | None = None
        self.shoot_speed: float = 1.5
        self.force_shoot_speed: float = 0.0
        self.bomb_speed: float = 5.0

        self.injury_time = False

        # bomb shoot sound
        self.shoot_sound = bs.getsound('laserReverse')

        # same as "powerupdist"
        self.bomb_type_dist: list[BombType] = []

        for bomb in bomb_type_dict:
            for _ in range(bomb_type_dict[bomb]):
                self.bomb_type_dist.append(bomb)

        # self._move_to_target()

    def _move_to_target(self):
        if not self.node:
            return

        current_pos = bs.Vec3(*self.node.position)
        target_pos = bs.Vec3(self._target_x, current_pos.y, current_pos.z)
        direction = (target_pos - current_pos).normalized()
        velocity = direction * self._speed
        self.node.velocity = (velocity.x, velocity.y, velocity.z)

        # Calculate time to reach the target
        distance = abs(target_pos.x - current_pos.x)
        travel_time = distance / self._speed if self._speed > 0 else 1.0

        # Schedule reversal after reaching the target
        bs.timer(travel_time, bs.WeakCallStrict(self._reverse_direction))

    def _reverse_direction(self):
        # Reverse direction and set new target
        self._direction *= -1
        self._target_x = self._init_pos.x + self._direction * self._distance
        self._move_to_target()

    def shoot_bomb(self) -> NoReturn:
        assert self.node

        def _random_target() -> bs.Vec3 | None:
            """Find the nearest enemy spaz."""
            target = [
                spaz
                for node in bs.getnodes()
                if (spaz := node.getdelegate(PlayerSpaz)) and spaz.is_alive()
            ]

            if not target:
                return None

            spaz = random.choice(target)
            return bs.Vec3(*spaz.node.position)

        spaz_pos = _random_target()
        if spaz_pos is None:
            return  # Don't shoot anything

        self.upgrade_bomb_type(random.choice(self.bomb_type_dist))
        self.check_bomb_type(self.bomb_type)

        pos = bs.Vec3(*self.node.position)
        if self.force_shoot_speed != 0.0:
            self.shoot_speed = self.force_shoot_speed
        else:
            (pos.x, pos.y + 0.75, pos.z)

        bomb_type = random.choices(
            ['impact', 'ice_impact'], weights=[0.90, 0.10], k=1
        )[0]

        # Create impact bomb with autoaim
        bomb = Bomb(
            position=pos,
            bomb_type=bomb_type,
            blast_radius=1.5,
            density=0.5,
            autoaim=True,
            gravity_scale=0.0,
            override_gravity=True,
        ).autoretain()

        # shoot Animation and sound
        self.shoot_animation()

        # push the bomb in chosen diagonal direction
        bomb.node.handlemessage(
            'impulse',
            pos.x,
            pos.y,
            pos.z,  # position
            0,
            0,
            0,  # velocity
            200,  # magnitude
            0.000,
            0.000,
            0.000,  # various params
            spaz_pos.x,  # direction
            0,
            spaz_pos.z,
        )

        def _safesetattr(node: bs.Node | None, attr: str, val: Any) -> None:
            if node:
                setattr(node, attr, val)

        bs.timer(
            0.3,
            bs.CallStrict(
                _safesetattr, bomb.node, 'max_speed', self.bomb_speed
            ),
        )

        # create timer for next shot
        self.shoot_timer = bs.Timer(self.shoot_speed, self.shoot_bomb)

    def upgrade_bomb_type(self, bomb_type: BombType) -> NoReturn:
        self.bomb_type = bomb_type

    def check_bomb_type(self, bomb_type: BombType) -> NoReturn:
        if self.injury_time:
            self.bomb_speed = 8
            self.light.color = (1.0, 0.0, 0.0)
        elif bomb_type == BombType.EASY:
            self.bomb_speed = 2
            self.light.color = (0.0, 1.0, 0.0)
        elif bomb_type == BombType.MEDIUM:
            self.bomb_speed = 3
            self.light.color = (0.0, 1.0, 1.0)
        elif bomb_type == BombType.ADVANCE:
            self.bomb_speed = 4
            self.light.color = (1.0, 1.0, 0.0)
        elif bomb_type == BombType.ULTRA:
            self.bomb_speed = 5
            self.light.color = (1.0, 0.0, 1.0)

    def shoot_animation(self) -> NoReturn:
        bs.animate(
            self.node,
            'mesh_scale',
            {
                0.00: 1.4,
                0.05: 1.7,
                0.10: 1.4,
            },
        )
        self.shoot_sound.play(position=self.node.position)

    def stop_shoot(self) -> NoReturn:
        self.shoot_timer = None

    def respawn_box(self) -> NoReturn:
        activity = self._activity()
        flag_pos = activity.map.get_flag_position(None)
        pos = (flag_pos[0], flag_pos[1] + 0.5, flag_pos[2])
        if activity.map.getname() == 'The Pad':
            pos = (0.46, 4.0, -2.8)
        self.box = Box(
            position=pos,
            velocity=(0.0, 0.0, 0.0),
        ).autoretain()

    def set_injury(self) -> NoReturn:
        self.injury_time = True
        self.shoot_speed = 0.75

    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            self.stop_shoot()
            self.check_player_pos_timer = None
            self.shield_drop_timer = None
            assert self.node
            self.node.delete()
            self.respawn_box()

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)


# ba_meta export bascenev1.GameActivity
class DodgeTheBombGame(EliminationGame):
    name = 'Dodge The Bomb'
    description = 'Derived from Dodge The Ball game.'
    announce_player_deaths = False

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.check_player_pos_timer: bs.Timer | None = None
        self.shield_drop_timer: bs.Timer | None = None
        self.box: Box | None = None

    def get_instance_description(self) -> str | Sequence:
        return 'Keep away as possible as you can'

    # add a tiny text under our game name.
    def get_instance_description_short(self) -> str | Sequence:
        return 'Dodge the chasing bombs'

    def on_begin(self) -> NoReturn:
        super().on_begin()
        self.setup_standard_powerup_drops()

        flag_pos = self.map.get_flag_position(None)
        pos = (flag_pos[0], flag_pos[1] + 0.5, flag_pos[2])
        if self.map.getname() == 'The Pad':
            pos = (0.46, 4.0, -2.8)
        self.box = Box(
            position=pos,
            velocity=(0.0, 0.1, 0.0),
        ).autoretain()

        if self._epic_mode:
            bs.timer(1.0, self.box.shoot_bomb)
        else:
            bs.timer(3.0, self.box.shoot_bomb)
        # bs.timer(5.0, self.check_player_pos)
        bs.timer(20.0, self.drop_powerup)
        bs.timer(15.0, self.credit_text, repeat=True)
        bs.timer(150, self.box.set_injury)

    def setup_standard_powerup_drops(self) -> None:
        pass

    def credit_text(self) -> None:
        credit = bs.newnode(
            'text',
            attrs={
                'text': 'Derived from Dodge The Ball | Author: EmperoR#4098',
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

    def get_alive_players(self) -> Sequence[bs.Player]:
        return [p for p in self.players if p.is_alive()]

    def check_player_pos(self):
        if not self.box.node.exists():
            return

        for player in self.get_alive_players():
            difference = bs.Vec3(player.position) - bs.Vec3(
                self.box.node.position
            )
            distance = difference.length()

            if distance <= 2.5:
                self.box.force_shoot_speed = 0.2
            else:
                self.box.force_shoot_speed = 0.0

            if distance < 0.5:
                Blast(
                    position=self.box.node.position,
                    velocity=self.box.node.velocity,
                    blast_type='normal',
                    blast_radius=1.0,
                ).autoretain()

                PopupText(
                    position=self.box.node.position,
                    text=random.choice(
                        ["You'd better run!", "You'd better be away!"]
                    ),
                    random_offset=0.0,
                    scale=2.0,
                    color=self.box.light.color,
                ).autoretain()

        # self.check_player_pos_timer = bs.Timer(0.5, self.check_player_pos)
        self.check_player_pos_timer = None

    def drop_powerup(self) -> NoReturn:
        if not hasattr(self.box.node, 'position'):
            return
        pos = self.box.node.position
        powerups = ['jump', 'dash']
        PowerupBox(
            position=(pos[0], pos[1] + 0.5, pos[2] + 3.0),
            poweruptype=random.choice(powerups),
        ).autoretain()
        PowerupBox(
            position=(pos[0], pos[1] + 0.5, pos[2] - 3.0),
            poweruptype=random.choice(powerups),
        ).autoretain()

        self.shield_drop_timer = bs.Timer(20.0, self.drop_powerup)

    def spawn_player(self, player: Player) -> bs.Actor:
        position = self.map.get_ffa_start_position(self.players)
        actor = self.spawn_player_spaz(player, position)

        actor.connect_controls_to_player(
            enable_bomb=False, enable_pickup=True, enable_punch=False
        )

        # If we have any icons, update their state.
        for icon in player.icons:
            icon.handle_player_spawned()
        return actor

    def end_game(self) -> None:
        super().end_game()
        self.box.stop_shoot()
        self.check_player_pos_timer = None
        self.shield_drop_timer = None
