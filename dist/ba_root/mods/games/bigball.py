# Made by MythB

# ba_meta require api 9
from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.powerupbox import PowerupBoxFactory
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

MIN_SPHERE_SIZE = 0.01


class PuckDiedMessage:
    """Inform something that a puck has died."""

    def __init__(self, puck: Puck):
        self.puck = puck


# goalpost


class FlagKale(bs.Actor):
    def __init__(self, position=(0, 2.5, 0), color=(1, 1, 1)):
        super().__init__()
        activity = self.getactivity()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'flag',
            attrs={
                'position': (position[0], position[1] + 0.75, position[2]),
                'color_texture': activity._flagKaleTex,
                'color': color,
                'materials': [shared.object_material, activity._kaleMaterial],
            },
            delegate=self,
        )

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            if self.node.exists():
                self.node.delete()
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(m)


class Puck(bs.Actor):
    def __init__(self, position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        shared = SharedObjects.get()
        activity = self.getactivity()

        # Spawn just above the provided point.
        self._spawn_pos = (position[0], position[1] + 1.0, position[2])
        self.last_players_to_touch: dict[int, Player] = {}
        self.scored = False
        assert activity is not None
        assert isinstance(activity, BigBallGame)
        pmats = [shared.object_material, activity.puck_material]
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': activity._ballModel,
                'color_texture': activity._ballTex,
                'body': 'sphere',
                'reflection': 'soft',
                'reflection_scale': [0.2],
                'shadow_size': 0.8,
                'is_area_of_interest': True,
                'position': self._spawn_pos,
                'materials': pmats,
                'body_scale': 4,
                'mesh_scale': 1,
                'density': 0.02,
            },
        )
        bs.animate(
            self.node,
            'mesh_scale',
            {0: MIN_SPHERE_SIZE, 0.2: 1.3, 0.26: 1},
        )

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            assert self.node
            self.node.delete()
            activity = self._activity()
            if activity and not msg.immediate:
                activity.handlemessage(PuckDiedMessage(self))

        # If we go out of bounds, move back to where we started.
        elif isinstance(msg, bs.OutOfBoundsMessage):
            assert self.node
            self.node.position = self._spawn_pos

        elif isinstance(msg, bs.HitMessage):
            assert self.node
            assert msg.force_direction is not None
            self.node.handlemessage(
                'impulse',
                msg.pos[0],
                msg.pos[1],
                msg.pos[2],
                msg.velocity[0],
                msg.velocity[1],
                msg.velocity[2],
                1.0 * msg.magnitude,
                1.0 * msg.velocity_magnitude,
                msg.radius,
                0,
                msg.force_direction[0],
                msg.force_direction[1],
                msg.force_direction[2],
            )

            # If this hit came from a player, log them as the last to touch us.
            s_player = msg.get_source_player(Player)
            if s_player is not None:
                activity = self._activity()
                if activity:
                    if s_player in activity.players:
                        self.last_players_to_touch[s_player.team.id] = s_player
        else:
            super().handlemessage(msg)


# for night mode: using a actor with large shadow and little mesh scale. Better then tint i think, players and objects more visible


class NightMod(bs.Actor):
    def __init__(self, position=(0, 0, 0)):
        super().__init__()
        shared = SharedObjects.get()
        activity = self.getactivity()
        # spawn just above the provided point
        self._spawnPos = (position[0], position[1], position[2])
        self.node = bs.newnode(
            'prop',
            attrs={
                'mesh': activity._nightModel,
                'color_texture': activity._nightTex,
                'body': 'sphere',
                'reflection': 'soft',
                'body_scale': 0.1,
                'mesh_scale': 0.001,
                'density': 0.010,
                'reflection_scale': [0.23],
                'shadow_size': 999999.0,
                'is_area_of_interest': True,
                'position': self._spawnPos,
                'materials': [activity._nightMaterial],
            },
            delegate=self,
        )

    def handlemssage(self, m):
        super().handlemessage(m)


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class BigBallGame(bs.TeamGameActivity[Player, Team]):
    name = 'Big Ball'
    description = 'Score some goals.\nFlags are goalposts.\nScored team players get boxing gloves,\nNon-scored team players getting shield (if Grant Powers on Score).\nYou can also set Night Mode!'
    SCORING_POWERUPS = [
        'shield',
        'invinciblity',
        'armor',
        'health',
        'avenge',
        'reflector',
        'cannon',
    ]
    CONCEDING_POWERUPS = [
        'autoaim',
        'iceman',
        'punch',
        'dynamite_punch',
        'snowball',
        'drone',
        'buddy_bot',
        'puppet',
    ]
    CONCEDING_PUNISHMENT = [
        'zombie',
        'skin',
    ]
    available_settings = [
        bs.IntSetting(
            'Score to Win',
            min_value=1,
            default=1,
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
        bs.BoolSetting('Epic Mode', True),
        bs.BoolSetting('Night Mode', False),
        bs.BoolSetting('Grant Powers on Score', False),
    ]
    default_music = bs.MusicType.HOCKEY

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Football Stadium']

    def __init__(self, settings: dict):
        super().__init__(settings)
        shared = SharedObjects.get()
        self._scoreboard = Scoreboard()
        self._cheer_sound = bs.getsound('cheer')
        self._chant_sound = bs.getsound('crowdChant')
        self._foghorn_sound = bs.getsound('foghorn')
        self._swipsound = bs.getsound('swip')
        self._whistle_sound = bs.getsound('refWhistle')
        self._ballModel = bs.getmesh('shield')
        self._ballTex = bs.gettexture('eggTex1')
        self._ballSound = bs.getsound('impactMedium2')
        self._flagKaleTex = bs.gettexture('star')
        self._kaleSound = bs.getsound('metalHit')
        self._nightModel = bs.getmesh('shield')
        self._nightTex = bs.gettexture('black')
        self._kaleMaterial = bs.Material()
        # add friction to flags for standing our position (as far as)
        self._kaleMaterial.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=(('modify_part_collision', 'friction', 9999.5)),
        )
        self._kaleMaterial.add_actions(
            conditions=(
                ('we_are_younger_than', 1),
                'and',
                ('they_have_material', shared.object_material),
            ),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self._kaleMaterial.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=(('modify_part_collision', 'collide', False)),
        )
        self._kaleMaterial.add_actions(
            conditions=('they_have_material', shared.object_material),
            actions=(('impact_sound', self._kaleSound, 2, 5)),
        )
        # we dont wanna hit the night so
        self._nightMaterial = bs.Material()
        self._nightMaterial.add_actions(
            conditions=(
                ('they_have_material', shared.pickup_material),
                'or',
                ('they_have_material', shared.attack_material),
            ),
            actions=(('modify_part_collision', 'collide', False)),
        )
        # we also dont want anything moving it
        self._nightMaterial.add_actions(
            conditions=(
                ('they_have_material', shared.object_material),
                'or',
                ('they_dont_have_material', shared.footing_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False),
            ),
        )
        self.puck_material = bs.Material()
        self.puck_material.add_actions(
            actions=(('modify_part_collision', 'friction', 0.5))
        )
        self.puck_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False),
        )
        self.puck_material.add_actions(
            conditions=(
                ('we_are_younger_than', 100),
                'and',
                ('they_have_material', shared.object_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )
        self.puck_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=('impact_sound', self._ballSound, 0.2, 5),
        )

        # Keep track of which player last touched the puck
        self.puck_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(('call', 'at_connect', self._handle_puck_player_collide),),
        )

        # We want the puck to kill powerups; not get stopped by them
        self.puck_material.add_actions(
            conditions=(
                'they_have_material',
                PowerupBoxFactory.get().powerup_material,
            ),
            actions=(
                ('modify_part_collision', 'physical', False),
                ('message', 'their_node', 'at_connect', bs.DieMessage()),
            ),
        )
        self._score_region_material = bs.Material()
        self._score_region_material.add_actions(
            conditions=('they_have_material', self.puck_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call', 'at_connect', self._handle_score),
            ),
        )
        self._puck_spawn_pos: Sequence[float] | None = None
        self._score_regions: list[bs.NodeActor] | None = None
        self._puck: Puck | None = None
        self._score_to_win = int(settings['Score to Win'])
        self._time_limit = float(settings['Time Limit'])
        self._nm = bool(settings['Night Mode'])
        self._grant_power = bool(settings['Grant Powers on Score'])
        self._epic_mode = settings['Epic Mode']
        # Base class overrides.
        self.slow_motion = self._epic_mode

        self._enable_powers = True
        self._switch_powers_timer = bs.Timer(
            30.0, self._switch_powers, repeat=True
        )

    def get_instance_description(self) -> str | Sequence:
        if self._score_to_win == 1:
            return 'Score a goal.'
        return 'Score ${ARG1} goals.', self._score_to_win

    def get_instance_description_short(self) -> str | Sequence:
        if self._score_to_win == 1:
            return 'score a goal'
        return 'score ${ARG1} goals', self._score_to_win

    def on_begin(self) -> None:
        super().on_begin()

        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops(enable_tnt=False)
        self._puck_spawn_pos = self.map.get_flag_position(None)
        self._spawn_puck()
        self._flagKalesSpawn()
        # for night mode we need night actor. And same goodies for nigh mode
        if self._nm:
            self._nightSpawny(), self._flagKaleFlash()

        # Set up the two score regions.
        defs = self.map.defs
        self._score_regions = []
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': (13.75, 0.85744967453, 0.1095578275),
                        'scale': (1.05, 1.1, 3.8),
                        'type': 'box',
                        'materials': [self._score_region_material],
                    },
                )
            )
        )
        self._score_regions.append(
            bs.NodeActor(
                bs.newnode(
                    'region',
                    attrs={
                        'position': (-13.55, 0.85744967453, 0.1095578275),
                        'scale': (1.05, 1.1, 3.8),
                        'type': 'box',
                        'materials': [self._score_region_material],
                    },
                )
            )
        )
        self._update_scoreboard()
        self._chant_sound.play()

    def _nightSpawny(self):
        self.MythBrk = NightMod(position=(0, 0.05744967453, 0))

    # spawn some goodies on nightmode for pretty visuals
    def _flagKaleFlash(self):
        # flags positions
        kale1 = (-12.45, 0.05744967453, -2.075)
        kale2 = (-12.45, 0.05744967453, 2.075)
        kale3 = (12.66, 0.03986567039, 2.075)
        kale4 = (12.66, 0.03986567039, -2.075)

        flash = bs.newnode(
            'light',
            attrs={'position': kale1, 'radius': 0.15, 'color': (1.0, 1.0, 0.7)},
        )

        flash = bs.newnode(
            'light',
            attrs={'position': kale2, 'radius': 0.15, 'color': (1.0, 1.0, 0.7)},
        )

        flash = bs.newnode(
            'light',
            attrs={'position': kale3, 'radius': 0.15, 'color': (0.7, 1.0, 1.0)},
        )

        flash = bs.newnode(
            'light',
            attrs={'position': kale4, 'radius': 0.15, 'color': (0.7, 1.0, 1.0)},
        )

    # flags positions

    def _flagKalesSpawn(self):
        for team in self.teams:
            if team.id == 0:
                _colorTeam0 = team.color
            if team.id == 1:
                _colorTeam1 = team.color

        self._MythB = FlagKale(
            position=(-12.45, 0.05744967453, -2.075), color=_colorTeam0
        )
        self._MythB2 = FlagKale(
            position=(-12.45, 0.05744967453, 2.075), color=_colorTeam0
        )
        self._MythB3 = FlagKale(
            position=(12.66, 0.03986567039, 2.075), color=_colorTeam1
        )
        self._MythB4 = FlagKale(
            position=(12.66, 0.03986567039, -2.075), color=_colorTeam1
        )

    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    def _handle_puck_player_collide(self) -> None:
        collision = bs.getcollision()
        try:
            puck = collision.sourcenode.getdelegate(Puck, True)
            player = collision.opposingnode.getdelegate(
                PlayerSpaz, True
            ).getplayer(Player, True)
        except bs.NotFoundError:
            return

        puck.last_players_to_touch[player.team.id] = player

    def _kill_puck(self) -> None:
        self._puck = None

    def _handle_score(self) -> None:
        """A point has been scored."""

        assert self._puck is not None
        assert self._score_regions is not None

        # Our puck might stick around for a second or two
        # we don't want it to be able to score again.
        if self._puck.scored:
            return

        region = bs.getcollision().sourcenode
        index = 0
        for index in range(len(self._score_regions)):
            if region == self._score_regions[index].node:
                break

        for team in self.teams:
            if team.id == index:
                scoring_team = team
                team.score += 1

                # Tell all players to celebrate.
                # Grant different powers to scoring team.
                for player in team.players:
                    if player.actor:
                        actor = player.actor
                        powerup = random.choice(self.SCORING_POWERUPS)
                        actor.handlemessage(bs.PowerupMessage(powerup))
                        actor.handlemessage(bs.CelebrateMessage(2.0))
                        if getattr(actor, '_puppetspaz', None):
                            actor._puppetspaz.handlemessage(
                                bs.PowerupMessage(powerup)
                            )

                # If we've got the player from the scoring team that last
                # touched us, give them points.
                if (
                    scoring_team.id in self._puck.last_players_to_touch
                    and self._puck.last_players_to_touch[scoring_team.id]
                ):
                    self.stats.player_scored(
                        self._puck.last_players_to_touch[scoring_team.id],
                        100,
                        big_message=True,
                    )

                # End game if we won.
                if team.score >= self._score_to_win:
                    self.end_game()

            # Grant different powers and punishments to conceding team.
            else:
                punishment = random.choice(self.CONCEDING_PUNISHMENT)
                for player in team.players:
                    if player.actor:
                        actor = player.actor
                        powerup = random.choice(self.CONCEDING_POWERUPS)
                        actor.handlemessage(bs.PowerupMessage(powerup))
                        if getattr(actor, '_puppetspaz', None):
                            powerup = random.choice(self.CONCEDING_POWERUPS)
                            actor._puppetspaz.handlemessage(
                                bs.PowerupMessage(powerup)
                            )

                        # Punishment
                        bs.timer(
                            1.0,
                            bs.WeakCallStrict(
                                actor.handlemessage,
                                bs.PowerupMessage(punishment),
                            ),
                        )
                        if getattr(actor, '_puppetspaz', None):
                            actor._puppetspaz.handlemessage(
                                bs.PowerupMessage(punishment)
                            )

        self._foghorn_sound.play()
        self._cheer_sound.play()

        self._puck.scored = True

        # Kill the puck (it'll respawn itself shortly).
        bs.timer(1.0, self._kill_puck)

        light = bs.newnode(
            'light',
            attrs={
                'position': bs.getcollision().position,
                'height_attenuated': False,
                'color': (1, 0, 0),
            },
        )
        bs.animate(light, 'intensity', {0: 0, 0.5: 1, 1.0: 0}, loop=True)
        bs.timer(1.0, light.delete)

        bs.cameraflash(duration=10.0)
        self._update_scoreboard()

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    def _update_scoreboard(self) -> None:
        winscore = self._score_to_win
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score, winscore)

    def _switch_powers(self) -> None:
        activity = bs.getactivity()
        if activity is not None:
            activity.toggle_slow_motion()

        self._enable_powers = not self._enable_powers
        # Instantly activate powers for all players
        # only when powers are enable
        for player in self.players:
            actor = player.actor
            if not actor or not getattr(actor, 'node', None):
                continue

            if not self._enable_powers:
                actor.node.hockey = False
                if getattr(actor, '_puppetspaz', None) and (
                    actor._puppetspaz.node
                ):
                    actor._puppetspaz.node.hockey = False
            else:
                actor.equip_speed()
                actor.equip_dash()
                actor.equip_teleport()
                actor.equip_super_jump()
                if getattr(actor, '_puppetspaz', None):
                    actor._puppetspaz.equip_speed()
                    actor._puppetspaz.equip_dash()
                    actor._puppetspaz.equip_teleport()
                    actor._puppetspaz.equip_super_jump()

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        """Spawn a player with enhanced abilities."""
        spaz = self.spawn_player_spaz(player)
        if self._enable_powers:
            spaz.equip_speed()
            spaz.equip_dash()
            spaz.equip_teleport()
            spaz.equip_super_jump()
        return spaz

    @override
    def handlemessage(self, msg: Any) -> Any:
        # Respawn dead players if they're still in the game.
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior...
            super().handlemessage(msg)
            self.respawn_player(msg.getplayer(Player))

        # Respawn dead pucks.
        elif isinstance(msg, PuckDiedMessage):
            if not self.has_ended():
                bs.timer(3.0, self._spawn_puck)
        else:
            super().handlemessage(msg)

    def _flash_puck_spawn(self) -> None:
        light = bs.newnode(
            'light',
            attrs={
                'position': self._puck_spawn_pos,
                'height_attenuated': False,
                'color': (1, 0, 0),
            },
        )
        bs.animate(light, 'intensity', {0.0: 0, 0.25: 1, 0.5: 0}, loop=True)
        bs.timer(1.0, light.delete)

    def _spawn_puck(self) -> None:
        self._swipsound.play()
        self._whistle_sound.play()
        # self._flagKalesSpawn()
        self._flash_puck_spawn()
        assert self._puck_spawn_pos is not None
        self._puck = Puck(position=self._puck_spawn_pos)
        self._puck.light = bs.newnode(
            'light',
            owner=self._puck.node,
            attrs={
                'intensity': 0.3,
                'height_attenuated': False,
                'radius': 0.2,
                'color': (0.9, 0.2, 0.9),
            },
        )
        self._puck.node.connectattr('position', self._puck.light, 'position')
