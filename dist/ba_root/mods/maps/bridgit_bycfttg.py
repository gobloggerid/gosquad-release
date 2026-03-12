# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import bauiv1 as bui
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *
import random

if TYPE_CHECKING:
    from typing import Any, Dict, Sequence
    
    
class FadeEffect():
    def __init__(self, map_tint = (1,1,1)):
        gnode = bs.getactivity().globalsnode
        bs.animate_array(gnode,'tint',3,{0:(0,0,0),3:(0,0,0),3.2:map_tint})
        
        text = bs.newnode('text',
                              attrs={
                                    'position': (0,250),
                                    'text': 'Loading...',
                                    'color': (1,1,1),
                                    'h_align': 'center','v_align': 'center', 'vr_depth': 410, 'maxwidth': 600, 'shadow': 1.0, 'flatness': 1.0, 'scale':1, 'h_attach': 'center', 'v_attach': 'bottom', 'big': True})
        bs.animate(text,'opacity',{0:0,0.3:1,0.5:1,3:0})
        bs.timer(5,text.delete)
        
        text = bs.newnode('text',
                              attrs={
                                    'position': (0,270),
                                    'text': 'by HWProgram',
                                    'color': (0,0.55,0),
                                    'h_align': 'center','v_align': 'center', 'vr_depth': 410, 'maxwidth': 600, 'shadow': 1.0, 'flatness': 1.0, 'scale':1.5, 'h_attach': 'center', 'v_attach': 'bottom'})
        bs.animate(text,'opacity',{0:0,0.3:1,0.5:1,3:0})
        bs.timer(5,text.delete)
        
class BridgitBYCFTTGMapData():
    points = {}
    boxes = {}
    
    boxes['area_of_interest_bounds'] = (
        (-0.2457963347, 3.828181068, -1.528362695)
        + (0.0, 0.0, 0.0)
        + (50, 50, 50)
    )
    points['ffa_spawn1'] = (-5.869295124, 3.715437928, -1.617274877) + (
        0.9410329222,
        1.0,
        1.818908238,
    )
    points['ffa_spawn2'] = (5.160809653, 3.761793434, -1.443012115) + (
        0.7729807005,
        1.0,
        1.818908238,
    )
    points['ffa_spawn3'] = (-0.4266381164, 3.761793434, -1.555562653) + (
        4.034151421,
        1.0,
        0.2731725824,
    )
    points['ffa_spawn4'] = (-7.303694725036621, -2.7723679542541504, 0.40963172912597656) + (
        4.034151421,
        1.0,
        0.2731725824,
    )
    points['ffa_spawn5'] = (8.786172866821289, -2.6709823608398438, -0.6856467723846436) + (
        4.034151421,
        1.0,
        0.2731725824,
    )
    points['ffa_spawn3'] = (-0.3481965661048889, -2.5086278915405273, -7.1792731285095215) + (
        4.034151421,
        1.0,
        0.2731725824,
    )
    points['flag1'] = (-7.354603923, 3.770769731, -1.617274877)
    points['flag2'] = (6.885846926, 3.770685211, -1.443012115)
    points['flag_default'] = (-0.2227795102, 3.802429326, -1.562586233)
    boxes['map_bounds'] = (
        (-0.1916036665, 3, -1.311948055)
        + (0.0, 0.0, 0.0)
        + (50, 50, 50)
    )
    points['powerup_spawn1'] = (6.82849491, 4.658454461, 0.1938139802)
    points['powerup_spawn2'] = (-7.253381358, 4.728692078, 0.252121017)
    points['powerup_spawn3'] = (6.82849491, 4.658454461, -3.461765427)
    points['powerup_spawn4'] = (-7.253381358, 4.728692078, -3.40345839)
    points['powerup_spawn5'] = (3.1612396240234375, -2.7144172191619873, 0.5446292161941528)
    points['powerup_spawn6'] = (-3.8668694496154785, -2.7266013622283936, 0.20502252876758575)
    points['powerup_spawn7'] = (-3.613382577896118, -2.7159674167633057, -3.004544258117676)
    points['powerup_spawn8'] = (2.6443872451782227, -2.7167677879333496, -3.0511648654937744)
    points['shadow_lower_bottom'] = (-0.2227795102, 2.83188898, 2.680075641)
    points['shadow_lower_top'] = (-0.2227795102, 3.498267184, 2.680075641)
    points['shadow_upper_bottom'] = (-0.2227795102, 6.305086402, 2.680075641)
    points['shadow_upper_top'] = (-0.2227795102, 9.470923628, 2.680075641)
    points['spawn1'] = (-5.869295124, 3.715437928, -1.617274877) + (
        0.9410329222,
        1.0,
        1.818908238,
    )
    points['spawn2'] = (5.160809653, 3.761793434, -1.443012115) + (
        0.7729807005,
        1.0,
        1.818908238,
    )

class BridgitBYCFTTG(bs.Map):
    """Map with a narrow bridge in the middle."""

    defs = BridgitBYCFTTGMapData()
    name = 'Bridgit BYCFTTG'
    dataname = 'bridgit'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        # print('getting playtypes', cls._getdata()['play_types'])
        return ['melee', 'team_flag', 'keep_away']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bridgitPreview'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'mesh_top': bs.getmesh('bridgitLevelTop'),
            'mesh_bottom': bs.getmesh('bridgitLevelBottom'),
            'mesh_bg': bs.getmesh('natureBackground'),
            'bg_vr_fill_mesh': bs.getmesh('natureBackgroundVRFill'),
            'collision_mesh': bs.getcollisionmesh('bridgitLevelCollide'),
            'tex': bs.gettexture('bridgitLevelColor'),
            'mesh_bg_tex': bs.gettexture('natureBackgroundColor'),
            'collide_bg': bs.getcollisionmesh('natureBackgroundCollide'),
            'bgtex2': bs.gettexture('menuBG'),
            'bgmesh2': bs.getmesh('thePadBG'),
            'railing_collision_mesh': (
                bs.getcollisionmesh('bridgitLevelRailingCollide')
            ),
            'bg_material': bs.Material(),
        }
        data['bg_material'].add_actions(
            actions=('modify_part_collision', 'friction', 10.0)
        )
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh_top'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bg'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bg_vr_fill_mesh'],
                'lighting': False,
                'vr_only': True,
                'background': True,
                'color_texture': self.preloaddata['mesh_bg_tex'],
            },
        )
        self.railing = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['railing_collision_mesh'],
                'materials': [shared.railing_material],
                'bumper': True,
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['bg_material'],
                ],
            },
        )
        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh2'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )
        self._real_wall_material = bs.Material()
        self._real_wall_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True)))
        carrier = bs.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(-0.5,-2.9,0.53),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[5,0.1,1.9]})
        carrier_collide = bs.newnode('region',attrs={'position': (-0.5,-2.9,0.53),'scale': (5,0.1,1.9),'type': 'box','materials': (shared.footing_material, self._real_wall_material)})
        bs.animate_array(carrier, 'position', 3, {0:(-0.5,-2.9,0.53), 3:(-0.5,3.7,0.53), 5:(-0.5,3.7,0.53), 8:(-0.5,-2.9,0.53), 10:(-0.5,-2.9,0.53)}, loop=True)
        bs.animate_array(carrier, 'color', 3, {0:(0,0,0), 1.5:(0,0,0), 2.00:(0,0,0), 2.05:(1,1,1), 2.1:(0,0,0), 2.15:(1,1,1), 2.2:(0,0,0), 2.25:(1,1,1), 2.3:(0,0,0), 2.35:(1,1,1), 2.4:(0,0,0), 2.45:(1,1,1), 2.50:(0,0,0), 2.55:(1,1,1)}, loop=False)
        bs.animate_array(carrier_collide, 'position', 3, {0:(-0.5,-2.9,0.53), 3:(-0.5,3.7,0.53), 5:(-0.5,3.7,0.53), 8:(-0.5,-2.9,0.53), 10:(-0.5,-2.9,0.53)}, loop=True)
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.2, 1.3)
        gnode.ambient_color = (1.1, 1.2, 1.3)
        gnode.vignette_outer = (0.65, 0.6, 0.55)
        gnode.vignette_inner = (0.9, 0.9, 0.93)
        FadeEffect(gnode.tint)

        
bs.register_map(BridgitBYCFTTG)
