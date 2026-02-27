# Released under the MIT License. See LICENSE for details.
#

from __future__ import annotations
import logging,math,weakref
from typing import TYPE_CHECKING
import _bascenev1,babase
from bascenev1._player import Player
if TYPE_CHECKING:from collections.abc import Sequence;from typing import Any;import bascenev1
_g_player_rejoin_cooldown=.0
_g_max_players_override=None
def set_player_rejoin_cooldown(cooldown):global _g_player_rejoin_cooldown;_g_player_rejoin_cooldown=max(.0,cooldown)
def set_max_players_override(max_players):global _g_max_players_override;_g_max_players_override=max_players
class Session:
	use_teams:bool=False;use_team_colors:bool=True;lobby:bascenev1.Lobby;max_players:int;min_players:int;sessionplayers:list[bascenev1.SessionPlayer];customdata:dict;sessionteams:list[bascenev1.SessionTeam]
	def __init__(self,depsets,*,team_names=None,team_colors=None,min_players=1,max_players=21,submit_score=True):
		from bascenev1._activity import Activity;from bascenev1._dependency import AssetPackage,Dependency,DependencyError;from bascenev1._gameactivity import GameActivity;from bascenev1._lobby import Lobby;from bascenev1._stats import Stats;from bascenev1._team import SessionTeam;from efro.util import empty_weakref;missing_asset_packages=set()
		for depset in depsets:
			try:depset.resolve()
			except DependencyError as exc:
				if all(issubclass(d.cls,AssetPackage)for d in exc.deps):
					for dep in exc.deps:assert isinstance(dep.config,str);missing_asset_packages.add(dep.config)
				else:missing_info=[(d.cls,d.config)for d in exc.deps];raise RuntimeError(f"Missing non-asset dependencies: {missing_info}")from exc
		if missing_asset_packages:raise DependencyError([Dependency(AssetPackage,set_id)for set_id in missing_asset_packages])
		required_asset_packages=set()
		for depset in depsets:required_asset_packages.update(depset.get_asset_package_ids())
		self._sessiondata=_bascenev1.register_session(self);self.tournament_id=None;self.sessionteams=[];self.sessionplayers=[];self.min_players=min_players;self.max_players=max_players if _g_max_players_override is None else _g_max_players_override;self.submit_score=submit_score;self.customdata={};self._saved_scores={};self._in_set_activity=False;self._next_team_id=0;self._activity_retained=None;self._launch_end_session_activity_time=None;self._activity_end_timer=None;self._activity_weak=empty_weakref(Activity);self._next_activity=None;self._wants_to_end=False;self._ending=False;self._activity_should_end_immediately=False;self._activity_should_end_immediately_results=None;self._activity_should_end_immediately_delay=.0
		if self.use_teams:
			if team_names is None:raise RuntimeError('use_teams is True but team_names not provided.')
			if team_colors is None:raise RuntimeError('use_teams is True but team_colors not provided.')
			if len(team_colors)!=len(team_names):raise RuntimeError(f"Got {len(team_names)} team_names and {len(team_colors)} team_colors; these numbers must match.")
			for(i,color)in enumerate(team_colors):
				team=SessionTeam(team_id=self._next_team_id,name=GameActivity.get_team_display_string(team_names[i]),color=color);self.sessionteams.append(team);self._next_team_id+=1
				try:
					with self.context:self.on_team_join(team)
				except Exception:logging.exception('Error in on_team_join for %s.',self)
		self.lobby=Lobby();self.stats=Stats();self._sessionglobalsnode=_bascenev1.newnode('sessionglobals');self._players_on_wait={};self._player_requested_identifiers={};self._waitlist_timers={}
	@property
	def context(self):return self._sessiondata.context()
	@property
	def sessionglobalsnode(self):
		node=self._sessionglobalsnode
		if not node:raise babase.NodeNotFoundError()
		return node
	def should_allow_mid_activity_joins(self,activity):del activity;return True
	def on_player_request(self,player):
		if babase.app.classic is not None and babase.app.classic.stress_test_update_timer is None:
			if len(self.sessionplayers)>=self.max_players>=0:_bascenev1.getsound('error').play();_bascenev1.broadcastmessage(babase.Lstr(resource='playerLimitReachedText',subs=[('${COUNT}',str(self.max_players))]),color=(.8,.0,.0),clients=[player.inputdevice.client_id],transient=True);return False
		identifier=player.get_v1_account_id()
		if identifier:
			leave_time=self._players_on_wait.get(identifier)
			if leave_time:diff=str(math.ceil(_g_player_rejoin_cooldown-babase.apptime()+leave_time));_bascenev1.broadcastmessage(babase.Lstr(translate=('serverResponses','You can join in ${COUNT} seconds.'),subs=[('${COUNT}',diff)]),color=(1,1,0),clients=[player.inputdevice.client_id],transient=True);return False
			self._player_requested_identifiers[player.id]=identifier
		_bascenev1.getsound('dripity').play();return True
	def on_player_leave(self,sessionplayer):
		if sessionplayer not in self.sessionplayers:print('ERROR: Session.on_player_leave called for player not in our list.');return
		_bascenev1.getsound('playerLeft').play();activity=self._activity_weak();identifier=self._player_requested_identifiers.get(sessionplayer.id)
		if identifier:
			self._players_on_wait[identifier]=babase.apptime()
			with babase.ContextRef.empty():self._waitlist_timers[identifier]=babase.AppTimer(_g_player_rejoin_cooldown,babase.CallStrict(self._remove_player_from_waitlist,identifier))
		if not sessionplayer.in_game:
			with self.context:
				try:self.lobby.remove_chooser(sessionplayer)
				except Exception:logging.exception('Error in Lobby.remove_chooser().')
		else:
			sessionteam=sessionplayer.sessionteam;assert sessionteam is not None;_bascenev1.broadcastmessage(babase.Lstr(resource='playerLeftText',subs=[('${PLAYER}',sessionplayer.getname(full=True))]))
			if sessionplayer in sessionteam.players:sessionteam.players.remove(sessionplayer)
			else:print('SessionPlayer not found in SessionTeam in on_player_leave.')
			if not self.use_teams:acid=sessionplayer.get_v1_account_id();name=sessionplayer.getname();key=f"{acid}:{name}";self._saved_scores[key]=sessionteam.customdata['score']
			player=sessionplayer.activityplayer;assert isinstance(player,Player|None)
			if player is not None and activity is not None:
				if player in activity.players:activity.remove_player(sessionplayer)
				else:print('Player not found in Activity in on_player_leave.')
			if not self.use_teams:self._remove_player_team(sessionteam,activity)
		self.sessionplayers.remove(sessionplayer)
	def _remove_player_team(self,sessionteam,activity):
		assert not sessionteam.players
		if activity is not None:
			if sessionteam.activityteam in activity.teams:activity.remove_team(sessionteam)
		with self.context:
			if sessionteam in self.sessionteams:
				try:self.sessionteams.remove(sessionteam);self.on_team_leave(sessionteam)
				except Exception:logging.exception('Error in on_team_leave for Session %s.',self)
			else:print('Team no in Session teams in on_player_leave.')
			try:sessionteam.leave()
			except Exception:logging.exception('Error clearing sessiondata for team %s in session %s.',sessionteam,self)
	def end(self):
		self._wants_to_end=True
		if self._next_activity is None:self._launch_end_session_activity()
	def _launch_end_session_activity(self):
		from bascenev1._activitytypes import EndSessionActivity
		with self.context:
			curtime=babase.apptime()
			if self._ending:
				assert self._launch_end_session_activity_time is not None;since_last=curtime-self._launch_end_session_activity_time
				if since_last<3e1:return
				logging.error('_launch_end_session_activity called twice (since_last=%s)',since_last)
			self._launch_end_session_activity_time=curtime;self.setactivity(_bascenev1.newactivity(EndSessionActivity));self._wants_to_end=False;self._ending=True
	def on_team_join(self,team):0
	def on_team_leave(self,team):0
	def end_activity(self,activity,results,delay,force):
		if activity is not self._activity_retained:return
		if not activity.has_begun():
			if not self._activity_should_end_immediately or force:self._activity_should_end_immediately=True;self._activity_should_end_immediately_results=results;self._activity_should_end_immediately_delay=delay
		elif not activity.has_ended()or force:activity.set_has_ended(True);self._activity_end_timer=_bascenev1.BaseTimer(delay,babase.CallStrict(self._complete_end_activity,activity,results))
	def handlemessage(self,msg):
		from bascenev1._lobby import PlayerReadyMessage;from bascenev1._messages import UNHANDLED,PlayerProfilesChangedMessage
		if isinstance(msg,PlayerReadyMessage):self._on_player_ready(msg.chooser)
		elif isinstance(msg,PlayerProfilesChangedMessage):
			with self.context:self.lobby.reload_profiles()
			return None
		else:return UNHANDLED
		return None
	class _SetActivityScopedLock:
		def __init__(self,session):
			self._session=session
			if session._in_set_activity:raise RuntimeError('Session.setactivity() called recursively.')
			self._session._in_set_activity=True
		def __del__(self):self._session._in_set_activity=False
	def setactivity(self,activity):
		_rlock=self._SetActivityScopedLock(self)
		if activity.session is not _bascenev1.getsession():raise RuntimeError("Provided Activity's Session is not current.")
		if self._ending:return
		if activity is self._activity_retained:logging.error('Activity set to already-current activity.');return
		if self._next_activity is not None:raise RuntimeError('Activity switch already in progress (to '+str(self._next_activity)+')')
		prev_activity=self._activity_retained;prev_globals=prev_activity.globalsnode if prev_activity is not None else None;activity.transition_in(prev_globals);self._next_activity=activity
		if prev_activity is not None:prev_activity.transition_out();self._activity_retained=None
		else:self.begin_next_activity()
		if prev_activity is not None:
			with babase.ContextRef.empty():babase.apptimer(max(.0,activity.transition_time),prev_activity.expire)
		self._in_set_activity=False
	def getactivity(self):return self._activity_weak()
	def get_custom_menu_entries(self):return[]
	def _complete_end_activity(self,activity,results):
		try:
			with self.context:self.on_activity_end(activity,results)
		except Exception:logging.error('Error in on_activity_end() for session %s activity %s with results %s',self,activity,results)
	def _request_player(self,sessionplayer):
		if self._ending:return False
		try:
			with self.context:result=self.on_player_request(sessionplayer)
		except Exception:logging.exception('Error in on_player_request for %s.',self);result=False
		if result:
			self.sessionplayers.append(sessionplayer)
			with self.context:
				try:self.lobby.add_chooser(sessionplayer)
				except Exception:logging.exception('Error in lobby.add_chooser().')
		return result
	def on_activity_end(self,activity,results):0
	def begin_next_activity(self):
		if self._next_activity is None:logging.error('begin_next_activity() called with no _next_activity');return
		self._activity_retained=self._next_activity;self._activity_weak=weakref.ref(self._next_activity);self._next_activity=None;self._activity_should_end_immediately=False;self.lobby.remove_all_choosers_and_kick_players();self._activity_retained.begin(self)
		if self._wants_to_end:self._launch_end_session_activity()
		elif self._activity_should_end_immediately:self._activity_retained.end(self._activity_should_end_immediately_results,self._activity_should_end_immediately_delay)
	def _on_player_ready(self,chooser):
		lobby=chooser.lobby;activity=self._activity_weak()
		if activity is None:print('_on_player_ready called with no activity.');return
		if activity.is_joining_activity:
			if not lobby.check_all_ready():return
			choosers=lobby.get_choosers();min_players=self.min_players
			if len(choosers)>=min_players:
				for lch in lobby.get_choosers():self._add_chosen_player(lch)
				lobby.remove_all_choosers();self._complete_end_activity(activity,{})
			else:_bascenev1.broadcastmessage(babase.Lstr(resource='notEnoughPlayersText',subs=[('${COUNT}',str(min_players))]),color=(1,1,0));_bascenev1.getsound('error').play()
		else:self._add_chosen_player(chooser);lobby.remove_chooser(chooser.getplayer())
	def transitioning_out_activity_was_freed(self,can_show_ad_on_death):
		babase.app.gc.collect();classic=babase.app.classic;plus=babase.app.plus;assert classic is not None;assert plus is not None
		with self.context:
			if can_show_ad_on_death and classic.can_show_interstitial():plus.ads.call_after_ad(self.begin_next_activity)
			else:babase.pushcall(self.begin_next_activity)
	def _add_chosen_player(self,chooser):
		from bascenev1._team import SessionTeam;sessionplayer=chooser.getplayer();assert sessionplayer in self.sessionplayers,'SessionPlayer not found in session player-list after chooser selection.';activity=self._activity_weak();assert activity is not None;sessionplayer.resetinput();pass_to_activity=activity.has_begun()and not activity.is_joining_activity
		if pass_to_activity:
			if not(activity.allow_mid_activity_joins and self.should_allow_mid_activity_joins(activity)):
				pass_to_activity=False
				with self.context:_bascenev1.broadcastmessage(babase.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',sessionplayer.getname(full=True))]),color=(0,1,0))
		if self.use_teams:sessionteam=chooser.sessionteam
		else:
			our_team_id=self._next_team_id;self._next_team_id+=1;sessionteam=SessionTeam(team_id=our_team_id,color=chooser.get_color(),name=chooser.getplayer().getname(full=True,icon=False));self.sessionteams.append(sessionteam)
			with self.context:
				try:self.on_team_join(sessionteam)
				except Exception:logging.exception('Error in on_team_join for %s.',self)
			if pass_to_activity:activity.add_team(sessionteam)
		assert sessionplayer not in sessionteam.players;sessionteam.players.append(sessionplayer);sessionplayer.setdata(team=sessionteam,character=chooser.get_character_name(),color=chooser.get_color(),highlight=chooser.get_highlight());self.stats.register_sessionplayer(sessionplayer)
		if pass_to_activity:activity.add_player(sessionplayer)
		if not self.use_teams:
			acid=sessionplayer.get_v1_account_id();name=sessionplayer.getname();key=f"{acid}:{name}"
			if key in self._saved_scores:sessionteam.customdata['score']=self._saved_scores[key];sessionteam.customdata['previous_score']=self._saved_scores[key]
		return sessionplayer
	def _remove_player_from_waitlist(self,identifier):
		try:self._players_on_wait.pop(identifier)
		except KeyError:pass
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._session');orig_session=orig_module.Session;overlay_session=Session
	for(name,value)in overlay_session.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_session,name,value)
	public_api.Session=orig_session;additions=['set_player_rejoin_cooldown','set_max_players_override']
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])