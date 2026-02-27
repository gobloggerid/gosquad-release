# Released under the MIT License. See LICENSE for details.
#

from __future__ import annotations
import logging,weakref
from typing import TYPE_CHECKING,overload
import _bascenev1,babase
from bascenev1._messages import UNHANDLED,DeathType,DieMessage,OutOfBoundsMessage
if TYPE_CHECKING:from typing import Any,Literal,Self;import bascenev1
class ActorMode:0
class SmashActorMode(ActorMode):0
class Actor:
	def __init__(self):
		if __debug__:self._root_actor_init_called=True
		activity=_bascenev1.getactivity();self._activity=weakref.ref(activity);activity.add_actor_weak_ref(self);self.mode=None
	def __del__(self):
		try:
			if not self.expired:self.handlemessage(DieMessage())
		except Exception:logging.exception('Error in bascenev1.Actor.__del__() for %s.',self)
	def handlemessage(self,msg):
		assert not self.expired
		if isinstance(msg,OutOfBoundsMessage):return self.handlemessage(DieMessage(how=DeathType.OUT_OF_BOUNDS))
		return UNHANDLED
	def autoretain(self):
		activity=self._activity()
		if activity is None:raise babase.ActivityNotFoundError()
		activity.retain_actor(self);return self
	def on_expire(self):0
	@property
	def expired(self):activity=self.getactivity(doraise=False);return True if activity is None else activity.expired
	def exists(self):return True
	def __bool__(self):return self.exists()
	def is_alive(self):return True
	@property
	def activity(self):
		activity=self._activity()
		if activity is None:raise babase.ActivityNotFoundError()
		return activity
	@overload
	def getactivity(self,doraise=True):...
	@overload
	def getactivity(self,doraise):...
	def getactivity(self,doraise=True):
		activity=self._activity()
		if activity is None and doraise:raise babase.ActivityNotFoundError()
		return activity
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._actor');orig_actor=orig_module.Actor;overlay_actor=Actor
	for(name,value)in overlay_actor.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_actor,name,value)
	public_api.Actor=orig_actor;additions=['ActorMode','SmashActorMode']
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])