# Porting made easier by baport.(https://github.com/bombsquad-community/baport)
# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.actor.bomb import Blast, Bomb, BombFactory
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any


class CustomLang:
    lang = bs.app.lang.language
    if lang == 'Spanish':
        name = 'Caja Mágica'
        description = 'Agarra la caja mágica y empieza a volar.'
        description_short = 'Mantén la caja mágica durante ${ARG1} segundos.'
        name2 = 'Bomba Atómica'
        description2 = (
            'Agarra la bomba atómica y empieza a volar.\n'
            '¡CUIDADO! Mayor probabilidad de explotar.'
        )
        description_short2 = 'Mantén la bomba atómica durante ${ARG1} segundos.'
    else:
        name = 'Magic Box'
        description = 'Grab the box and start flying.'
        description_short = 'Hold the magic box for ${ARG1} seconds.'
        name2 = 'Atomic Bomb'
        description2 = (
            'Grab the atomic bomb and start flying.\n'
            'CARE! Increased chance of exploding.'
        )
        description_short2 = 'Hold the atomic bomb for ${ARG1} seconds.'


class MagicBox(Bomb):
    def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        bomb_type: str = 'tnt',
        blast_radius: float = 2.0,
        source_player: bs.Player = None,
        owner: bs.Node = None,
    ):
        bs.Actor.__init__(self)

        shared = SharedObjects.get()
        factory = BombFactory.get()

        self.bomb_type = bomb_type
        self._exploded = False
        self.blast_radius = blast_radius
        self.blast_radius *= 1.45

        self._explode_callbacks = []

        # the player this came from
        self.source_player = self._source_player = source_player

        # by default our hit type/subtype is our own,
        # but we pick up types of whoever
        # sets us off so we know what caused a chain reaction
        self.hit_type = 'explosion'
        self.hit_subtype = self.bomb_type

        # if no owner was provided, use an unconnected node ref
        if owner is None:
            owner = bs.Node(None)

        # The node this came from.
        # FIXME: can we unify this and source_player?
        self.owner = owner

        materials = (factory.bomb_material, shared.object_material)
        self._tnt_material = materials + (shared.footing_material,)
        self._impact_material = materials + (factory.impact_blast_material,)

        if self.bomb_type == 'tnt':
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': velocity,
                    'mesh': factory.tnt_mesh,
                    'body': 'crate',
                    'shadow_size': 0.5,
                    'color_texture': factory.tnt_tex,
                    'reflection': 'powerup',
                    'reflection_scale': [0.23],
                    'materials': self._tnt_material,
                },
            )
        else:
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': velocity,
                    'mesh': factory.impact_bomb_mesh,
                    'body': 'crate',
                    'shadow_size': 0.2,
                    'color_texture': factory.impact_tex,
                    'reflection': 'powerup',
                    'reflection_scale': [1.5],
                    'materials': materials,
                },
            )

        # self.node.extraAcceleration = (0, 40, 0)
        self.held_by = 0
        self._is_dead: bool = False

        if self.bomb_type == 'tnt':
            bs.animate(self.node, 'mesh_scale', {0.0: 0.0, 0.2: 1.3, 0.26: 1.0})
        else:
            bs.animate(self.node, 'mesh_scale', {0.0: 0.0, 0.2: 1.3, 0.26: 1.0})

    def _animate_impact(self) -> None:
        bs.animate(
            self.node,
            'mesh_scale',
            {0.0: 1.0, 2.0: 1.5, 20.0: 5.3, 22.0: 5.0, 24.0: 5.0, 40.0: 20.0},
        )

    def arm(self) -> None:
        if not self.node:
            return
        factory = BombFactory.get()
        self.node.materials = self._impact_material
        intex: Sequence[bs.Texture]
        intex = (
            factory.impact_lit_tex,
            factory.impact_tex,
            factory.impact_tex,
        )
        self.texture_sequence = bs.newnode(
            'texture_sequence',
            owner=self.node,
            attrs={'rate': 100, 'input_textures': intex},
        )
        self.texture_sequence.connectattr(
            'output_texture', self.node, 'color_texture'
        )
        factory.activate_sound.play(0.5, position=self.node.position)

    def explode(self) -> None:
        """Blows up the bomb if it has not yet done so."""
        if self._exploded:
            return
        self._exploded = True
        if self.bomb_type != 'tnt':
            self.blast_radius *= self.node.mesh_scale
        if self.node:
            blast = Blast(
                position=self.node.position,
                velocity=self.node.velocity,
                blast_radius=self.blast_radius,
                blast_type=self.bomb_type,
                source_player=bs.existing(self._source_player),
                hit_type=self.hit_type,
                hit_subtype=self.hit_subtype,
            ).autoretain()
            for callback in self._explode_callbacks:
                callback(self, blast)

        # We blew up so we need to go away.
        # NOTE TO SELF: do we actually need this delay?
        bs.timer(0.001, bs.WeakCallStrict(self.handlemessage, bs.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PickedUpMessage):
            self._activity()._update_box_state()
            if self.bomb_type != 'tnt':
                self.owner = msg.node
                self._animate_impact()
                bs.timer(0.25, self.arm)
        elif isinstance(msg, bs.DroppedMessage):
            if self.bomb_type != 'tnt':
                self.owner = None
            self.held_by -= 1
            bs.timer(0.01, self._update_floatyness)
            bs.timer(0.2, self._activity()._update_box_state)
        elif isinstance(msg, bs.DieMessage):
            if self._is_dead:
                return
            bs.timer(1.0, self._activity()._spawn_box)
            self._is_dead = True
        super().handlemessage(msg)

    def _update_floatyness(self) -> None:
        if self.node:
            old_y = self.node.extra_acceleration[1]
            new_y = {0: 0, 1: 39, 2: 19 + 20 * 2, 3: 19 + 20 * 3}.get(
                self.held_by, 0
            )
            time = 0.3 if (old_y >= new_y) else 1.0
            keys = {0: (0, old_y, 0), time: (0, new_y, 0)}
            bs.animate_array(self.node, 'extra_acceleration', 3, keys)

    def _hide_score_text(self) -> None:
        if self._score_text:
            assert isinstance(self._score_text.scale, float)
            bs.animate(
                self._score_text,
                'scale',
                {0.0: self._score_text.scale, 0.2: 0.0},
            )

    def set_score_text(self, text: str) -> None:
        """Show a message over the flag; handy for scores."""
        if not self.node:
            return
        try:
            exists = self._score_text
        except Exception:
            exists = False
        if not exists:
            start_scale = 0.0
            math = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 0.6, 0), 'operation': 'add'},
            )
            self.node.connectattr('position', math, 'input2')
            self._score_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'scale': 0.02,
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'h_align': 'center',
                },
            )
            math.connectattr('output', self._score_text, 'position')
        else:
            assert isinstance(self._score_text.scale, float)
            start_scale = self._score_text.scale
            self._score_text.text = text
        self._score_text.color = bs.safecolor((1.0, 1.0, 0.4))
        bs.animate(self._score_text, 'scale', {0: start_scale, 0.2: 0.02})
        self._score_text_hide_timer = bs.Timer(
            1.0, bs.WeakCallStrict(self._hide_score_text)
        )


class BoxState(Enum):
    """States our single flag can be in."""

    NEW = 0
    UNCONTESTED = 1
    CONTESTED = 2
    HELD = 3


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self, timeremaining: int) -> None:
        self.timeremaining = timeremaining
        self.holdingbox = False


# ba_meta export bascenev1.GameActivity
class MagicBoxGame(bs.TeamGameActivity[Player, Team]):
    name = CustomLang.name
    description = CustomLang.description
    scoreconfig = bs.ScoreConfig(label='Time Held')
    available_settings = [
        bs.IntSetting(
            'Hold Time',
            min_value=10,
            default=30,
            increment=10,
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

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return bs.app.classic.getmaps('keep_away')

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._swipsound = bs.getsound('swip')
        self._tick_sound = bs.getsound('tick')
        self._countdownsounds = {
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

        self._flag_spawn_pos: Sequence[float] | None = None
        self._update_timer: bs.Timer | None = None
        self._holding_players: list[Player] = []
        self._box_state: BoxState | None = None
        self._box_light: bs.Node | None = None
        self._box: MagicBox | None = None
        self._hold_time = int(settings['Hold Time'])
        self._time_limit = float(settings['Time Limit'])
        self._epic_mode = bool(settings['Epic Mode'])

        # Base class overrides
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.CHOSEN_ONE
        )

    def get_instance_description(self) -> str | Sequence:
        return CustomLang.description_short, self._hold_time

    def get_instance_description_short(self) -> str | Sequence:
        return CustomLang.description_short, self._hold_time

    def create_team(self, sessionteam: bs.SessionTeam) -> Team:
        return Team(timeremaining=self._hold_time)

    def on_team_join(self, team: Team) -> None:
        self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops(enable_tnt=False)
        self._box_spawn_pos = self.map.get_flag_position(None)
        self._spawn_box()
        self._update_timer = bs.Timer(1.0, call=self._tick, repeat=True)
        self._update_box_state()

    def _tick(self) -> None:
        self._update_box_state()

        # Award points to all living players holding the flag.
        for player in self._holding_players:
            if player:
                assert self.stats
                self.stats.player_scored(
                    player, 3, screenmessage=False, display=False
                )

        scoreteam = self._scoring_team

        if scoreteam is not None:
            if scoreteam.timeremaining > 0:
                self._tick_sound.play()

            scoreteam.timeremaining = max(0, scoreteam.timeremaining - 1)
            self._update_scoreboard()
            if scoreteam.timeremaining > 0:
                assert self._box is not None
                self._box.set_score_text(str(scoreteam.timeremaining))

            # announce numbers we have sounds for
            if scoreteam.timeremaining in self._countdownsounds:
                self._countdownsounds[scoreteam.timeremaining].play()

            # Winner!
            if scoreteam.timeremaining <= 0:
                self.end_game()

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, self._hold_time - team.timeremaining)
        self.end(results=results, announce_delay=0)

    def _update_box_state(self) -> None:
        for team in self.teams:
            team.holdingbox = False
        self._holding_players = []
        for player in self.players:
            holdingbox = False
            try:
                assert isinstance(player.actor, (PlayerSpaz, type(None)))
                if (
                    player.actor
                    and player.actor.node
                    and player.actor.node.hold_node
                ):
                    holdingbox = player.actor.node.hold_node == self._box.node
            except Exception:
                print('Error checking hold box.')
            if holdingbox:
                self._holding_players.append(player)
                player.team.holdingbox = True

        if self._box is not None and self._box:
            self._box.held_by = len(self._holding_players)
            self._box._update_floatyness()

        holdingteams = set(t for t in self.teams if t.holdingbox)
        prevstate = self._box_state
        assert self._box is not None
        assert self._box.node
        if len(holdingteams) > 1:
            self._box_state = BoxState.CONTESTED
            self._scoring_team = None
        elif len(holdingteams) == 1:
            holdingteam = list(holdingteams)[0]
            self._box_state = BoxState.HELD
            self._scoring_team = holdingteam
        else:
            self._box_state = BoxState.UNCONTESTED
            self._scoring_team = None

        if self._box_state != prevstate:
            self._swipsound.play()

    def _spawn_box(self) -> None:
        self._swipsound.play()
        self._flash_box_spawn()
        self._box = MagicBox(position=self._box_spawn_pos, bomb_type='tnt')
        self._box_state = BoxState.NEW
        self._box_light = bs.newnode(
            'light',
            owner=self._box.node,
            attrs={'intensity': 0.2, 'radius': 0.3, 'color': (0.2, 0.2, 0.2)},
        )
        assert self._box.node
        self._box.node.connectattr('position', self._box_light, 'position')
        self._update_box_state()

    def _flash_box_spawn(self) -> None:
        light = bs.newnode(
            'light',
            attrs={
                'position': self._box_spawn_pos,
                'color': (1.0, 1.0, 1.0),
                'radius': 0.3,
                'height_attenuated': False,
            },
        )
        bs.animate(light, 'intensity', {0.0: 0, 0.25: 0.5, 0.5: 0}, loop=True)
        bs.timer(1.0, light.delete)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.timeremaining, self._hold_time, countdown=True
            )

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            self.respawn_player(player)
        else:
            super().handlemessage(msg)


# ba_meta export bascenev1.GameActivity
class AtomicBombGame(MagicBoxGame):
    name = CustomLang.name2
    description = CustomLang.description2

    def get_instance_description(self) -> str | Sequence:
        return CustomLang.description_short2, self._hold_time

    def get_instance_description_short(self) -> str | Sequence:
        return CustomLang.description_short2, self._hold_time

    def _spawn_box(self) -> None:
        self._swipsound.play()
        self._flash_box_spawn()
        self._box = MagicBox(position=self._box_spawn_pos, bomb_type='impact')
        self._box_state = BoxState.NEW
        self._box_light = bs.newnode(
            'light',
            owner=self._box.node,
            attrs={'intensity': 0.2, 'radius': 0.3, 'color': (0.2, 0.2, 0.2)},
        )
        assert self._box.node
        self._box.node.connectattr('position', self._box_light, 'position')
        self._update_box_state()
