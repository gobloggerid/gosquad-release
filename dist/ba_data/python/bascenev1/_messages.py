# Released under the MIT License. See LICENSE for details.
#

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
import babase
if TYPE_CHECKING:from collections.abc import Sequence;from typing import Any;import bascenev1
class _UnhandledType:0
UNHANDLED=_UnhandledType()
@dataclass
class OutOfBoundsMessage:0
class DeathType(Enum):GENERIC='generic';OUT_OF_BOUNDS='out_of_bounds';IMPACT='impact';FALL='fall';REACHED_GOAL='reached_goal';LEFT_GAME='left_game';EXPLODE='explode'
@dataclass
class DieMessage:immediate:bool=False;how:DeathType=DeathType.GENERIC
class PlayerDiedMessage:
	killed:bool;how:DeathType
	def __init__(self,player,was_killed,killerplayer,how):assert player.exists();self._player=player;assert killerplayer is None or killerplayer.exists();self._killerplayer=killerplayer;self.killed=was_killed;self.how=how
	def getkillerplayer[PlayerT:bascenev1.Player](self,playertype):assert isinstance(self._killerplayer,playertype|None);return self._killerplayer
	def getplayer[PlayerT:bascenev1.Player](self,playertype):player=self._player;assert isinstance(player,playertype);assert player.exists();return player
@dataclass
class StandMessage:position:Sequence[float]=(.0,.0,.0);angle:float=.0
@dataclass
class PickUpMessage:node:bascenev1.Node
@dataclass
class DropMessage:0
@dataclass
class PickedUpMessage:node:bascenev1.Node
@dataclass
class DroppedMessage:node:bascenev1.Node
@dataclass
class ShouldShatterMessage:extreme:bool=False
@dataclass
class ImpactDamageMessage:intensity:float
@dataclass
class FreezeMessage:time:float=5.
@dataclass
class ThawMessage:0
@dataclass
class CelebrateMessage:duration:float=1e1
class HitMessage:
	def __init__(self,*,srcnode=None,pos=None,velocity=None,magnitude=1.,velocity_magnitude=.0,radius=1.,source_player=None,kick_back=1.,flat_damage=None,hit_type='generic',force_direction=None,hit_subtype='default'):self.srcnode=srcnode;self.pos=pos if pos is not None else babase.Vec3();self.velocity=velocity if velocity is not None else babase.Vec3();self.magnitude=magnitude;self.velocity_magnitude=velocity_magnitude;self.radius=radius;assert source_player is None or source_player.exists();self._source_player=source_player;self.kick_back=kick_back;self.flat_damage=flat_damage;self.hit_type=hit_type;self.hit_subtype=hit_subtype;self.force_direction=force_direction if force_direction is not None else velocity
	def get_source_player[PlayerT:bascenev1.Player](self,playertype):player=self._source_player;assert player is None or player.exists();return player if isinstance(player,playertype)else None
@dataclass
class PlayerProfilesChangedMessage:0
@dataclass
class ShatterMessage:0
@dataclass
class UniteMessage:0
@dataclass
class DisorientMessage:0
@dataclass
class TextMessage:text:str='';icon:str='📢';color:str='white';animate:bool=False;screen:bool=False
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._messages');orig_shouldshatter=orig_module.ShouldShatterMessage;overlay_shouldshatter=ShouldShatterMessage
	for(name,value)in overlay_shouldshatter.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_shouldshatter,name,value)
	public_api.ShouldShatterMessage=orig_shouldshatter;additions=['ShatterMessage','UniteMessage','DisorientMessage','TextMessage']
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])