# Canvas / Paint
# Created by MattZ45986 on Github
# Updated to API9 with Claude Opus 4.6

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs

from bascenev1lib.actor.playerspaz import PlayerSpaz

if TYPE_CHECKING:
    from typing import Any, Sequence


class Dot(bs.Actor):
    """A colored circle drawn on the ground."""

    def __init__(
        self,
        position: Sequence[float] = (0, 0, 0),
        color: Sequence[float] = (0, 0, 0),
        radius: float = 0.5,
    ):
        super().__init__()
        self._r1 = max(radius, 0)
        self.position = position
        self.color = color
        n1 = bs.newnode(
            'locator',
            attrs={
                'shape': 'circle',
                'position': position,
                'color': self.color,
                'opacity': 1.0,
                'draw_beauty': True,
                'additive': True,
            },
        )
        bs.animate_array(n1, 'size', 1, {0: [0.0], 0.2: [self._r1 * 2.0]})
        self._node = n1


class Artist(PlayerSpaz):
    """A PlayerSpaz subclass with painting controls instead of combat."""

    def __init__(
        self,
        player: bs.Player,
        color: Sequence[float] = (1, 1, 1),
        highlight: Sequence[float] = (0.5, 0.5, 0.5),
        character: str = 'Spaz',
    ):
        super().__init__(
            player=player,
            color=color,
            highlight=highlight,
            character=character,
            powerups_expire=False,
        )
        self.mode = 'Draw'
        self.dot_radius = 0.5
        self.paint_color = [1.0, 0.0, 0.0]
        self.value = 1.0

    @override
    def on_bomb_press(self) -> None:
        """Bomb button: increase radius (Draw) or shift color forward (Color)."""
        if not self.node:
            return
        if self.mode == 'Draw':
            self.dot_radius += 0.1
            self.set_score_text('Radius: ' + str(round(self.dot_radius, 2)))
        elif self.mode == 'Color':
            self._shift_color(forward=True)
            c = self._get_display_color()
            self.set_score_text('COLOR', color=c)

    @override
    def on_punch_press(self) -> None:
        """Punch button: decrease radius (Draw) or shift color backward (Color)."""
        if not self.node:
            return
        if self.mode == 'Draw':
            self.dot_radius -= 0.1
            if self.dot_radius < 0.05:
                self.dot_radius = 0.0
            self.set_score_text('Radius: ' + str(round(self.dot_radius, 2)))
        elif self.mode == 'Color':
            self._shift_color(forward=False)
            c = self._get_display_color()
            self.set_score_text('COLOR', color=c)

    @override
    def on_jump_press(self) -> None:
        """Jump button: place dot (Draw) or adjust brightness (Color)."""
        if not self.node:
            return
        if self.mode == 'Draw':
            c = self._get_display_color()
            pos = self.node.position_center
            dot_pos = (pos[0], pos[1] - 2, pos[2])
            Dot(position=dot_pos, color=c, radius=self.dot_radius)
        elif self.mode == 'Color':
            self.value += 0.1
            if self.value > 1.0:
                self.value = 0.0
            c = self._get_display_color()
            self.set_score_text(
                'Value: ' + str(round(self.value, 2)), color=c
            )

    @override
    def on_pickup_press(self) -> None:
        """Pick-up button: toggle between Draw and Color modes."""
        if not self.node:
            return
        if self.mode == 'Draw':
            self.mode = 'Color'
        elif self.mode == 'Color':
            self.mode = 'Draw'
        self.set_score_text(self.mode + ' Mode')

    def _shift_color(self, forward: bool) -> None:
        """Cycle through the color wheel."""
        c = self.paint_color
        if forward:
            if c[0] >= 1:
                if c[2] == 0:
                    c[1] += 0.1
                else:
                    c[2] -= 0.1
            if c[1] >= 1:
                if c[0] == 0:
                    c[2] += 0.1
                else:
                    c[0] -= 0.1
            if c[2] >= 1:
                if c[1] == 0:
                    c[0] += 0.1
                else:
                    c[1] -= 0.1
        else:
            if c[0] >= 1:
                if c[1] == 0:
                    c[2] += 0.1
                else:
                    c[1] -= 0.1
            if c[1] >= 1:
                if c[2] == 0:
                    c[0] += 0.1
                else:
                    c[2] -= 0.1
            if c[2] >= 1:
                if c[0] == 0:
                    c[1] += 0.1
                else:
                    c[0] -= 0.1
        for i in range(3):
            c[i] = max(0.0, min(1.0, c[i]))

    def _get_display_color(self) -> tuple[float, float, float]:
        """Get current paint color adjusted by brightness value."""
        return (
            self.paint_color[0] * self.value,
            self.paint_color[1] * self.value,
            self.paint_color[2] * self.value,
        )


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""


# ba_meta export bascenev1.GameActivity
class Paint(bs.TeamGameActivity[Player, Team]):
    """A creative mode where players paint with colored dots."""

    name = 'Paint'
    description = 'Create a masterpiece.'
    scoreconfig = bs.ScoreConfig(
        label='Score', scoretype=bs.ScoreType.POINTS
    )

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(
            sessiontype,
            (
                bs.CoopSession,
                bs.DualTeamSession,
                bs.FreeForAllSession,
            ),
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Doom Shroom']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._info_text: bs.NodeActor | None = None

    @override
    def on_transition_in(self) -> None:
        super().on_transition_in()
        bs.setmusic(bs.MusicType.FORWARD_MARCH)
        self._info_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'v_attach': 'bottom',
                    'h_align': 'center',
                    'vr_depth': 0,
                    'color': (0, 0.2, 0),
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'position': (0, 0),
                    'scale': 0.8,
                    'text': 'Created by MattZ45986 on Github',
                },
            )
        )

    @override
    def on_begin(self) -> None:
        super().on_begin()

    @override
    def spawn_player_spaz(
        self,
        player: Player,
        position: Sequence[float] | None = None,
        angle: float | None = None,
    ) -> PlayerSpaz:
        # Use default map spawn point if none specified.
        if position is None:
            position = (0, 3, 0)
        color = player.color
        highlight = player.highlight
        spaz = Artist(
            player=player,
            color=color,
            highlight=highlight,
            character=player.character,
        )
        player.actor = spaz
        assert spaz.node
        spaz.node.name = player.getname()
        spaz.node.name_color = bs.safecolor(color, target_intensity=0.75)
        spaz.connect_controls_to_player()
        spaz.handlemessage(
            bs.StandMessage(position, angle if angle is not None else 90)
        )
        return spaz


# ba_meta export babase.Plugin
class PaintPlugin(babase.Plugin):
    """Plugin to register Paint as a coop practice level."""

    def on_app_running(self) -> None:
        classic = babase.app.classic
        if classic is not None:
            classic.add_coop_practice_level(
                bs.Level(
                    'Paint',
                    gametype=Paint,
                    settings={},
                    preview_texture_name='courtyardPreview',
                )
            )
