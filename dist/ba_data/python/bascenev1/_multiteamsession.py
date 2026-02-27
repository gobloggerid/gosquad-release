# Released under the MIT License. See LICENSE for details.
#

from __future__ import annotations
import copy,logging,random
from typing import TYPE_CHECKING,override
import _bascenev1,babase
from bascenev1._session import Session
if TYPE_CHECKING:from collections.abc import Sequence;from typing import Any;import bascenev1
DEFAULT_TEAM_COLORS=(.1,.25,1.),(1.,.25,.2)
DEFAULT_TEAM_NAMES='Merah','Putih'
class MultiTeamSession(Session):
	_playlist_selection_var='UNSET Playlist Selection';_playlist_randomize_var='UNSET Playlist Randomize';_playlists_var='UNSET Playlists'
	def __init__(self):
		from bascenev1 import _playlist;from bascenev1lib.activity.multiteamjoin import MultiTeamJoinActivity;app=babase.app;classic=app.classic;assert classic is not None;cfg=app.config
		if self.use_teams:team_names=cfg.get('Custom Team Names',DEFAULT_TEAM_NAMES);team_colors=cfg.get('Custom Team Colors',DEFAULT_TEAM_COLORS)
		else:team_names=None;team_colors=None
		depsets=[];super().__init__(depsets,team_names=team_names,team_colors=team_colors,min_players=1,max_players=self.get_max_players());self._series_length=int(cfg.get('Teams Series Length',7));self._ffa_series_length=int(cfg.get('FFA Series Length',30));show_tutorial=cfg.get('Show Tutorial',True)
		if classic.stress_test_update_timer is not None:show_tutorial=False
		(self._tutorial_activity_instance):0
		if show_tutorial:from bascenev1lib.tutorial import TutorialActivity;tutorial_activity=TutorialActivity;self._tutorial_activity_instance=_bascenev1.newactivity(tutorial_activity)
		else:self._tutorial_activity_instance=None
		self._playlist_name=cfg.get(self._playlist_selection_var,'__default__');self._playlist_randomize=cfg.get(self._playlist_randomize_var,False);self._game_number=0;playlists=cfg.get(self._playlists_var,{})
		if self._playlist_name!='__default__'and self._playlist_name in playlists:playlist=copy.deepcopy(playlists[self._playlist_name])
		elif self.use_teams:playlist=_playlist.get_default_teams_playlist()
		else:playlist=_playlist.get_default_free_for_all_playlist()
		playlist_resolved=_playlist.filter_playlist(playlist,sessiontype=type(self),add_resolved_type=True,name='default teams'if self.use_teams else'default ffa')
		if not playlist_resolved:raise RuntimeError('Playlist contains no valid games.')
		self._playlist=ShuffleList(playlist_resolved,shuffle=self._playlist_randomize);self._current_game_spec=None;self._next_game_spec=self._playlist.pull_next();self._next_game=self._next_game_spec['resolved_type'];self._instantiate_next_game();self.setactivity(_bascenev1.newactivity(MultiTeamJoinActivity))
	def get_ffa_series_length(self):return self._ffa_series_length
	def get_series_length(self):return self._series_length
	def get_next_game_description(self):from bascenev1._gameactivity import GameActivity;gametype=self._next_game_spec['resolved_type'];assert issubclass(gametype,GameActivity);return gametype.get_settings_display_string(self._next_game_spec)
	def get_game_number(self):return self._game_number
	@override
	def on_team_join(self,team):team.customdata['previous_score']=team.customdata['score']=0
	def get_max_players(self):
		if self.use_teams:val=babase.app.config.get('Team Game Max Players',21)
		else:val=babase.app.config.get('Free-for-All Max Players',21)
		assert isinstance(val,int);return val
	def _instantiate_next_game(self):self._next_game_instance=_bascenev1.newactivity(self._next_game_spec['resolved_type'],self._next_game_spec['settings'])
	@override
	def on_activity_end(self,activity,results):
		from bascenev1._activitytypes import JoinActivity,ScoreScreenActivity,TransitionActivity;from bascenev1lib.activity.multiteamvictory import TeamSeriesVictoryScoreScreenActivity;from bascenev1lib.tutorial import TutorialActivity
		if self._tutorial_activity_instance is not None:self.setactivity(self._tutorial_activity_instance);self._tutorial_activity_instance=None
		elif isinstance(activity,TutorialActivity):self.setactivity(_bascenev1.newactivity(TransitionActivity))
		elif isinstance(activity,(JoinActivity,TransitionActivity,ScoreScreenActivity)):
			if isinstance(activity,TeamSeriesVictoryScoreScreenActivity):
				self.stats.reset();self._game_number=0
				for team in self.sessionteams:team.customdata['score']=0
			else:self.stats.reset_accum()
			next_game=self._next_game_instance;self._current_game_spec=self._next_game_spec;self._next_game_spec=self._playlist.pull_next();self._game_number+=1;self._instantiate_next_game()
			for player in self.sessionplayers:
				try:has_team=player.sessionteam is not None
				except babase.NotFoundError:has_team=False
				if has_team:self.stats.register_sessionplayer(player)
			self.stats.setactivity(next_game);self.setactivity(next_game)
		else:self._switch_to_score_screen(results)
	def _switch_to_score_screen(self,results):del results;logging.error('This should be overridden.',stack_info=True)
	def announce_game_results(self,activity,results,delay,announce_winning_team=True):
		from bascenev1._freeforallsession import FreeForAllSession;from bascenev1._gameutils import cameraflash;from bascenev1._messages import CelebrateMessage,TextMessage;from textlibs.manager import textlist;_bascenev1.timer(delay,_bascenev1.getsound('boxingBell').play)
		if announce_winning_team:
			winning_sessionteam=results.winning_sessionteam
			if winning_sessionteam is not None:
				celebrate_msg=CelebrateMessage(duration=1e1);assert winning_sessionteam.activityteam is not None;players=winning_sessionteam.activityteam.players
				for player in players:
					if player.actor:player.actor.handlemessage(celebrate_msg)
				if isinstance(self,FreeForAllSession):celeb_text=textlist.get('celebrate_messages')
				elif not isinstance(self,FreeForAllSession)and len(players)>1:celeb_text=textlist.get('celebrate_messages_team')
				else:celeb_text=textlist.get('celebrate_messages')
				text_msg=TextMessage(text=celeb_text,color='random',screen=True)
				for player in players:
					if player.actor:player.actor.handlemessage(text_msg);break
				cameraflash()
				if isinstance(self,FreeForAllSession):wins_resource='winsPlayerText'
				else:wins_resource='winsTeamText'
				wins_text=babase.Lstr(resource=wins_resource,subs=[('${NAME}',winning_sessionteam.name)]);activity.show_zoom_message(wins_text,scale=.85,color=babase.normalized_color(winning_sessionteam.color))
class ShuffleList:
	def __init__(self,items,shuffle=True):self.source_list=items;self.shuffle=shuffle;self.shuffle_list=[];self.last_gotten=None
	def pull_next(self):
		if not self.shuffle_list:self.shuffle_list=list(self.source_list)
		index=0
		if self.shuffle:
			for _i in range(4):
				index=random.randrange(0,len(self.shuffle_list));test_obj=self.shuffle_list[index]
				if len(self.shuffle_list)>1 and self.last_gotten is not None:
					if test_obj['settings']['map']==self.last_gotten['settings']['map']:continue
					if test_obj['type']==self.last_gotten['type']:continue
				break
		obj=self.shuffle_list.pop(index);self.last_gotten=obj;return obj
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._multiteamsession');orig_session=orig_module.MultiTeamSession;overlay_session=MultiTeamSession
	for(name,value)in overlay_session.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_session,name,value)
	public_api.MultiTeamSession=orig_session;additions=[]
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])