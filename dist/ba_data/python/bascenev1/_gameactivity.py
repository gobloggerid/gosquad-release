# Released under the MIT License. See LICENSE for details.
# Modified for gosquad server.
#

from __future__ import annotations
import logging,random,time,uuid
from typing import TYPE_CHECKING,override
import _bascenev1,babase
from bascenev1 import _map,_music
from bascenev1._activity import Activity
from bascenev1._messages import PlayerDiedMessage,StandMessage
from bascenev1._player import PlayerInfo
from bascenev1._score import ScoreConfig
if TYPE_CHECKING:from collections.abc import Sequence;from typing import Any;import bascenev1;from bascenev1lib.actor.bomb import TNTSpawner;from bascenev1lib.actor.playerspaz import PlayerSpaz;from bascenev1lib.actor.spaz import Spaz
class GameActivity[PlayerT:bascenev1.Player,TeamT:bascenev1.Team](Activity[PlayerT,TeamT]):
	tips:list[str|bascenev1.GameTip]=[];name:str|None=None;description:str|None=None;available_settings:list[bascenev1.Setting]|None=None;scoreconfig:bascenev1.ScoreConfig|None=None;allow_pausing=True;allow_kick_idle_players=True;show_kill_points=True;default_music:bascenev1.MusicType|None=None
	@classmethod
	def getscoreconfig(cls):return cls.scoreconfig if cls.scoreconfig is not None else ScoreConfig()
	@classmethod
	def getname(cls):return cls.name if cls.name is not None else'Untitled Game'
	@classmethod
	def get_display_string(cls,settings=None):
		name=babase.Lstr(translate=('gameNames',cls.getname()))
		if settings is not None:
			if'Solo Mode'in settings and settings['Solo Mode']:name=babase.Lstr(resource='soloNameFilterText',subs=[('${NAME}',name)])
			if'Epic Mode'in settings and settings['Epic Mode']:name=babase.Lstr(resource='epicNameFilterText',subs=[('${NAME}',name)])
		return name
	@classmethod
	def get_team_display_string(cls,name):return babase.Lstr(translate=('teamNames',name))
	@classmethod
	def get_description(cls,sessiontype):del sessiontype;return cls.description if cls.description is not None else''
	@classmethod
	def get_description_display_string(cls,sessiontype):description=cls.get_description(sessiontype);return babase.Lstr(translate=('gameDescriptions',description))
	@classmethod
	def get_available_settings(cls,sessiontype):del sessiontype;return[]if cls.available_settings is None else cls.available_settings
	@classmethod
	def get_supported_maps(cls,sessiontype):del sessiontype;assert babase.app.classic is not None;return babase.app.classic.getmaps('melee')
	@classmethod
	def get_settings_display_string(cls,config):
		name=cls.get_display_string(config['settings'])
		if'map'in config['settings']:sval=babase.Lstr(value='${NAME} @ ${MAP}',subs=[('${NAME}',name),('${MAP}',_map.get_map_display_string(_map.get_filtered_map_name(config['settings']['map'])))])
		elif'map'in config:sval=babase.Lstr(value='${NAME} @ ${MAP}',subs=[('${NAME}',name),('${MAP}',_map.get_map_display_string(_map.get_filtered_map_name(config['map'])))])
		else:print('invalid game config - expected map entry under settings');sval=babase.Lstr(value='???')
		return sval
	@classmethod
	def supports_session_type(cls,sessiontype):from bascenev1._multiteamsession import MultiTeamSession;return issubclass(sessiontype,MultiTeamSession)
	def __init__(self,settings):super().__init__(settings);self.initialplayerinfos=None;self._map_type=_map.get_map_class(self._calc_map_name(settings));self._spawn_sound=_bascenev1.getsound('spawn');self._map_type.preload();self._map=None;self._powerup_drop_timer=None;self._tnt_spawners=None;self._tnt_drop_timer=None;self._game_scoreboard_name_text=None;self._game_scoreboard_description_text=None;self._standard_time_limit_time=None;self._standard_time_limit_timer=None;self._standard_time_limit_text=None;self._standard_time_limit_text_input=None;self._tournament_time_limit=None;self._tournament_time_limit_timer=None;self._tournament_time_limit_title_text=None;self._tournament_time_limit_text=None;self._tournament_time_limit_text_input=None;self._zoom_message_times={}
	@property
	def map(self):
		if self._map is None:raise babase.MapNotFoundError
		return self._map
	def get_instance_display_string(self):return self.get_display_string(self.settings_raw)
	def get_instance_scoreboard_display_string(self):
		try:
			from bascenev1._coopsession import CoopSession
			if isinstance(self.session,CoopSession):campaign=self.session.campaign;assert campaign is not None;return campaign.getlevel(self.session.campaign_level_name).displayname
		except Exception:logging.exception('Error getting campaign level name.')
		return self.get_instance_display_string()
	def get_instance_description(self):return self.get_description(type(self.session))
	def get_instance_description_short(self):return''
	@override
	def on_transition_in(self):
		Activity.on_transition_in(self);self._map=self._map_type();mapname=getattr(self._map_type,'name',None);map_preview=getattr(self._map_type,'get_preview_texture_name',None)
		if babase.app.discord.is_ready and mapname and map_preview:preview=map_preview().lower().removesuffix('preview');babase.app.discord.set_presence(state=self.getname(),details=f"Playing on {mapname}",large_image_key=preview,large_image_text=mapname,small_image_key=babase.app.classic.platform if babase.app.classic else None,small_image_text=babase.app.classic.platform if babase.app.classic else None,start_timestamp=int(time.time()))
		map_music=self._map_type.get_music_type();music=map_music if map_music is not None else self.default_music
		if music is not None:_music.setmusic(music)
	@override
	def on_begin(self):
		Activity.on_begin(self)
		if babase.app.classic is not None:babase.app.classic.game_begin_analytics()
		if babase.app.discord.is_ready:party_size=len(self.players);max_size=max(8,party_size);babase.app.discord.set_presence(party_id=str(uuid.uuid4()),party_size=(party_size,max_size))
		_bascenev1.timer(.001,self._show_scoreboard_info);_bascenev1.timer(1.,self._show_info);_bascenev1.timer(2.5,self._show_tip);self.initialplayerinfos=[PlayerInfo(name=p.getname(full=True),character=p.character)for p in self.players];self.initialplayerinfos.sort(key=lambda x:x.name);tournament_id=self.session.tournament_id
		if tournament_id is not None:assert babase.app.plus is not None;babase.app.plus.tournament_query(args={'tournamentIDs':[tournament_id],'source':'in-game time remaining query'},callback=babase.WeakCallPartial(self._on_tournament_query_response))
	def _on_tournament_query_response(self,data):
		if data is not None:data_t=data['t'];assert babase.app.classic is not None;babase.app.classic.accounts.cache_tournament_info(data_t);self._setup_tournament_time_limit(max(5,data_t[0]['timeRemaining']))
	@override
	def on_player_join(self,player):Activity.on_player_join(self,player);self.spawn_player(player)
	@override
	def handlemessage(self,msg):
		if isinstance(msg,PlayerDiedMessage):
			from bascenev1lib.actor.spaz import Spaz;player=msg.getplayer(self.playertype);killer=msg.getkillerplayer(self.playertype);self.stats.player_was_killed(player,killed=msg.killed,killer=killer)
			if killer and killer.team is not player.team:
				assert isinstance(killer.actor,Spaz);pts,importance=killer.actor.get_death_points(msg.how)
				if not self.has_ended():self.stats.player_scored(killer,pts,kill=True,victim_player=player,importance=importance,showpoints=self.show_kill_points)
		else:return Activity.handlemessage(self,msg)
		return None
	def _show_scoreboard_info(self):
		from bascenev1._freeforallsession import FreeForAllSession;from bascenev1._gameutils import animate;from bascenev1._nodeactor import NodeActor;sb_name=self.get_instance_scoreboard_display_string();sb_desc_in=self.get_instance_description_short();sb_desc_l:0
		if isinstance(sb_desc_in,str):sb_desc_l=[sb_desc_in]
		else:sb_desc_l=sb_desc_in
		if not isinstance(sb_desc_l[0],str):raise TypeError('Invalid format for instance description.')
		is_empty=sb_desc_l[0]=='';subs=[]
		for i in range(len(sb_desc_l)-1):subs.append(('${ARG'+str(i+1)+'}',str(sb_desc_l[i+1])))
		translation=babase.Lstr(translate=('gameDescriptions',sb_desc_l[0]),subs=subs);sb_desc=translation;vrmode=babase.app.env.vr;yval=-34 if is_empty else-20;yval-=16;sbpos=(15,yval)if isinstance(self.session,FreeForAllSession)else(15,yval);self._game_scoreboard_name_text=NodeActor(_bascenev1.newnode('text',attrs={'text':sb_name,'maxwidth':300,'position':sbpos,'h_attach':'left','vr_depth':10,'v_attach':'top','v_align':'bottom','color':(1.,1.,1.,1.),'shadow':1. if vrmode else .6,'flatness':1. if vrmode else .5,'scale':1.1}));assert self._game_scoreboard_name_text.node;animate(self._game_scoreboard_name_text.node,'opacity',{0:.0,1.:1.});descpos=(17,-34)if isinstance(self.session,FreeForAllSession)else(17,-34);self._game_scoreboard_description_text=NodeActor(_bascenev1.newnode('text',attrs={'text':sb_desc,'maxwidth':480,'position':descpos,'scale':.7,'h_attach':'left','v_attach':'top','v_align':'top','shadow':1. if vrmode else .7,'flatness':1. if vrmode else .8,'color':(1,1,1,1)if vrmode else(.9,.9,.9,1.)}));assert self._game_scoreboard_description_text.node;animate(self._game_scoreboard_description_text.node,'opacity',{0:.0,1.:1.})
	def _show_info(self):
		from bascenev1._gameutils import animate;from bascenev1lib.actor.zoomtext import ZoomText;name=self.get_instance_display_string();ZoomText(name,maxwidth=800,lifespan=2.5,jitter=2.,position=(0,180),flash=False,color=(1.1625,1.125,1.25),trailcolor=(.15,.05,1.,.0)).autoretain();_bascenev1.timer(.2,_bascenev1.getsound('gong').play);desc_in=self.get_instance_description();desc_l:0
		if isinstance(desc_in,str):desc_l=[desc_in]
		else:desc_l=desc_in
		if not isinstance(desc_l[0],str):raise TypeError('Invalid format for instance description')
		subs=[]
		for i in range(len(desc_l)-1):subs.append(('${ARG'+str(i+1)+'}',str(desc_l[i+1])))
		translation=babase.Lstr(translate=('gameDescriptions',desc_l[0]),subs=subs)
		if self.settings_raw.get('Epic Mode',False):translation=babase.Lstr(resource='epicDescriptionFilterText',subs=[('${DESCRIPTION}',translation)])
		vrmode=babase.app.env.vr;dnode=_bascenev1.newnode('text',attrs={'v_attach':'center','h_attach':'center','h_align':'center','color':(1,1,1,1),'shadow':1. if vrmode else .5,'flatness':1. if vrmode else .5,'vr_depth':-30,'position':(0,80),'scale':1.2,'maxwidth':700,'text':translation});cnode=_bascenev1.newnode('combine',owner=dnode,attrs={'input0':1.,'input1':1.,'input2':1.,'size':4});cnode.connectattr('output',dnode,'color');keys={.5:0,1.:1.,2.5:1.,4.:.0};animate(cnode,'input3',keys);_bascenev1.timer(4.,dnode.delete)
	def _show_tip(self):
		from bascenev1._gameutils import GameTip,animate
		if self.tips:
			tip=self.tips.pop(random.randrange(len(self.tips)));tip_title=babase.Lstr(value='${A}:',subs=[('${A}',babase.Lstr(resource='tipText'))]);icon=None;sound=None
			if isinstance(tip,GameTip):icon=tip.icon;sound=tip.sound;tip=tip.text;assert isinstance(tip,str)
			tip_lstr=babase.Lstr(translate=('tips',tip),subs=[('${PICKUP}',babase.charstr(babase.SpecialChar.TOP_BUTTON))]);base_position=75,50;tip_scale=.8;tip_title_scale=1.2;vrmode=babase.app.env.vr;t_offs=-35e1;tnode=_bascenev1.newnode('text',attrs={'text':tip_lstr,'scale':tip_scale,'maxwidth':900,'position':(base_position[0]+t_offs,base_position[1]),'h_align':'left','vr_depth':300,'shadow':1. if vrmode else .5,'flatness':1. if vrmode else .5,'v_align':'center','v_attach':'bottom'});t2pos=base_position[0]+t_offs-(20 if icon is None else 82),base_position[1]+2;t2node=_bascenev1.newnode('text',owner=tnode,attrs={'text':tip_title,'scale':tip_title_scale,'position':t2pos,'h_align':'right','vr_depth':300,'shadow':1. if vrmode else .5,'flatness':1. if vrmode else .5,'maxwidth':140,'v_align':'center','v_attach':'bottom'})
			if icon is not None:ipos=base_position[0]+t_offs-40,base_position[1]+1;img=_bascenev1.newnode('image',attrs={'texture':icon,'position':ipos,'scale':(50,50),'opacity':1.,'vr_depth':315,'color':(1,1,1),'absolute_scale':True,'attach':'bottomCenter'});animate(img,'opacity',{0:0,1.:1,4.:1,5.:0});_bascenev1.timer(5.,img.delete)
			if sound is not None:sound.play()
			combine=_bascenev1.newnode('combine',owner=tnode,attrs={'input0':1.,'input1':.8,'input2':1.,'size':4});combine.connectattr('output',tnode,'color');combine.connectattr('output',t2node,'color');animate(combine,'input3',{0:0,1.:1,4.:1,5.:0});_bascenev1.timer(5.,tnode.delete)
	@override
	def end(self,results=None,delay=.0,force=False):
		from bascenev1._gameresults import GameResults
		if isinstance(results,GameResults):results.set_game(self)
		if self._standard_time_limit_time is not None and self._standard_time_limit_time>0:self._standard_time_limit_timer=None;self._standard_time_limit_text=None
		if self._tournament_time_limit is not None and self._tournament_time_limit>0:self._tournament_time_limit_timer=None;self._tournament_time_limit_text=None;self._tournament_time_limit_title_text=None
		if delay<4.:delay=4.
		Activity.end(self,results,delay,force)
	def end_game(self):print('WARNING: default end_game() implementation called; your game should override this.')
	def respawn_player(self,player,respawn_time=None):
		assert player
		if respawn_time is None:
			teamsize=len(player.team.players)
			if teamsize==1:respawn_time=1.
			elif teamsize==2:respawn_time=2.
			else:respawn_time=3.
		if'Respawn Times'in self.settings_raw:respawn_time*=self.settings_raw['Respawn Times']
		assert respawn_time is not None;respawn_time=round(max(1.,respawn_time),0)
		if player.actor and not self.has_ended():from bascenev1lib.actor.respawnicon import RespawnIcon;player.customdata['respawn_timer']=_bascenev1.Timer(respawn_time,babase.WeakCallStrict(self.spawn_player_if_exists,player));player.customdata['respawn_icon']=RespawnIcon(player,respawn_time)
	def spawn_player_if_exists(self,player):
		if player:self.spawn_player(player)
	def spawn_player(self,player):assert player;return self.spawn_player_spaz(player)
	def spawn_player_spaz(self,player,position=(0,0,0),angle=None):
		from bascenev1._coopsession import CoopSession;from bascenev1._gameutils import animate;from bascenev1lib.actor.playerspaz import PlayerSpaz;from gobase.godata import Hide;name=player.getname();color=player.color;highlight=player.highlight;acid=player.sessionplayer.get_v1_account_id();playerspaztype=getattr(player,'playerspaztype',PlayerSpaz)
		if not issubclass(playerspaztype,PlayerSpaz):playerspaztype=PlayerSpaz
		light_color=babase.normalized_color(color);display_color=babase.safecolor(color,target_intensity=.75);spaz=playerspaztype(color=color,highlight=highlight,character=player.character,player=player);player.actor=spaz;assert spaz.node
		if isinstance(self.session,CoopSession)and self.map.getname()in['Courtyard','Tower D']:mat=self.map.preloaddata['collide_with_wall_material'];assert isinstance(spaz.node.materials,tuple);assert isinstance(spaz.node.roller_materials,tuple);spaz.node.materials+=mat,;spaz.node.roller_materials+=mat,
		spaz.node.name=''if Hide.is_hidden(acid,'name')else name;spaz.node.name_color=display_color;spaz.connect_controls_to_player();spaz.handlemessage(StandMessage(position,angle if angle is not None else random.uniform(0,360)));self._spawn_sound.play(1,position=spaz.node.position);light=_bascenev1.newnode('light',attrs={'color':light_color});spaz.node.connectattr('position',light,'position');animate(light,'intensity',{0:0,.25:1,.5:0});_bascenev1.timer(.5,light.delete);return spaz
	def setup_standard_powerup_drops(self,enable_tnt=True):
		from bascenev1lib.actor.powerupbox import DEFAULT_POWERUP_INTERVAL;self._powerup_drop_timer=_bascenev1.Timer(DEFAULT_POWERUP_INTERVAL,babase.WeakCallStrict(self._standard_drop_powerups),repeat=True);self._standard_drop_powerups()
		if enable_tnt:self._tnt_spawners={};self._setup_standard_tnt_drops()
	def _standard_drop_powerup(self,index,expire=True):from bascenev1lib.actor.powerupbox import PowerupBox,PowerupBoxFactory;PowerupBox(position=self.map.powerup_spawn_points[index],poweruptype=PowerupBoxFactory.get().get_random_powerup_type(),expire=expire).autoretain()
	def _standard_drop_powerups(self):
		points=self.map.powerup_spawn_points
		for i in range(len(points)):_bascenev1.timer(i*.4,babase.WeakCallStrict(self._standard_drop_powerup,i))
	def _setup_standard_tnt_drops(self):
		from bascenev1lib.actor.bomb import TNTSpawner
		for(i,point)in enumerate(self.map.tnt_points):
			assert self._tnt_spawners is not None
			if self._tnt_spawners.get(i)is None:self._tnt_spawners[i]=TNTSpawner(point)
	def setup_standard_time_limit(self,duration):
		from bascenev1._nodeactor import NodeActor
		if duration<=.0:return
		self._standard_time_limit_time=int(duration);self._standard_time_limit_timer=_bascenev1.Timer(1.,babase.WeakCallStrict(self._standard_time_limit_tick),repeat=True);self._standard_time_limit_text=NodeActor(_bascenev1.newnode('text',attrs={'v_attach':'top','h_attach':'center','h_align':'left','color':(1.,1.,1.,.5),'position':(-25,-30),'flatness':1.,'scale':.9}));self._standard_time_limit_text_input=NodeActor(_bascenev1.newnode('timedisplay',attrs={'time2':duration*1000,'timemin':0}));self.globalsnode.connectattr('time',self._standard_time_limit_text_input.node,'time1');assert self._standard_time_limit_text_input.node;assert self._standard_time_limit_text.node;self._standard_time_limit_text_input.node.connectattr('output',self._standard_time_limit_text.node,'text')
	def _standard_time_limit_tick(self):
		from bascenev1._gameutils import animate;assert self._standard_time_limit_time is not None;self._standard_time_limit_time-=1
		if self._standard_time_limit_time<=10:
			if self._standard_time_limit_time==10:assert self._standard_time_limit_text is not None;assert self._standard_time_limit_text.node;self._standard_time_limit_text.node.scale=1.3;self._standard_time_limit_text.node.position=-30,-45;cnode=_bascenev1.newnode('combine',owner=self._standard_time_limit_text.node,attrs={'size':4});cnode.connectattr('output',self._standard_time_limit_text.node,'color');animate(cnode,'input0',{0:1,.15:1},loop=True);animate(cnode,'input1',{0:1,.15:.5},loop=True);animate(cnode,'input2',{0:.1,.15:.0},loop=True);cnode.input3=1.
			_bascenev1.getsound('tick').play()
		if self._standard_time_limit_time<=0:self._standard_time_limit_timer=None;self.end_game();node=_bascenev1.newnode('text',attrs={'v_attach':'top','h_attach':'center','h_align':'center','color':(1,.7,0,1),'position':(0,-90),'scale':1.2,'text':babase.Lstr(resource='timeExpiredText')});_bascenev1.getsound('refWhistle').play();animate(node,'scale',{.0:.0,.1:1.4,.15:1.2})
	def _setup_tournament_time_limit(self,duration):
		from bascenev1._nodeactor import NodeActor
		if duration<=.0:return
		self._tournament_time_limit=int(duration);self._tournament_time_limit_timer=_bascenev1.BaseTimer(1.,babase.WeakCallStrict(self._tournament_time_limit_tick),repeat=True);self._tournament_time_limit_title_text=NodeActor(_bascenev1.newnode('text',attrs={'v_attach':'bottom','h_attach':'right','h_align':'center','v_align':'center','vr_depth':300,'maxwidth':100,'color':(1.,1.,1.,.5),'position':(-60,50),'flatness':1.,'scale':.5,'text':babase.Lstr(resource='tournamentText')}));self._tournament_time_limit_text=NodeActor(_bascenev1.newnode('text',attrs={'v_attach':'bottom','h_attach':'right','h_align':'center','v_align':'center','vr_depth':300,'maxwidth':100,'color':(1.,1.,1.,.5),'position':(-60,30),'flatness':1.,'scale':.9}));self._tournament_time_limit_text_input=NodeActor(_bascenev1.newnode('timedisplay',attrs={'timemin':0,'time2':self._tournament_time_limit*1000}));assert self._tournament_time_limit_text.node;assert self._tournament_time_limit_text_input.node;self._tournament_time_limit_text_input.node.connectattr('output',self._tournament_time_limit_text.node,'text')
	def _tournament_time_limit_tick(self):
		from bascenev1._gameutils import animate;assert self._tournament_time_limit is not None;self._tournament_time_limit-=1
		if self._tournament_time_limit<=10:
			if self._tournament_time_limit==10:assert self._tournament_time_limit_title_text is not None;assert self._tournament_time_limit_title_text.node;assert self._tournament_time_limit_text is not None;assert self._tournament_time_limit_text.node;self._tournament_time_limit_title_text.node.scale=1.;self._tournament_time_limit_text.node.scale=1.3;self._tournament_time_limit_title_text.node.position=-80,85;self._tournament_time_limit_text.node.position=-80,60;cnode=_bascenev1.newnode('combine',owner=self._tournament_time_limit_text.node,attrs={'size':4});cnode.connectattr('output',self._tournament_time_limit_title_text.node,'color');cnode.connectattr('output',self._tournament_time_limit_text.node,'color');animate(cnode,'input0',{0:1,.15:1},loop=True);animate(cnode,'input1',{0:1,.15:.5},loop=True);animate(cnode,'input2',{0:.1,.15:.0},loop=True);cnode.input3=1.
			_bascenev1.getsound('tick').play()
		if self._tournament_time_limit<=0:self._tournament_time_limit_timer=None;self.end_game();tval=babase.Lstr(resource='tournamentTimeExpiredText',fallback_resource='timeExpiredText');node=_bascenev1.newnode('text',attrs={'v_attach':'top','h_attach':'center','h_align':'center','color':(1,.7,0,1),'position':(0,-200),'scale':1.6,'text':tval});_bascenev1.getsound('refWhistle').play();animate(node,'scale',{0:.0,.1:1.4,.15:1.2})
		assert self._tournament_time_limit_text_input is not None;assert self._tournament_time_limit_text_input.node;self._tournament_time_limit_text_input.node.time2=self._tournament_time_limit*1000
	def show_zoom_message(self,message,*,color=(.9,.4,.0),scale=.8,duration=2.,trail=False):
		from bascenev1lib.actor.zoomtext import ZoomText;i=0;cur_time=babase.apptime()
		while True:
			if i not in self._zoom_message_times or self._zoom_message_times[i]<cur_time:self._zoom_message_times[i]=cur_time+duration;break
			i+=1
		ZoomText(message,lifespan=duration,jitter=2.,position=(0,200-i*100),scale=scale,maxwidth=800,trail=trail,color=color).autoretain()
	def _calc_map_name(self,settings):
		map_name:0
		if'map'in settings:map_name=settings['map']
		else:
			unowned_maps=babase.app.classic.store.get_unowned_maps()if babase.app.classic is not None else[];valid_maps=[m for m in self.get_supported_maps(type(self.session))if m not in unowned_maps]
			if not valid_maps:_bascenev1.broadcastmessage(babase.Lstr(resource='noValidMapsErrorText'));raise RuntimeError('No valid maps')
			map_name=valid_maps[random.randrange(len(valid_maps))]
		return map_name
	def activate_low_gravity(self,duration=None):
		from bascenev1lib.actor.bomb import Bomb;from bascenev1lib.actor.powerupbox import PowerupBox;from bascenev1lib.actor.spaz import Spaz;_bascenev1.broadcastmessage('Gravity Falls!',color=(1,0,1),clients=None);data=self.customdata;data['gravity_mult']=.3
		try:
			for node in _bascenev1.getnodes():
				delegate=node.getdelegate(object)
				if isinstance(delegate,Spaz):delegate._gravity_timer=_bascenev1.Timer(.016666667,babase.WeakCallStrict(delegate._update_gravity),True)
				elif isinstance(delegate,(Bomb,PowerupBox)):
					if not node.exists():continue
					node.gravity_scale=.3;node.velocity=random.randrange(-2,2),7,random.randrange(-2,2)
		except Exception as e:print(f"Error changing gravity: {e}.");return
		if duration:data['gravity_timer']=_bascenev1.Timer(duration,babase.WeakCallStrict(self._reset_low_gravity))
	def _reset_low_gravity(self):self.customdata['gravity_mult']=1.
	def activate_icy_ground(self,duration=None):
		from bascenev1lib.gameutils import SharedObjects;data=self.customdata
		if data.get('icy_active',False)and duration is not None:data['icy_timer']=_bascenev1.Timer(duration,babase.WeakCallStrict(self._reset_icy_ground));_bascenev1.getsound('hiss').play(2.);return
		shared=SharedObjects.get();ice_material=_bascenev1.Material();ice_material.add_actions(actions=('modify_part_collision','friction',.05))
		try:
			terrain_nodes=[]
			for node in _bascenev1.getnodes():
				if node.getnodetype()=='terrain'and hasattr(node,'materials')and shared.footing_material in node.materials:terrain_nodes.append(node)
			if not terrain_nodes:return
			if'icy_attrs'not in data:
				data['icy_attrs']={}
				for node in terrain_nodes:data['icy_attrs'][node]={'materials':node.materials,'color':getattr(node,'color',None),'reflection':getattr(node,'reflection',None),'reflection_scale':getattr(node,'reflection_scale',None)}
			_bascenev1.getsound('hiss').play(2.)
			for node in terrain_nodes:
				if ice_material not in node.materials:node.materials=node.materials+(ice_material,)
				if hasattr(node,'color'):node.color=1.,1.,2.
				if hasattr(node,'reflection'):node.reflection='soft'
				if hasattr(node,'reflection_scale'):node.reflection_scale=[.2]
		except Exception as e:print(f"Failed to toggle icy ground: {e}");return
		data['snowfall_timer']=_bascenev1.Timer(.02,self._snowfall_effect,repeat=True);data['icy_active']=True
		if duration:data['icy_timer']=_bascenev1.Timer(duration,babase.WeakCallStrict(self._reset_icy_ground))
	def _reset_icy_ground(self):
		data=self.customdata
		try:
			if not data.get('icy_active',False):return
			terrain_attrs=data.get('icy_attrs',{})
			for(node,attrs)in list(terrain_attrs.items()):
				try:
					if not node.exists():continue
					node.materials=attrs['materials']
					if attrs['color']is not None and hasattr(node,'color'):node.color=attrs['color']
					if attrs['reflection']is not None and hasattr(node,'reflection'):node.reflection=attrs['reflection']
					if attrs['ref_scale']is not None and hasattr(node,'reflection_scale'):node.reflection_scale=attrs['ref_scale']
				except Exception:pass
			data['icy_timer']=None;data['snowfall_timer']=None;data['icy_active']=False
		except Exception as e:print(f"Error in un-freezing terrain: {e}")
	def _snowfall_effect(self):pos=-10+random.random()*30,15,-10+random.random()*30;vel=(-5.+random.random()*3e1)*(-1. if pos[0]>0 else 1.),-5e1,(-5.+random.random()*3e1)*(-1. if pos[0]>0 else 1.);_bascenev1.emitfx(position=pos,velocity=vel,count=20,scale=1.+random.random(),spread=.0,chunk_type='spark')
	def toggle_slow_motion(self,duration=None,value=None):
		if value is None:value=not self.globalsnode.slow_motion
		self.globalsnode.slow_motion=value
		if duration:self.customdata['motion_timer']=_bascenev1.Timer(duration,babase.WeakCallStrict(self._reset_slow_motion))
	def _reset_slow_motion(self):self.globalsnode.slow_motion=self.customdata['default_slow_motion']
	def activate_meteor_shower(self,duration=None,source_player=None):
		data=self.customdata
		try:bounds=list(self.map.get_def_bound_box('area_of_interest_bounds'))
		except Exception as e:print(f"Error in activating meteor shower: {e}.");return
		owner=None
		if source_player is not None:
			actor=source_player.actor
			if actor is not None and actor.exists():owner=actor
		data['meteor_player']=source_player;data['meteor_owner']=owner;data['meteor_type']=['normal','normal','normal','ice','ice','impact','impact','land_mine','land_mine','sticky','sticky','portal','vacuum','hyper','fire','fire','spring','spring','shatter','knockout','knockout','curser','power'];data['meteor_timer']=_bascenev1.Timer(.75,babase.WeakCallStrict(self.drop_meteor,bounds),repeat=True)
		if duration:data['reset_meteor_timer']=_bascenev1.Timer(duration,babase.WeakCallStrict(self._reset_meteor_shower))
	def drop_meteor(self,bounds):
		vel=None;random_pos=False;map_name=self.map.getname()
		for _i in range(random.randrange(1,3)):
			if map_name=='Rampage':pos=random.randrange(-7,8),11,random.randrange(-5,-2)
			elif map_name=='Hockey Stadium':pos=random.randrange(-11,12),6,random.randrange(-4,5)
			else:random_pos=True;pos=random.uniform(bounds[0],bounds[3]),bounds[4],random.uniform(bounds[2],bounds[5]);dropdirx=-1 if pos[0]>0 else 1;dropdirz=-1 if pos[2]>0 else 1;forcex=bounds[0]-bounds[3]if bounds[0]-bounds[3]>0 else-(bounds[0]-bounds[3]);forcez=bounds[2]-bounds[5]if bounds[2]-bounds[5]>0 else-(bounds[2]-bounds[5]);vel=(-5+random.random()*forcex)*dropdirx,random.uniform(-3.066,-4.12),(-5+random.random()*forcez)*dropdirz
			if not random_pos:dropdir=-1. if pos[0]>0 else 1.;vel=(-5.+random.random()*3e1)*dropdir,random.uniform(-3.066,-4.12),0
			self._drop_meteor(pos,vel)
	def _drop_meteor(self,position,velocity):
		from bascenev1lib.actor.bomb import Bomb;owner=self.customdata.get('meteor_owner');source_player=self.customdata.get('meteor_player');meteor_type=self.customdata.get('meteor_type')
		if owner is None:bomb=Bomb(position=position,velocity=velocity,bomb_type=random.choice(meteor_type),blast_radius=2.,bomb_scale=1.,fuse_time=2.5,gravity_scale=1.,source_player=None,autoaim=False).autoretain();return
		bomb_type=random.choice(['normal']+owner.bomb_history);lower_gravity=.5 if owner.autoaim else 1.;bomb=Bomb(position=position,velocity=velocity,bomb_type=bomb_type,blast_radius=owner.blast_radius,bomb_scale=owner.bomb_scale,density=lower_gravity,source_player=babase.existing(source_player),autoaim=owner.autoaim,fuse_time=owner.fuse_time,gravity_scale=lower_gravity).autoretain()
		if bomb_type=='land_mine':_bascenev1.timer(1.2,bomb.arm)
	def _reset_meteor_shower(self):self.customdata['meteor_timer']=None
	def activate_blackout(self,duration=None):
		from bascenev1._gameutils import animate_array;animate_array(self.globalsnode,'tint',3,{0:self.globalsnode.tint,3.:(.1,.1,.1)},loop=False)
		if duration:self.customdata['blackout_timer']=_bascenev1.Timer(duration,babase.WeakCallStrict(self._reset_blackout))
	def _reset_blackout(self):from bascenev1._gameutils import animate_array;from gobase.svdata import Setting;animate_array(self.globalsnode,'tint',3,{0:self.globalsnode.tint,3.:Setting.tint},loop=False)
	def disable_powerups(self,duration=None):
		from bascenev1 import DieMessage;from bascenev1lib.actor.powerupbox import PowerupBox
		for node in _bascenev1.getnodes():
			if node.getdelegate(PowerupBox):node.handlemessage(DieMessage())
		self.customdata['powerup_disabled']=True
		if duration:self.customdata['powerup_timer']=_bascenev1.Timer(duration,babase.WeakCallStrict(self._allow_powerups))
	def _allow_powerups(self):self.customdata['powerup_disabled']=False
	def hug_players(self,indices):
		if len(indices)<2:return
		players=self.players;length=len(indices)
		for i in range(length):
			c=indices[i];n=indices[(i+1)%length]
			try:
				pc=players[c];pn=players[n]
				if pc.actor is None or pn.actor is None or pc.actor.node is None or pn.actor.node is None:continue
				pc.actor.node.hold_node=pn.actor.node
			except Exception as e:print(f"Hug failed for {c}->{n}: {e}")
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._gameactivity');orig_activity=orig_module.GameActivity;overlay_activity=GameActivity
	for(name,value)in overlay_activity.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_activity,name,value)
	public_api.GameActivity=orig_activity;additions=[]
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])