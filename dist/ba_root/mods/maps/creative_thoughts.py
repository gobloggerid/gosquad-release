from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any


class CreativeThoughts(bs.Map):
    """Freaking map by smoothy."""

    from bascenev1lib.mapdata import happy_thoughts as defs

    name = 'Creative Thoughts'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'alwaysLandPreview'

    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh': bs.getmesh('alwaysLandLevel'),
            'bottom_mesh': bs.getmesh('alwaysLandLevelBottom'),
            'bgmesh': bs.getmesh('alwaysLandBG'),
            'collision_mesh': bs.getcollisionmesh('alwaysLandLevelCollide'),
            'tex': bs.gettexture('alwaysLandLevelColor'),
            'bgtex': bs.gettexture('alwaysLandBGColor'),
            'vr_fill_mound_mesh': bs.getmesh('alwaysLandVRFillMound'),
            'vr_fill_mound_tex': bs.gettexture('vrFillMound'),
        }
        return data

    @classmethod
    def get_music_type(cls) -> bs.MusicType:
        return bs.MusicType.FLYING

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, -3.7, 2.5))
        shared = SharedObjects.get()
        self._fake_wall_material = bs.Material()
        self._real_wall_material = bs.Material()
        self._fake_wall_material.add_actions(
            conditions=(
                ('they_are_younger_than', 9000),
                'and',
                ('they_have_material', shared.player_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )
        self._real_wall_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )
        # self.node = bs.newnode(
        #     'terrain',
        #     delegate=self,
        #     attrs={
        #         'collision_mesh': self.preloaddata['collision_mesh'],
        #         'mesh': self.preloaddata['mesh'],
        #         'color_texture': self.preloaddata['tex'],
        #         'materials': [shared.footing_material,self._fake_wall_material]
        #     })
        # self.bottom = bs.newnode('terrain',
        #                          attrs={
        #                              'mesh': self.preloaddata['bottom_mesh'],
        #                              'lighting': False,
        #                              'color_texture': self.preloaddata['tex']
        #                          })
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                'background': True,
                'color_texture': bs.gettexture('rampageBGColor'),
            },
        )
        # bs.newnode('terrain',
        #            attrs={
        #                'mesh': self.preloaddata['vr_fill_mound_mesh'],
        #                'lighting': False,
        #                'vr_only': True,
        #                'color': (0.2, 0.25, 0.2),
        #                'background': True,
        #                'color_texture': self.preloaddata['vr_fill_mound_tex']
        #            })

        self.leftwall = bs.newnode(
            'region',
            attrs={
                'position': (-18.75152479, 21.057427485, -5.52),
                'scale': (2, 42, 6),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    self._real_wall_material,
                ],
            },
        )
        self.rightwall = bs.newnode(
            'region',
            attrs={
                'position': (17.65152479, 21.057427485, -5.52),
                'scale': (2, 42, 6),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    self._real_wall_material,
                ],
            },
        )
        self.topwall = bs.newnode(
            'region',
            attrs={
                'position': (-18.65152479, 21.057427485, -5.52),
                'scale': (72, 2, 6),
                'type': 'box',
                'materials': [
                    shared.footing_material,
                    self._real_wall_material,
                ],
            },
        )
        self.node_text_left = bs.newnode(
            'text',
            attrs={
                'text': '|\n|\n|\n|\n|\n\n\n\n|\n|\n|\n|\n End here \n|\n|\n|\n|\n|\n|\n|\n\n\n\n|\n|\n',
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'scale': 0.019,
                'h_align': 'center',
                'position': (-18, 20, -5),
            },
        )
        self.node_text_right = bs.newnode(
            'text',
            attrs={
                'text': '|\n|\n|\n|\n|\n\n\n\n|\n|\n|\n|\n End here \n|\n|\n|\n|\n|\n|\n|\n\n\n\n|\n|\n',
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'scale': 0.019,
                'h_align': 'center',
                'position': (17, 20, -5),
            },
        )
        self.node_text_top = bs.newnode(
            'text',
            attrs={
                'text': '_ _  _ _  _  _ _ _ _         _ _ _    _ _ _ _          _ _ _ _   _ _   _ _ _  _ _      _ _ _',
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'scale': 0.019,
                'h_align': 'center',
                'position': (0, 21, -5),
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.happy_thoughts_mode = True
        gnode.shadow_offset = (0.0, 8.0, 5.0)
        gnode.tint = (1.3, 1.23, 1.0)
        gnode.ambient_color = (1.3, 1.23, 1.0)
        gnode.vignette_outer = (0.64, 0.59, 0.69)
        gnode.vignette_inner = (0.95, 0.95, 0.93)
        gnode.vr_near_clip = 1.0
        self.is_flying = True

        # throw out some tips on flying
        txt = bs.newnode(
            'text',
            attrs={
                'text': babase.Lstr(resource='pressJumpToFlyText'),
                'scale': 1.2,
                'maxwidth': 800,
                'position': (0, 200),
                'shadow': 0.5,
                'flatness': 0.5,
                'h_align': 'center',
                'v_attach': 'bottom',
            },
        )
        cmb = bs.newnode(
            'combine',
            owner=txt,
            attrs={'size': 4, 'input0': 0.3, 'input1': 0.9, 'input2': 0.0},
        )
        bs.animate(cmb, 'input3', {3.0: 0, 4.0: 1, 9.0: 1, 10.0: 0})
        cmb.connectattr('output', txt, 'color')
        bs.timer(10.0, txt.delete)


bs._map.register_map(CreativeThoughts)
