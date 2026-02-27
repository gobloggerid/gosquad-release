# Released under the MIT License. See LICENSE for details.

# pylint: disable=too-many-lines

# ba_meta require api 9

from __future__ import annotations
from typing import TYPE_CHECKING
import bascenev1 as bs
import bauiv1 as bui
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    pass



class SoccerStadiumV2SpecialMapData():
    points = {}
    boxes = {}

    boxes['area_of_interest_bounds'] = (
        (0.0, 0.7956858119, 0.0)
        + (0.0, 0.0, 0.0)
        + (30.80223883, 0.5961646365, 13.88431707)
    )
    boxes['edge_box'] = (
        (-0.103873591, 0.4133341891, 0.4294651013)
        + (0.0, 0.0, 0.0)
        + (22.48295719, 1.290242794, 8.990252454)
    )
    points['ffa_spawn1'] =(-0.08015551329, 0.02275111462, -4.373674593) + (
    8.895057015,
    1.0,
    0.444350722,
    )
    points['ffa_spawn2'] =  (-0.08015551329, 0.02275111462, 4.076288941) + (
    8.895057015,
    1.0,
    0.444350722,
    )
    boxes['map_bounds'] = (
        (0.0, 1.185751251, 0.4326226188)
        + (0.0, 0.0, 0.0)
        + (42.09506485, 22.81173179, 29.76723155)
    )
    points['flag1'] = (-11.21689747, 0.09527878981, -0.07659307272)
    points['flag2'] = (11.08204909, 0.04119542459, -0.07659307272)
    points['flag_default'] = (-0.01690735171, 0.06139940044, -0.07659307272)
    points['puck'] = (0, -5, 0)
    boxes['goal1'] = (8.45, 1.0, 0.0) + (0.0, 0.0, 0.0) + (0.4334079123, 1.6, 3.0)
    boxes['goal2'] = (-8.45, 1.0, 0.0) + (0.0, 0.0, 0.0) + (0.4334079123, 1.6, 3.0)
    points['powerup_spawn1'] = (5.414681236, 0.9515026107, -5.037912441)
    points['powerup_spawn2'] = (-5.555402285, 0.9515026107, -5.037912441)
    points['powerup_spawn3'] = (5.414681236, 0.9515026107, 5.148223181)
    points['powerup_spawn4'] = (-5.737266365, 0.9515026107, 5.148223181)
    points['spawn1'] = (-6.835352227, 0.02305323209, 0.0) + (1.0, 1.0, 3.0)
    points['spawn2'] = (6.857415055, 0.03938567998, 0.0) + (1.0, 1.0, 3.0)
    points['tnt1'] = (-0.05791962398, 1.080990833, -4.765886164)
    points['box1'] = (-5.08421587483, 0.9515026107, -2.7762602271)


class SoccerStadiumV2Special(bs.Map):
    """Stadium map used for ice hockey games."""

    defs = SoccerStadiumV2SpecialMapData()
    name = 'Soccer Stadium V3'

    @override
    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee', 'hockey', 'team_flag', 'keep_away']

    @override
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'hockeyStadiumPreview'

    @override
    @classmethod
    def on_preload(cls) -> Any:
        data: dict[str, Any] = {
            'meshes': (
                bs.getmesh('hockeyStadiumOuter'),
                bs.getmesh('hockeyStadiumInner'),
                bs.getmesh('hockeyStadiumStands'),
            ),
            'vr_fill_mesh': bs.getmesh('footballStadiumVRFill'),
            'collision_mesh': bs.getcollisionmesh('hockeyStadiumCollide'),
            'tex': bs.gettexture('hockeyStadium'),
            'stands_tex': bs.gettexture('footballStadium'),
        }
        mat = bs.Material()
        data['ice_material'] = mat
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['meshes'][0],
                'collision_mesh': self.preloaddata['collision_mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [
                    shared.footing_material,
                    self.preloaddata['ice_material'],
                ],
            },
        )
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['vr_fill_mesh'],
                'vr_only': True,
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['stands_tex'],
            },
        )
        mats = [shared.footing_material, self.preloaddata['ice_material']]
        self.floor = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['meshes'][1],
                'color_texture': bs.gettexture('white'),
                'opacity': 0.92,
                'opacity_in_low_or_medium_quality': 1.0,
                'materials': mats,
                'color': (0, 0.50, 0),
            },
        )
        self.stands = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['meshes'][2],
                'visible_in_reflections': False,
                'color_texture': self.preloaddata['stands_tex'],
                'color': (0, 0.20, 1.00)
            },
        )
        
        ###
        node = bs.newnode('text', attrs={
            'text': "           \ue043 \nTOURNAMENT",
            'color': (1, 1, 1),
            'opacity': 0.9, 
            'position': (-8.7, 2.3, -6), 
            'scale': 0.0300, 
            'in_world': True,
            'shadow': 0.5
            })
        
        ###   
        color = (1,1,1),
        opacity = 1                                    
        pos1 = [(0.00000001,0.01,0.00000001)]
        for m_pos in pos1:
            node = bs.newnode('locator',attrs={'shape':'circleOutline','position':m_pos, 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':[2.8]})  
            node = bs.newnode('locator',attrs={'shape':'box','position':(-7.3, 0.00, 0.0), 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':(1.7, 0.01, 3.7)})       
            node = bs.newnode('locator',attrs={'shape':'box','position':(7.3, 0.00, 0.0), 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':(1.7, 0.01, 3.7)})       
            node = bs.newnode('locator',attrs={'shape':'box','position':(0.0, 1.5, -6), 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':(18.7, 0.05, 2.9)})



        pos2 = [(0.000001,0.02,0.0000001)]
        for m_pos1 in pos2:  
            node = bs.newnode('locator',attrs={'shape':'circle','position':(4.2, 0.01,0), 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':[0.2]})
            node = bs.newnode('locator',attrs={'shape':'circle','position':(-4.2, 0.01, 0), 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':[0.2]})
        #Line Central
        node = bs.newnode('locator',attrs={'shape':'circle','position':m_pos, 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':(0.09,100,1000.5)})
        node = bs.newnode('locator',attrs={'shape':'circle','position':(-8.1,0.01,0.0), 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':(0.09,100,1000.5)})
        node = bs.newnode('locator',attrs={'shape':'circle','position':(8.1,0.01,0.0), 'color':color, 'opacity':opacity, 'drawShadow': False,  'draw_beauty':True, 'additive':False, 'size':(0.09,100,1000.5)})
        
        gnode = bs.getactivity().globalsnode
        gnode.floor_reflection = False
        gnode.debris_friction = 0.3
        gnode.debris_kill_height = -0.3
        gnode.tint = (1.2, 1.3, 1.33)
        gnode.ambient_color = (1.15, 1.25, 1.6)
        gnode.vignette_outer = (0.66, 0.67, 0.73)
        gnode.vignette_inner = (0.93, 0.93, 0.95)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
        self.is_hockey = False

        
_map.register_map(SoccerStadiumV2Special)

