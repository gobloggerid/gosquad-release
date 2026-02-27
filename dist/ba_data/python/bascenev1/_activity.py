# Released under the MIT License. See LICENSE for details.
#

from __future__ import annotations
import logging,weakref
from typing import TYPE_CHECKING
import _bascenev1,babase
from bascenev1._dependency import DependencyComponent
from bascenev1._messages import UNHANDLED
if TYPE_CHECKING:from typing import Any,Self;import bascenev1
class Activity[PlayerT:bascenev1.Player,TeamT:bascenev1.Team](DependencyComponent):
	settings_raw:dict[str,Any];teams:list[TeamT];players:list[PlayerT];announce_player_deaths=False;is_joining_activity=False;allow_pausing=False;allow_kick_idle_players=True;use_fixed_vr_overlay=False;slow_motion=False;inherits_slow_motion=False;inherits_music=False;inherits_vr_camera_offset=False;inherits_vr_overlay_center=False;inherits_tint=False;allow_mid_activity_joins:bool=True;transition_time=.0;can_show_ad_on_death=False
	def __init__(self,settings):super().__init__();self._activity_data=_bascenev1.register_activity(self);assert isinstance(settings,dict);assert _bascenev1.getactivity()is self;self._globalsnode=None;(self._playertype):0;(self._teamtype):0;self._setup_player_and_team_types();self.paused_text=None;self._session=weakref.ref(_bascenev1.getsession());self.preloads={};self.settings_raw=settings;self._has_transitioned_in=False;self._has_begun=False;self._has_ended=False;self._activity_death_check_timer=None;self._expired=False;self._delay_delete_players=[];self._delay_delete_teams=[];self._players_that_left=[];self._teams_that_left=[];self._transitioning_out=False;self._actor_refs=[];self._actor_weak_refs=[];self._last_prune_dead_actors_time=babase.apptime();self._prune_dead_actors_timer=None;self.teams=[];self.players=[];self.lobby=None;self._stats=None;self._customdata={};self._customdata['hide_player_decorators']=False;self._customdata['thunder_punch_time']=-9999;self._customdata['last_masskill_message']=-9999
	def __del__(self):
		if not self._expired:
			with babase.ContextRef.empty():self._expire()
		if self._transitioning_out:
			session=self._session()
			if session is not None:babase.pushcall(babase.CallStrict(session.transitioning_out_activity_was_freed,self.can_show_ad_on_death))
	@property
	def context(self):return self._activity_data.context()
	@property
	def globalsnode(self):
		node=self._globalsnode
		if not node:raise babase.NodeNotFoundError()
		return node
	@property
	def stats(self):
		if self._stats is None:raise babase.NotFoundError()
		return self._stats
	def on_expire(self):0
	@property
	def customdata(self):assert not self._expired;assert isinstance(self._customdata,dict);return self._customdata
	@property
	def expired(self):return self._expired
	@property
	def playertype(self):return self._playertype
	@property
	def teamtype(self):return self._teamtype
	def set_has_ended(self,val):self._has_ended=val
	def expire(self):
		with babase.ContextRef.empty():ref=weakref.ref(self);self._activity_death_check_timer=babase.AppTimer(5.,babase.CallStrict(self._check_activity_death,ref,[0]),repeat=True)
		if not self._expired:
			with babase.ContextRef.empty():self._expire()
		else:raise RuntimeError(f"destroy() called when already expired for {self}.")
	def retain_actor(self,actor):
		if __debug__:from bascenev1._actor import Actor;assert isinstance(actor,Actor)
		self._actor_refs.append(actor)
	def add_actor_weak_ref(self,actor):
		if __debug__:from bascenev1._actor import Actor;assert isinstance(actor,Actor)
		self._actor_weak_refs.append(weakref.ref(actor))
	@property
	def session(self):
		session=self._session()
		if session is None:raise babase.SessionNotFoundError()
		return session
	def on_player_join(self,player):0
	def on_player_leave(self,player):0
	def on_team_join(self,team):0
	def on_team_leave(self,team):0
	def on_transition_in(self):0
	def on_transition_out(self):0
	def on_begin(self):0
	def handlemessage(self,msg):del msg;return UNHANDLED
	def has_transitioned_in(self):return self._has_transitioned_in
	def has_begun(self):return self._has_begun
	def has_ended(self):return self._has_ended
	def is_transitioning_out(self):return self._transitioning_out
	def transition_in(self,prev_globals):
		assert not self._has_transitioned_in;self._has_transitioned_in=True
		with self.context:
			glb=self._globalsnode=_bascenev1.newnode('globals');glb.use_fixed_vr_overlay=self.use_fixed_vr_overlay;glb.allow_kick_idle_players=self.allow_kick_idle_players
			if self.inherits_slow_motion and prev_globals is not None:glb.slow_motion=prev_globals.slow_motion
			else:glb.slow_motion=self.slow_motion
			if self.inherits_music and prev_globals is not None:glb.music_continuous=True;glb.music=prev_globals.music;glb.music_count+=1
			if self.inherits_vr_camera_offset and prev_globals is not None:glb.vr_camera_offset=prev_globals.vr_camera_offset
			if self.inherits_vr_overlay_center and prev_globals is not None:glb.vr_overlay_center=prev_globals.vr_overlay_center;glb.vr_overlay_center_enabled=prev_globals.vr_overlay_center_enabled
			if self.inherits_tint and prev_globals is not None:glb.tint=prev_globals.tint;glb.vignette_outer=prev_globals.vignette_outer;glb.vignette_inner=prev_globals.vignette_inner
			self._prune_dead_actors();self._prune_dead_actors_timer=_bascenev1.Timer(5.17,self._prune_dead_actors,repeat=True);_bascenev1.timer(13.3,self._prune_delay_deletes,repeat=True);self._activity_data.start()
			try:self.on_transition_in()
			except Exception:logging.exception('Error in on_transition_in for %s.',self)
		self._activity_data.make_foreground()
	def transition_out(self):
		assert not self._transitioning_out;self._transitioning_out=True
		with self.context:
			try:self.on_transition_out()
			except Exception:logging.exception('Error in on_transition_out for %s.',self)
	def begin(self,session):
		assert not self._has_begun;self._stats=session.stats
		for team in session.sessionteams:self.add_team(team)
		for player in session.sessionplayers:self.add_player(player)
		self._has_begun=True
		with self.context:self.on_begin()
	def end(self,results=None,delay=.0,force=False):self.session.end_activity(self,results,delay,force)
	def create_player(self,sessionplayer):del sessionplayer;player=self._playertype();return player
	def create_team(self,sessionteam):del sessionteam;team=self._teamtype();return team
	def add_player(self,sessionplayer):
		assert sessionplayer.sessionteam is not None;sessionplayer.resetinput();sessionteam=sessionplayer.sessionteam;assert sessionplayer in sessionteam.players;team=sessionteam.activityteam;assert team is not None;sessionplayer.setactivity(self)
		with self.context:
			sessionplayer.activityplayer=player=self.create_player(sessionplayer);player.postinit(sessionplayer);assert player not in team.players;team.players.append(player);assert player in team.players;assert player not in self.players;self.players.append(player);assert player in self.players
			try:self.on_player_join(player)
			except Exception:logging.exception('Error in on_player_join for %s.',self)
	def remove_player(self,sessionplayer):
		assert not self.expired;player=sessionplayer.activityplayer;assert isinstance(player,self._playertype);team=sessionplayer.sessionteam.activityteam;assert isinstance(team,self._teamtype);assert player in team.players;team.players.remove(player);assert player not in team.players;assert player in self.players;self.players.remove(player);assert player not in self.players
		with self.context:
			try:self.on_player_leave(player)
			except Exception:logging.exception('Error in on_player_leave for %s.',self)
			try:player.leave()
			except Exception:logging.exception('Error on leave for %s in %s.',player,self)
			self._reset_session_player_for_no_activity(sessionplayer)
		self._delay_delete_players.append(player);self._players_that_left.append(weakref.ref(player))
	def add_team(self,sessionteam):
		assert not self.expired
		with self.context:
			sessionteam.activityteam=team=self.create_team(sessionteam);team.postinit(sessionteam);self.teams.append(team)
			try:self.on_team_join(team)
			except Exception:logging.exception('Error in on_team_join for %s.',self)
	def remove_team(self,sessionteam):
		assert not self.expired;assert sessionteam.activityteam is not None;team=sessionteam.activityteam;assert isinstance(team,self._teamtype);assert team in self.teams;self.teams.remove(team);assert team not in self.teams
		with self.context:
			try:self.on_team_leave(team)
			except Exception:logging.exception('Error in on_team_leave for %s.',self)
			try:team.leave()
			except Exception:logging.exception('Error on leave for %s in %s.',team,self)
			sessionteam.activityteam=None
		self._delay_delete_teams.append(team);self._teams_that_left.append(weakref.ref(team))
	def _reset_session_player_for_no_activity(self,sessionplayer):
		try:sessionplayer.setnode(None)
		except Exception:logging.exception('Error resetting SessionPlayer node on %s for %s.',sessionplayer,self)
		try:sessionplayer.resetinput()
		except Exception:logging.exception('Error resetting SessionPlayer input on %s for %s.',sessionplayer,self)
		sessionplayer.setactivity(None);sessionplayer.activityplayer=None
	def _setup_player_and_team_types(self):
		from bascenev1._player import Player;from bascenev1._team import Team
		if not TYPE_CHECKING:
			self._playertype=type(self).__orig_bases__[-1].__args__[0]
			if not isinstance(self._playertype,type):self._playertype=Player;print(f"ERROR: {type(self)} was not passed a Player type argument; please explicitly pass bascenev1.Player if you do not want to override it.")
			self._teamtype=type(self).__orig_bases__[-1].__args__[1]
			if not isinstance(self._teamtype,type):self._teamtype=Team;print(f"ERROR: {type(self)} was not passed a Team type argument; please explicitly pass bascenev1.Team if you do not want to override it.")
		assert issubclass(self._playertype,Player);assert issubclass(self._teamtype,Team)
	@classmethod
	def _check_activity_death(cls,activity_ref,counter):
		try:
			activity=activity_ref();print('ERROR: Activity is not dying when expected:',activity,'(warning '+str(counter[0]+1)+')');print('This means something is still strong-referencing it.\nCheck out methods such as efro.debug.printrefs() to help debug this sort of thing.');counter[0]+=1
			if counter[0]==4:print('Killing app due to stuck activity... :-(');babase.quit()
		except Exception:logging.exception('Error on _check_activity_death.')
	def _expire(self):
		assert not self._expired;self._expired=True
		try:self.on_expire()
		except Exception:logging.exception('Error in Activity on_expire() for %s.',self)
		try:self._customdata=None
		except Exception:logging.exception('Error clearing customdata for %s.',self)
		self._prune_delay_deletes();self._expire_actors();self._expire_players();self._expire_teams()
		try:self._activity_data.expire()
		except Exception:logging.exception('Error expiring _activity_data for %s.',self)
	def _expire_actors(self):
		for actor_ref in self._actor_weak_refs:
			actor=actor_ref()
			if actor is not None:
				babase.verify_object_death(actor)
				try:actor.on_expire()
				except Exception:logging.exception('Error in Actor.on_expire() for %s.',actor_ref())
	def _expire_players(self):
		for ex_player in(p()for p in self._players_that_left):
			if ex_player is not None:babase.verify_object_death(ex_player)
		for player in self.players:
			babase.verify_object_death(player)
			try:player.expire()
			except Exception:logging.exception('Error expiring %s.',player)
			try:sessionplayer=player.sessionplayer;self._reset_session_player_for_no_activity(sessionplayer)
			except babase.SessionPlayerNotFoundError:pass
			except Exception:logging.exception('Error expiring %s.',player)
	def _expire_teams(self):
		for ex_team in(p()for p in self._teams_that_left):
			if ex_team is not None:babase.verify_object_death(ex_team)
		for team in self.teams:
			babase.verify_object_death(team)
			try:team.expire()
			except Exception:logging.exception('Error expiring %s.',team)
			try:sessionteam=team.sessionteam;sessionteam.activityteam=None
			except babase.SessionTeamNotFoundError:pass
			except Exception:logging.exception('Error expiring Team %s.',team)
	def _prune_delay_deletes(self):self._delay_delete_players.clear();self._delay_delete_teams.clear();self._teams_that_left=[t for t in self._teams_that_left if t()is not None];self._players_that_left=[p for p in self._players_that_left if p()is not None]
	def _prune_dead_actors(self):self._last_prune_dead_actors_time=babase.apptime();self._actor_refs=[a for a in self._actor_refs if a.exists()];self._actor_weak_refs=[a for a in self._actor_weak_refs if a()is not None]
	def set_attribute(self,attr,value):
		if not hasattr(self,attr):raise AttributeError(f"'{type(self).__name__}' has no attribute '{attr}'")
		setattr(self,attr,value)
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._activity');orig_activity=orig_module.Activity;overlay_activity=Activity
	for(name,value)in overlay_activity.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_activity,name,value)
	public_api.Activity=orig_activity;additions=[]
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])