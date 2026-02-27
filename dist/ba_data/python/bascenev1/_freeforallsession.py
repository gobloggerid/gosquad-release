# Released under the MIT License. See LICENSE for details.
#

from __future__ import annotations
from typing import TYPE_CHECKING,override
import _bascenev1,babase
from bascenev1._multiteamsession import MultiTeamSession
if TYPE_CHECKING:import bascenev1
class FreeForAllSession(MultiTeamSession):
	use_teams=False;use_team_colors=False;_playlist_selection_var='Free-for-All Playlist Selection';_playlist_randomize_var='Free-for-All Playlist Randomize';_playlists_var='Free-for-All Playlists'
	def get_ffa_point_awards(self):
		point_awards:0
		if len(self.sessionplayers)==1:point_awards={0:3}
		elif len(self.sessionplayers)==2:point_awards={0:6}
		elif len(self.sessionplayers)==3:point_awards={0:6,1:3}
		elif len(self.sessionplayers)==4 or len(self.sessionplayers)==5:point_awards={0:8,1:4,2:2}
		elif len(self.sessionplayers)==6:point_awards={0:8,1:4,2:2,3:1}
		elif len(self.sessionplayers)==7 or len(self.sessionplayers)==8:point_awards={0:10,1:6,2:4,3:2}
		else:point_awards={0:10,1:6,2:4,3:2,4:1}
		return point_awards
	def __init__(self):babase.increment_analytics_count('Free-for-all session start');super().__init__()
	@override
	def _switch_to_score_screen(self,results):
		from bascenev1lib.activity.drawscore import DrawScoreScreenActivity;from bascenev1lib.activity.freeforallvictory import FreeForAllVictoryScoreScreenActivity;from bascenev1lib.activity.multiteamvictory import TeamSeriesVictoryScoreScreenActivity;from efro.util import asserttype;winners=results.winnergroups
		if len(self.sessionplayers)>1 and len(winners)<2:self.setactivity(_bascenev1.newactivity(DrawScoreScreenActivity,{'results':results}))
		else:
			point_awards=self.get_ffa_point_awards()
			for(i,winner)in enumerate(winners):
				for team in winner.teams:points=point_awards[i]if i in point_awards else 0;team.customdata['previous_score']=team.customdata['score'];team.customdata['score']+=points
			series_winners=[team for team in self.sessionteams if team.customdata['score']>=self._ffa_series_length];series_winners.sort(reverse=True,key=lambda t:asserttype(t.customdata['score'],int))
			if len(series_winners)==1 or len(series_winners)>1 and series_winners[0].customdata['score']!=series_winners[1].customdata['score']:self.setactivity(_bascenev1.newactivity(TeamSeriesVictoryScoreScreenActivity,{'winner':series_winners[0]}))
			else:self.setactivity(_bascenev1.newactivity(FreeForAllVictoryScoreScreenActivity,{'results':results}))
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._freeforallsession');orig_session=orig_module.FreeForAllSession;overlay_session=FreeForAllSession
	for(name,value)in overlay_session.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_session,name,value)
	public_api.FreeForAllSession=orig_session;additions=[]
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])