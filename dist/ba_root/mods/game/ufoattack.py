# Porting to api 8 made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, override
from math import cos, sin

import babase
import bascenev1 as bs
import random
from bascenev1lib.actor.bomb import BombFactory, Bomb
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.onscreentimer import OnScreenTimer

if TYPE_CHECKING:
    from typing import Any

# Ensure external map module is imported so maps get registered.
for _module_name in ('maps.ufoattack_maps', 'ufoattack_maps'):
    try:
        importlib.import_module(_module_name)
    except ImportError:
        continue
    except Exception:
        babase.print_exception(
            f'Error importing UFO Attack map module: {_module_name}'
        )
    else:
        break


# ---- Custom Messages ----

class _GotTouched:
    pass


# ---- Actors ----

class UFO(bs.Actor):

    def __init__(self,
                 moves_randomly: bool = False):
        super().__init__()
        shared = SharedObjects.get()
        self._moves_randomly = moves_randomly
        self.r: int = 0
        self.dis: list[Any] = []
        self.target: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.regs: list[bs.NodeActor] = []

        x = 1.9699566 + cos(random.randint(0, 360)) * 5.0
        z = 6.5221915 + sin(random.randint(0, 360)) * 5.0
        self.node = bs.newnode('prop',
                               delegate=self,
                               attrs={'body': 'landMine',
                                      'position': (x, 6.616, z),
                                      'mesh': bs.getmesh('landMine'),
                                      'mesh_scale': 1.5,
                                      'body_scale': 0.01,
                                      'shadow_size': 0.000001,
                                      'gravity_scale': 0.0,
                                      'color_texture': bs.gettexture(
                                          'achievementCrossHair'),
                                      'materials': [shared.object_material]})
        if self._moves_randomly:
            bs.timer(random.randrange(4500, 7000) * 0.001, self.move)

    def move(self) -> None:
        """Pick a target tile, fly to it, drop a bomb, then repeat."""
        if not self.node.exists():
            return
        try:
            # --- Step 1: collect available tiles and pick one ---
            self.dis = []
            self.regs.clear()
            for j in bs.getnodes():
                n = j.getdelegate(object)
                if j.getnodetype() == 'prop' and isinstance(n, TileFloor):
                    if n.node.exists() and not n.is_targeted:
                        self.dis.append(n)

            if not self.dis:
                # No free tiles right now; try again shortly.
                bs.timer(1.0, self.move)
                return

            self.r = random.randint(0, len(self.dis) - 1)
            self.dis[self.r].is_targeted = True
            self.target = (self.dis[self.r].node.position[0],
                           self.node.position[1],
                           self.dis[self.r].node.position[2])

            # --- Step 2: animate UFO to the chosen tile ---
            bs.animate_array(self.node, 'position', 3, {
                0: self.node.position,
                3.0: self.target})

            # --- Step 3: schedule bomb drop and next move cycle ---
            # Capture current target/index so the closures reference the
            # correct values even after self.target changes next cycle.
            self._schedule_attack(self.target, self.r)

        except Exception:
            pass

    def _schedule_attack(self,
                         target: tuple[float, float, float],
                         tile_idx: int) -> None:
        """Schedule the bomb drop (after UFO arrives) and the next move."""
        if not self.node.exists():
            return

        def _drop_bomb() -> None:
            if not self.node.exists():
                return
            Bomb(
                velocity=(0, 0, 0),
                position=(target[0],
                          self.node.position[1] - 0.43999,
                          target[2]),
                bomb_type='impact',
            ).autoretain().arm()

        def _clear_targeted() -> None:
            try:
                self.dis[tile_idx].is_targeted = False
            except Exception:
                pass

        # UFO animation takes 3 s → drop bomb just after it arrives.
        bs.timer(3.277, _drop_bomb)
        # Un-mark the tile shortly after the bomb lands.
        bs.timer(3.65, _clear_targeted)
        # Begin the next move cycle.
        bs.timer(3.875, self.move)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)


class TileFloor(bs.Actor):
    def __init__(self,
                 pos: tuple[float, float, float] = (0, 0, 0)):
        super().__init__()
        get_mat = SharedObjects.get()
        self.is_targeted: bool = False
        self.pos = pos
        self.scale = 1.5
        self.mat = bs.Material()
        self.test = bs.Material()
        self.mat.add_actions(conditions=('we_are_older_than', 1),
                             actions=(('modify_part_collision',
                                       'collide', False),))
        self.test.add_actions(
            conditions=('they_have_material',
                        BombFactory.get().bomb_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _GotTouched())))
        self.node = bs.newnode('prop',
                               delegate=self,
                               attrs={'body': 'puck',
                                      'position': self.pos,
                                      'mesh': bs.getmesh(
                                          'buttonSquareOpaque'),
                                      'mesh_scale': self.scale * 1.16,
                                      'body_scale': self.scale,
                                      'shadow_size': 0.0002,
                                      'gravity_scale': 0.0,
                                      'color_texture': bs.gettexture('tnt'),
                                      'is_area_of_interest': True,
                                      'materials': [self.mat, self.test]})
        self.node_support = bs.newnode('region',
                                       attrs={
                                           'position': self.pos,
                                           'scale': (self.scale * 0.8918,
                                                     0.1,
                                                     self.scale * 0.8918),
                                           'type': 'box',
                                           'materials': [
                                               get_mat.footing_material,
                                           ]
                                       })

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            self.node_support.delete()
        elif isinstance(msg, _GotTouched):
            bs.timer(0.1, lambda: self.handlemessage(bs.DieMessage()))
        else:
            super().handlemessage(msg)


# ---- Player / Team ----

class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        super().__init__()
        self.death_time: float | None = None


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ---- Game Activity ----

# ba_meta export bascenev1.GameActivity
class UFOAttackGame(bs.TeamGameActivity[Player, Team]):

    name = 'UFO Attack'
    description = 'Dodge the falling bombs.'
    available_settings = [
        bs.IntSetting('UFO Count',
                       max_value=20, min_value=1, default=1, increment=1),
        bs.BoolSetting('UFOs Moves Randomly', default=False),
        bs.BoolSetting('Epic Mode', default=False),
        bs.BoolSetting('Enable Run', default=True),
        bs.BoolSetting('Enable Jump', default=True),
        bs.BoolSetting('Display Map Area Dimension', default=False),
        bs.IntSetting('No. of Rows' + u' \u2192',
                       max_value=13, min_value=1, default=8, increment=1),
        bs.IntSetting('No. of Columns' + u' \u2193',
                       max_value=12, min_value=1, default=6, increment=1),
    ]
    scoreconfig = bs.ScoreConfig(label='Survived',
                                 scoretype=bs.ScoreType.SECONDS,
                                 version='B')

    # Print messages when players die (since its meaningful in this game).
    announce_player_deaths = True

    @override
    @classmethod
    def get_supported_maps(cls,
                           sessiontype: type[bs.Session]) -> list[str]:
        return ['Tile Lands', 'Tile Lands Night']

    @override
    @classmethod
    def supports_session_type(
            cls, sessiontype: type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    def __init__(self, settings: dict):
        super().__init__(settings)

        self.col = int(settings['No. of Columns' + u' \u2193'])
        self.row = int(settings['No. of Rows' + u' \u2192'])
        self._ufo_count = int(settings['UFO Count'])
        self._enable_run = bool(settings['Enable Run'])
        self._enable_jump = bool(settings['Enable Jump'])
        self._ufos_random = bool(settings['UFOs Moves Randomly'])
        self._epic_mode = settings.get('Epic Mode', False)
        self._show_dimensions = bool(
            settings['Display Map Area Dimension'])
        self._last_player_death_time: float | None = None
        self._timer: OnScreenTimer | None = None
        self._ufos: list[UFO] = []
        self.default_music = (bs.MusicType.EPIC
                              if self._epic_mode else bs.MusicType.SURVIVAL)
        if self._epic_mode:
            self.slow_motion = True

    @override
    def get_instance_display_string(self) -> babase.Lstr:
        if self._show_dimensions:
            return babase.Lstr(
                value='UFO Attack (${COL}x${ROW})',
                subs=[('${COL}', str(self.col)),
                      ('${ROW}', str(self.row))])
        return babase.Lstr(value='UFO Attack')

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self._timer = OnScreenTimer()
        self._timer.start()
        for r in range(self.col):
            for j in range(self.row):
                TileFloor(pos=(-6.204283 + (j * 1.399),
                               3.425666,
                               -1.3538 + (r * 1.399))).autoretain()
        # Spawn the requested number of UFOs.
        for _ in range(self._ufo_count):
            ufo = UFO(moves_randomly=self._ufos_random).autoretain()
            self._ufos.append(ufo)
        # If UFOs don't auto-move, kick off the first one after a delay.
        if not self._ufos_random and self._ufos:
            bs.timer(7.0, lambda: self._ufos[0].move()
                     if self._ufos else None)
        for t in self.players:
            self.spawn_player(t)

    @override
    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            bs.broadcastmessage(
                babase.Lstr(resource='playerDelayedJoinText',
                            subs=[('${PLAYER}',
                                   player.getname(full=True))]),
                color=(0, 1, 0),
            )
            assert self._timer is not None
            player.death_time = self._timer.getstarttime()
            return

    @override
    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        self._check_end_game()

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        dis: list[TileFloor] = []
        for a in bs.getnodes():
            g = a.getdelegate(object)
            if (
                a.getnodetype() == 'prop'
                and isinstance(g, TileFloor)
                and g.node.exists()
                and not g.is_targeted
            ):
                dis.append(g)

        if dis:
            tile = random.choice(dis)
            spaz = self.spawn_player_spaz(
                player,
                position=(
                    tile.node.position[0],
                    tile.node.position[1] + 1.005958,
                    tile.node.position[2],
                ),
            )
        else:
            spaz = self.spawn_player_spaz(player)

        # Brief spawn protection to avoid unavoidable instant deaths.
        if spaz.node:
            spaz.node.invincible = True

            def _clear_spawn_invincible(node: bs.Node = spaz.node) -> None:
                if node and node.exists():
                    node.invincible = False

            bs.timer(2.0, _clear_spawn_invincible)

        spaz.connect_controls_to_player(enable_punch=False,
                                        enable_bomb=False,
                                        enable_run=self._enable_run,
                                        enable_jump=self._enable_jump,
                                        enable_pickup=False)
        spaz.play_big_death_sound = True
        return spaz

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)

            curtime = bs.time()
            msg.getplayer(Player).death_time = curtime
            bs.timer(1.0, self._check_end_game)

        else:
            return super().handlemessage(msg)
        return None

    def _check_end_game(self) -> None:
        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break
        if living_team_count <= 1:
            self.end_game()

    @override
    def end_game(self) -> None:
        # Clean up all UFOs.
        for ufo in self._ufos:
            ufo.handlemessage(bs.DieMessage())
        cur_time = bs.time()
        assert self._timer is not None
        start_time = self._timer.getstarttime()
        for team in self.teams:
            for player in team.players:
                survived = False
                if player.death_time is None:
                    survived = True
                    player.death_time = cur_time + 1
                score = int(player.death_time - self._timer.getstarttime())
                if survived:
                    score += 2
                self.stats.player_scored(player, score, screenmessage=False)
        self._timer.stop(endtime=self._last_player_death_time)
        results = bs.GameResults()
        for team in self.teams:
            longest_life = 0.0
            for player in team.players:
                assert player.death_time is not None
                longest_life = max(longest_life,
                                   player.death_time - start_time)

            # Submit the score value in milliseconds.
            results.set_team_score(team, int(longest_life))

        self.end(results=results)
