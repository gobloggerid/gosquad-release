# ba_meta require api 9

from __future__ import annotations
from typing import TYPE_CHECKING

import random
import bascenev1 as ba
from bascenev1lib.maps import *
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, List, Dict
   
class Paradisee_defs():
    points = {}
    boxes = {}
    boxes['area_of_interest_bounds'] = (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (29.8180273, 11.57249038, 18.89134176)
    boxes['edge_box'] = (-0.103873591, 0.4133341891, 0.4294651013) + (0.0, 0.0, 0.0) + (22.48295719, 1.290242794, 8.990252454)
    points['ffa_spawn1'] = (-0.08015551329, 0.02275111462, -4.373674593) + (
        8.895057015,
        1.0,
        0.444350722,
    )
    points['ffa_spawn2'] = (-0.08015551329, 0.02275111462, 4.076288941) + (
        8.895057015,
        1.0,
        0.444350722,
    )
    points['flag1'] = (-8.95, 1.20, -1.4)
    points['flag2'] = (8.95, 1.20, -1.4)
    points['flag_default'] = (-0.1001374046, 0.04180340146, 0.1095578275)
    boxes['goal1'] = (12.22454533, 1.0, 0.1087926362) + (0.0, 0.0, 0.0) + (2.0, 2.0, 12.97466313)
    boxes['goal2'] = (-12.15961605, 1.0, 0.1097860203) + (0.0, 0.0, 0.0) + (2.0, 2.0, 13.11856424)
    boxes['map_bounds'] = (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (42.09506485, 22.81173179, 29.76723155)
    boxes['level_bounds'] = (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (42.09506485, 22.81173179, 29.76723155)
    points['powerup_spawn1'] = (-2.50, 2, 2.0)
    points['powerup_spawn2'] = (2.50, 2, -2.0)
    points['powerup_spawn3'] = (-2.50, 2, -2.0)
    points['powerup_spawn4'] = (2.50, 2, 2.0)
    points['tnt1'] = (0, 4, 0)
    points['spawn1'] = (-10.03866341, 0.02275111462, 0.0) + (0.5, 1.0, 4.0)
    points['spawn2'] = (9.823107149, 0.01092306765, 0.0) + (0.5, 1.0, 4.0)
   

def barfs():
     ba.emitfx(position=(0,0,0),
                      velocity=(0,0,0),
                      count=4,
                      scale=0.7,
                      spread=0.10,
                      chunk_type="spark")
                      
def barfss():
     ba.emitfx(position=(-10+(random.random()*30),15,-10+(random.random()*30)),
                      velocity=(0,0,0),
                      count=3,
                      scale=0.35,
                      spread=0,
                      chunk_type="spark")
                      
# deleted: lag
#def path():
# p = ba.newnode('prop', attrs={'position':(-0.50, 5, 0),'velocity':(-4.0,0,0),'sticky':False,'body':'landMine','model':ba.getmodel('landMine'),'color_texture':ba.gettexture('achievementWall'),'body_scale':1.0,'reflection': 'powerup','density':9999999999999999,'reflection_scale': [1.0],'model_scale':1.0,'gravity_scale':0,'shadow_size':0.0,'materials': [shared.footing_material]})
# ba.timer(0.15, p.delete)
# pp = ba.newnode('prop', attrs={'position':(0.50, 5, 0),'velocity':(4.0,0,0),'sticky':False,'body':'landMine','model':ba.getmodel('landMine'),'color_texture':ba.gettexture('achievementWall'),'body_scale':1.0,'reflection': 'powerup','density':9999999999999999,'reflection_scale': [1.0],'model_scale':1.0,'gravity_scale':0,'shadow_size':0.0,'materials': [shared.footing_material]})
# ba.timer(0.15, pp.delete)
                
# def landmine_Up():
# LandMine_Up = ba.newnode('prop', attrs={'position':(0, 0, 0),'velocity':(0,3,0),'sticky':False,'body':'landMine','model':ba.getmodel('landMine'),'color_texture':ba.gettexture('achievementWall'),'body_scale':5.0,'reflection': 'powerup','density':9999999999999999999999999*99999999999999999,'reflection_scale': [1.0],'model_scale':5.0,'gravity_scale':0,'shadow_size':0.0,'materials': [shared.footing_material]})
# ba.timer(0.012, LandMine_Up.delete)    
   
   
class ParadiseeMap(ba.Map):
    """Wee little map with ramps on the sides."""

    defs = Paradisee_defs()
    name = 'Paradisee'

    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee', 'keep_away', 'team_flag']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'bg'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'mesh': ba.getmesh('actionHeroUpperArm'),
            'collision_mesh': ba.getcollisionmesh('footballStadiumCollide'),
            'tex': ba.gettexture('tnt'),
            'bgtex': ba.gettexture('tipTopBGColor'),
            'bgtex2': ba.gettexture('tipTopBGColor'),
            'bgmesh': ba.getmesh('thePadBG'),
            'vr_fill_mesh': ba.getmesh('footballStadiumVRFill'),
        }
        return data

    def __init__(self) -> None:
        super().__init__(vr_overlay_offset=(0, 0, 2))
        shared = SharedObjects.get()
        self.barfs = ba.timer(1.0, ba.CallPartial(barfs), repeat=True)
        self.barfss = ba.timer(0.4, ba.CallPartial(barfss), repeat=True)
       # self.paths = ba.timer(0.3,ba.CallPartial(path), repeat=True)
       # self.up = ba.timer(0.006,ba.CallPartial(landmine_Up), repeat=True)
        self.node = ba.newnode(
            'terrain',
            delegate=self,
            attrs={
                'collision_mesh': self.preloaddata['collision_mesh'],
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'materials': [shared.footing_material]
            })       
          
        self.bg = ba.newnode('terrain',
                              attrs={
                                  'mesh': self.preloaddata['bgmesh'],
                                  'lighting': False,
                                  'background': True,
                                  'color_texture': self.preloaddata['bgtex']
                              })
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(0,0,0),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[10]})

        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.50,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.40,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.30,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.20,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.10,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.0,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.90,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.80,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.70,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.60,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.50,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.40,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.30,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.20,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.10,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.60,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.70,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.80,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.90,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.0,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.10,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.20,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.30,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.40,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.50,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.60,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.70,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.80,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.90,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,3.0,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})

        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.50,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.40,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.30,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.20,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.10,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.0,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.90,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.80,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.70,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.60,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.50,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.40,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.30,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.20,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.10,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.60,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.70,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.80,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.90,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.0,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.10,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.20,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.30,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.40,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.50,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.60,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.70,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.80,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.90,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,3.0,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})

        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.50,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.40,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.30,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.20,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.10,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.0,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.90,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.80,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.70,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.60,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.50,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.40,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.30,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.20,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,0.10,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})


        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.60,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.70,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.80,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,1.90,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.0,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.10,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.20,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.30,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.40,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.50,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.60,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.70,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.80,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,2.90,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(5.50,3.0,4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})


        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.50,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.40,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.30,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.20,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.10,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.0,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.90,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.80,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.70,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.60,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.50,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.40,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.30,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.20,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,0.10,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})


        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.60,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.70,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.80,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,1.90,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.20]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.0,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.10,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[1.0]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.20,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.90]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.30,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.80]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.40,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.70]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.50,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.60]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.60,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.50]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.70,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.40]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.80,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.30]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,2.90,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0.10]})
        self.zone = ba.newnode('locator',attrs={'shape':'circleOutline','position':(-5.50,3.0,-4.50),
                    'color':(1,1,1),'opacity':1,'draw_beauty':True,'additive':False,'size':[0]})
 
        # Visual-only markers (non-physical); avoids extreme impulses from
        # large decorative props colliding with players/bombs.
        self.powerup_left = ba.newnode(
            'locator',
            attrs={
                'shape': 'circleOutline',
                'position': (-8.50, 1.20, 0),
                'color': (1, 1, 1),
                'opacity': 0.8,
                'draw_beauty': True,
                'additive': False,
                'size': [2.2],
            },
        )
        self.powerup_right = ba.newnode(
            'locator',
            attrs={
                'shape': 'circleOutline',
                'position': (8.50, 1.20, 0),
                'color': (1, 1, 1),
                'opacity': 0.8,
                'draw_beauty': True,
                'additive': False,
                'size': [2.2],
            },
        )
    
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.0,1.0,1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
           

ba.register_map(ParadiseeMap)
