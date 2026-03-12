# ba_meta require api 9
from __future__ import annotations
from typing import TYPE_CHECKING
import bascenev1 as ba
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    from typing import List, Dict, Any

class MyMapPoints:
    # This file was automatically generated from "hockey_stadium.ma"
    # pylint: disable=all
    points = {}
    # noinspection PyDictCreation
    boxes = {}
    boxes['area_of_interest_bounds'] = (0.0, 0.7956858119, 0.0) + (
        0.0, 0.0, 0.0) + (30.80223883, 0.5961646365, 13.88431707)
    boxes['map_bounds'] = (0.0, 0.7956858119, -0.4689020853) + (0.0, 0.0, 0.0) + (
        35.16182389, 12.18696164, 21.52869693)
    points['ffa_spawn1'] = (-6.25, 1.0, -2.0) + (
        0.5, 1.0, 5.5)
    points['ffa_spawn2'] = (6.25, 1.0, -2.0) + (
        0.5, 1.0, 5.5)
    points['ffa_spawn3'] = (0.0, 1.0, 4.25) + (
        4.5, 1.0, 0.5)
    points['ffa_spawn4'] = (0.0, 1.0, -8.25) + (
        4.5, 1.0, 0.5)
    points['spawn1'] = (-6.25, 1.0, -3.0)
    points['spawn2'] = (6.25, 1.0, -1.0)
    # Disabled old outer-corner powerup spawns.
    points['old_powerup_spawn1'] = (6.25, 1.0, 4.25)
    points['old_powerup_spawn2'] = (-6.25, 1.0, 4.25)
    points['old_powerup_spawn3'] = (6.25, 1.0, -8.25)
    points['old_powerup_spawn4'] = (-6.25, 1.0, -8.25)
    points['powerup_spawn1'] = (3.75, 1.0, 1.75)
    points['powerup_spawn2'] = (-3.75, 1.0, 1.75)
    points['powerup_spawn3'] = (3.75, 1.0, -5.75)
    points['powerup_spawn4'] = (-3.75, 1.0, -5.75)
    points['flag_default'] = (0.0, -0.5, -2.0)
    points['tnt1'] = (0.0, -0.25, -2.0)
    points['flag1'] = (-6.25, 1.0, -2.0)
    points['flag2'] = (6.25, 1.0, -2.0)
    

class MyMap(ba.Map):

    defs = MyMapPoints
    name = 'Icy Arena'

    @classmethod
    def get_play_types(cls) -> List[str]:
        return ['melee', 'keep_away', 'team_flag', 'king_of_the_hill']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'white'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {}
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.locs = []
        self.regions = []
        
##SpecialMaterials###################
        
        self.collision = ba.Material()
        self.collision.add_actions(
            actions=(('modify_part_collision', 'collide', True)))
            
        self.nothing = ba.Material()
        self.nothing.add_actions(
            actions=(('modify_part_collision', 'collide', False)))
            
        self.ice = ba.Material()
        self.ice.add_actions(
            actions =(('modify_part_collision', 'collide', True), ('modify_part_collision', 'friction', 0.2,)))

##Color###############################

        set = [
              dict(position=(0.0, 0.0, -2.0), color=(0.0, 0.75, 1.0), size=(10.0, 0.01, 10.0)),
              dict(position=(0.0, 0.0, -2.0), color=(0.0, 0.75, 1.0), size=(16.0, 0.01, 16.0)),
              ]

        for a, map in enumerate(set):
            self.locs.append(
                ba.newnode('locator',
                    attrs={'shape': 'box',
                           'position': set[a]['position'],
                           'color': set[a]['color'],
                           'opacity': 1.0,
                           'draw_beauty': True,
                           'size': set[a]['size'],
                           'additive': False}))
                           
            self.regions.append(
                ba.newnode('region',
                    attrs={'scale': tuple(set[a]['size']),
                           'type': 'box',
                           'materials': [self.nothing,
                                         shared.footing_material]}))
            self.locs[-1].connectattr('position', self.regions[-1], 'position')
            
##Material###############################

        set = [
              dict(position=(0.0, 0.15, -10.0), color=(0.0, 0.0, 0.0), size=(16.0, 0.3, 0.01)),
              dict(position=(0.0, 0.15, 6.0), color=(0.0, 0.0, 0.0), size=(16.0, 0.3, 0.01)),
              dict(position=(-8.0, 0.15, -2.0), color=(0.0, 0.0, 0.0), size=(0.01, 0.3, 16.0)),
              dict(position=(8.0, 0.15, -2.0), color=(0.0, 0.0, 0.0), size=(0.01, 0.3, 16.0)),
              dict(position=(6.5, 0.0, -2.0), color=(0.0, 0.0, 0.0), size=(3.0, 0.01, 16.0)),
              dict(position=(-6.5, 0.0, -2.0), color=(0.0, 0.0, 0.0), size=(3.0, 0.01, 16.0)),
              dict(position=(0.0, 0.0, 4.5), color=(0.0, 0.0, 0.0), size=(10.0, 0.01, 3.0)),
              dict(position=(0.0, 0.0, -8.5), color=(0.0, 0.0, 0.0), size=(10.0, 0.01, 3.0)),
              ]

        for b, map in enumerate(set):
            self.locs.append(
                ba.newnode('locator',
                    attrs={'shape': 'box',
                           'position': set[b]['position'],
                           'color': set[b]['color'],
                           'opacity': 1.0,
                           'draw_beauty': False,
                           'size': set[b]['size'],
                           'additive': False}))
                           
            self.regions.append(
                ba.newnode('region',
                    attrs={'scale': tuple(set[b]['size']),
                           'type': 'box',
                           'materials': [self.collision,
                                         shared.footing_material]}))
            self.locs[-1].connectattr('position', self.regions[-1], 'position')
            
##ColorAndMaterial###############################

        set = [
              dict(position=(0.0, -1.0, -2.0), color=(0.75, 1.0, 1.0), size=(9.5, 0.01, 9.5)),
              dict(position=(0.0, -0.5, -6.75), color=(0.75, 1.0, 1.0), size=(9.5, 1.0, 0.01)),
              dict(position=(0.0, -0.5, 2.75), color=(0.75, 1.0, 1.0), size=(9.5, 1.0, 0.01)),
              dict(position=(-4.75, -0.5, -2.0), color=(0.75, 1.0, 1.0), size=(0.01, 1.0, 9.5)),
              dict(position=(4.75, -0.5, -2.0), color=(0.75, 1.0, 1.0), size=(0.01, 1.0, 9.5)),
              ]

        for c, map in enumerate(set):
            self.locs.append(
                ba.newnode('locator',
                    attrs={'shape': 'box',
                           'position': set[c]['position'],
                           'color': set[c]['color'],
                           'opacity': 1.0,
                           'draw_beauty': True,
                           'size': set[c]['size'],
                           'additive': False}))
                           
            self.regions.append(
                ba.newnode('region',
                    attrs={'scale': tuple(set[c]['size']),
                           'type': 'box',
                           'materials': [self.ice,
                                         shared.footing_material]}))
            self.locs[-1].connectattr('position', self.regions[-1], 'position')

##Other###########################

        self.background = ba.newnode(
            'terrain',
            attrs={
                'mesh': ba.getmesh('thePadBG'),
                'lighting': False,
                'background': True,
                'color': (0.25, 0.25, 0.25),
                'color_texture': ba.gettexture('white')})

        gnode = ba.getactivity().globalsnode
        gnode.tint = (0.8, 0.9, 1.3)
        gnode.ambient_color = (0.8, 0.9, 1.3)
        gnode.vignette_outer = (0.79, 0.79, 0.69)
        gnode.vignette_inner = (0.97, 0.97, 0.99)


ba.register_map(MyMap)
