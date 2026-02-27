# Released under the MIT License. See LICENSE for details.
# Modified for gosquad server.
#

from __future__ import annotations
import contextlib,logging,random,weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING
import _bascenev1,babase
if TYPE_CHECKING:from collections.abc import Sequence;from typing import Any;import bascenev1
@dataclass
class PlayerScoredMessage:score:int
class PlayerRecord:
	character:str
	def __init__(self,name,name_full,sessionplayer,stats):self.name=name;self.name_full=name_full;self.score=0;self.accumscore=0;self.kill_count=0;self.accum_kill_count=0;self.killed_count=0;self.accum_killed_count=0;self.betray_count=0;self.accum_betray_count=0;self._multi_kill_timer=None;self._multi_kill_count=0;self._stats=weakref.ref(stats);self._last_sessionplayer=None;self._sessionplayer=None;self._sessionteam=None;self.streak=0;self.associate_with_sessionplayer(sessionplayer)
	@property
	def team(self):
		assert self._sessionteam is not None;team=self._sessionteam()
		if team is None:raise babase.SessionTeamNotFoundError()
		return team
	@property
	def player(self):
		if not self._sessionplayer:raise babase.SessionPlayerNotFoundError()
		return self._sessionplayer
	def getname(self,full=False):return self.name_full if full else self.name
	def get_icon(self):player=self._last_sessionplayer;assert player is not None;return player.get_icon()
	def cancel_multi_kill_timer(self):self._multi_kill_timer=None
	def getactivity(self):
		stats=self._stats()
		if stats is not None:return stats.getactivity()
		return None
	def associate_with_sessionplayer(self,sessionplayer):self._sessionteam=weakref.ref(sessionplayer.sessionteam);self.character=sessionplayer.character;self._last_sessionplayer=sessionplayer;self._sessionplayer=sessionplayer;self.streak=0;from gobase.godata import Stat;self.acid=sessionplayer.get_v1_account_id();score=Stat.getmany(self.acid,['score','milestone']);self.db_score=score[0]or 0;self.db_milestone=score[1]or 2500
	def _end_multi_kill(self):self._multi_kill_timer=None;self._multi_kill_count=0
	def get_last_sessionplayer(self):assert self._last_sessionplayer is not None;return self._last_sessionplayer
	def submit_kill(self,showpoints=True,p_name='Go Player',p_color=(1,1,1)):
		self._multi_kill_count+=1;stats=self._stats();assert stats
		if self._multi_kill_count==1:score=0;name=None;delay=.0;color=.0,.0,.0,1.;scale=1.;sound=None
		elif self._multi_kill_count==2:score=20;name=babase.Lstr(resource='twoKillText');color=.1,1.,.0,1;scale=1.;delay=.0;sound=stats.orchestrahitsound1
		elif self._multi_kill_count==3:score=40;name=babase.Lstr(resource='threeKillText');color=1.,.7,.0,1;scale=1.1;delay=.3;sound=stats.orchestrahitsound2
		elif self._multi_kill_count==4:score=60;name=babase.Lstr(resource='fourKillText');color=1.,1.,.0,1;scale=1.2;delay=.6;sound=stats.orchestrahitsound3
		elif self._multi_kill_count==5:score=80;name=babase.Lstr(resource='fiveKillText');color=1.,.5,.0,1;scale=1.3;delay=.9;sound=stats.orchestrahitsound4
		else:score=100;name=babase.Lstr(resource='multiKillText',subs=[('${COUNT}',str(self._multi_kill_count))]);color=1.,.5,.0,1;scale=1.3;delay=1.;sound=stats.orchestrahitsound4
		def _apply(name2,score2,showpoints2,color2,scale2,sound2):
			from bascenev1._messages import TextMessage;from bascenev1lib.actor.popuptext import PopupText;from bascenev1lib.actor.zoomtext import ZoomText;from textlibs.manager import textlist;our_pos=None
			if self._sessionplayer and self._sessionplayer.activityplayer is not None:
				with contextlib.suppress(babase.NodeNotFoundError):our_pos=self._sessionplayer.activityplayer.position
			if our_pos is None:return
			our_pos=babase.Vec3(our_pos[0]+(random.random()-.5)*2.,our_pos[1]+(random.random()-.5)*2.,our_pos[2]+(random.random()-.5)*2.);activity=self.getactivity()
			if activity is not None:PopupText(babase.Lstr(value=('+'+str(score2)+' 'if showpoints2 else'')+'${N}',subs=[('${N}',name2)]),color=color2,scale=scale2,position=our_pos).autoretain()
			if sound2:sound2.play()
			self.score+=score2;self.accumscore+=score2
			if score2!=0 and activity is not None:activity.handlemessage(PlayerScoredMessage(score=score2))
			if self._multi_kill_count>=4 and activity is not None:
				cur_time=_bascenev1.time()
				if cur_time-activity.customdata['last_masskill_message']>5.:ZoomText(text=textlist.get('masskill_messages'),maxwidth=800,lifespan=2.,jitter=2.,position=(0,120),flash=False,color=(1.1625,1.125,1.25),trailcolor=(.15,.05,1.,.0)).autoretain();ZoomText(text=self.get_masskill_text(p_name),maxwidth=800,position=(0,25),lifespan=1.75,color=babase.normalized_color(p_color),flash=False,trail=False,scale=.3).autoretain();csound=_bascenev1.getsound(random.choice(['score','nice','woo','woo2','woo3']));_bascenev1.timer(1.,babase.CallStrict(csound.play,5.));activity.customdata['last_masskill_message']=cur_time
			actor=getattr(getattr(self._sessionplayer,'activityplayer',None),'actor',None)
			if actor is not None:
				if random.choice([True,False]):text=textlist.get('emote_messages');actor.handlemessage(TextMessage(text=text,animate=True))
				else:text=textlist.get('kill_messages');actor.handlemessage(TextMessage(text=text,color='random',animate=True))
		if name is not None:_bascenev1.timer(.3+delay,babase.CallStrict(_apply,name,score,showpoints,color,scale,sound))
		self._multi_kill_timer=_bascenev1.Timer(1.,self._end_multi_kill)
	def get_masskill_text(self,p_name):texts=[f"📷✨ GREAT! {p_name} DID A MASS-KILLING ✨📷",f"📷✨ {p_name} IS ON A RAMPAGE! HE KILLED EVERYONE! ✨📷",f"📷✨ UNSTOPPABLE! {p_name} IS COOKING EVERYBODY! ✨📷",f"📷✨ AWESOME! {p_name} WIPED OUT EVERYONE! ✨📷",f"📷✨ UNREAL! {p_name} JUST ANNIHILATED THE WHOLE ARENA! ✨📷",f"📷✨ INCREDIBLE! {p_name} TOOK DOWN EVERY LAST OPPONENT! ✨📷",f"📷✨ BRUTAL! {p_name} EXECUTED A TOTAL TEAM KNOCKOUT! ✨📷",f"📷✨ EPIC! {p_name} LEFT NO ONE STANDING! ✨📷"];return random.choice(texts)
class Stats:
	def __init__(self):self._activity=None;self._player_records={};self.orchestrahitsound1=None;self.orchestrahitsound2=None;self.orchestrahitsound3=None;self.orchestrahitsound4=None
	def setactivity(self,activity):
		self._activity=None if activity is None else weakref.ref(activity)
		if activity is not None:
			if activity.expired:logging.exception('Unexpected finalized activity.')
			else:
				with activity.context:self._load_activity_media()
	def getactivity(self):
		if self._activity is None:return None
		return self._activity()
	def _load_activity_media(self):self.orchestrahitsound1=_bascenev1.getsound('orchestraHit');self.orchestrahitsound2=_bascenev1.getsound('orchestraHit2');self.orchestrahitsound3=_bascenev1.getsound('orchestraHit3');self.orchestrahitsound4=_bascenev1.getsound('orchestraHit4')
	def reset(self):
		for p_entry in list(self._player_records.values()):p_entry.cancel_multi_kill_timer()
		self._player_records={}
	def reset_accum(self):
		for s_player in list(self._player_records.values()):s_player.cancel_multi_kill_timer();s_player.accumscore=0;s_player.accum_kill_count=0;s_player.accum_killed_count=0;s_player.accum_betray_count=0;s_player.streak=0
	def register_sessionplayer(self,player):
		assert player.exists();name=player.getname()
		if name in self._player_records:self._player_records[name].associate_with_sessionplayer(player)
		else:name_full=player.getname(full=True);self._player_records[name]=PlayerRecord(name,name_full,player,self)
	def get_records(self):
		records={}
		for(record_id,record)in self._player_records.items():
			lastplayer=record.get_last_sessionplayer()
			if lastplayer and lastplayer.getname()==record_id:records[record_id]=record
		return records
	def player_scored(self,player,base_points=1,*,target=None,kill=False,victim_player=None,scale=1.,color=None,title=None,screenmessage=True,display=True,importance=1,showpoints=True,big_message=False):
		from bascenev1._gameactivity import GameActivity;from bascenev1lib.actor.popuptext import PopupText;del victim_player;name=player.getname();s_player=self._player_records[name]
		if kill:s_player.submit_kill(showpoints=showpoints,p_name=player.getname(full=True),p_color=player.team.color)
		display_color=1.,1.,1.,1.
		if color is not None:display_color=color
		elif importance!=1:display_color=1.,1.,.4,1.
		points=base_points
		if display and big_message:
			try:
				assert self._activity is not None;activity=self._activity()
				if isinstance(activity,GameActivity):name_full=player.getname(full=True,icon=False);activity.show_zoom_message(babase.Lstr(resource='nameScoresText',subs=[('${NAME}',name_full)]),color=babase.normalized_color(player.team.color))
			except Exception:logging.exception('Error showing big_message.')
		if display and showpoints:
			our_pos=player.node.position if player.node else None
			if our_pos is not None:
				if target is None:target=our_pos
				display_pos=target[0],max(target[1],our_pos[1]-2.),min(target[2],our_pos[2]+2.);activity=self.getactivity()
				if activity is not None:
					if title is not None:sval=babase.Lstr(value='+${A} ${B}',subs=[('${A}',str(points)),('${B}',title)])
					else:sval=babase.Lstr(value='+${A}',subs=[('${A}',str(points))])
					PopupText(sval,color=display_color,scale=1.2*scale,position=display_pos).autoretain()
		if kill:s_player.accum_kill_count+=1;s_player.kill_count+=1
		try:
			if screenmessage and not kill:_bascenev1.broadcastmessage(babase.Lstr(resource='nameScoresText',subs=[('${NAME}',name)]),top=True,color=player.color,image=player.get_icon())
		except Exception:logging.exception('Error announcing score.')
		s_player.score+=points;s_player.accumscore+=points;s_player.db_score+=points
		if s_player.db_score>=s_player.db_milestone:self.update_player_level(s_player)
		if points!=0:
			activity=self._activity()if self._activity is not None else None
			if activity is not None:activity.handlemessage(PlayerScoredMessage(score=points))
		return points
	def update_player_level(self,player):
		from gobase.godata import Level,Stat;actual_milestone=Stat.getone(player.acid,'milestone')or 0
		if player.db_milestone!=actual_milestone:player.db_milestone=actual_milestone;return
		try:Level.update(player.acid,1)
		except Exception:Stat.update(player.acid,{'milestone':1000000});return
		milestone=Stat._calculate_milestone(player.acid);Stat.update(player.acid,{'milestone':milestone});self.levelup_message(player.getname(full=True))
	def levelup_message(self,name='awesome player'):messages=[f"Congratulations, {name}! You level up! 🎉 🥳 🚀",f"That's great, {name}! You've leveled up! 🛡️ 🚀 🔥",f"{name}, you did it! You just leveled up! 🔝 🎉 💪",f"Boom! {name}, you're leveling up like a champion! 🏅 🎊 🏆⚡",f"Another level reached, {name}! Keep crushing it! 🎮 🌟 🎯"];message=random.choice(messages);schedule_announcement(message,delay=.5,color=(0,.8,0),sound=_bascenev1.getsound('achievement'),volume=2.)
	def player_was_killed(self,player,killed=False,killer=None):
		from textlibs.manager import textlist;name=player.getname();prec=self._player_records[name];prec.streak=0
		if killed:
			if killer is player:prec.accum_killed_count+=1;prec.killed_count+=1
			elif killer is not None:
				if killer.team is not player.team:prec.accum_killed_count+=1;prec.killed_count+=1
				elif killer.team is player.team:
					krec=self._player_records[killer.getname()];krec.accum_betray_count+=1;krec.betray_count+=1;killer_name=killer.getname(full=True)
					if krec.accum_betray_count==1:_bascenev1.broadcastmessage(f"{name}: {textlist.get("betrayed_messages")}",color=(.8,.8,0))
					elif krec.accum_betray_count==2:_bascenev1.broadcastmessage(f"Play more carefully, {killer_name}! Don't attack your teammates!",color=(.8,.8,0))
					elif krec.accum_betray_count==3:_bascenev1.broadcastmessage(f"{name}: {textlist.get("betrayed_messages")}",color=(.8,.8,0))
					elif krec.accum_betray_count==4:_bascenev1.broadcastmessage(f"WARNING to {killer_name}. Stop betraying or get banned!",color=(.8,.0,0))
					elif krec.accum_betray_count>=5:_bascenev1.broadcastmessage('Goodbye! It is not fun to play with a betrayer!',color=(.8,0,0),transient=True,clients=[killer.sessionplayer.inputdevice.client_id]);schedule_announcement(f"{killer_name} was kicked for betraying too much.",delay=.5,color=(.8,0,.8));_bascenev1.disconnect_client(killer.sessionplayer.inputdevice.client_id,900)
			else:prec.accum_killed_count+=1;prec.killed_count+=1
		try:
			if killed and _bascenev1.getactivity().announce_player_deaths:
				if killer is player:_bascenev1.broadcastmessage(babase.Lstr(resource='nameSuicideText',subs=[('${NAME}',name)]),top=True,color=player.color,image=player.get_icon())
				elif killer is not None:
					if killer.team is player.team:_bascenev1.broadcastmessage(babase.Lstr(resource='nameBetrayedText',subs=[('${NAME}',killer.getname()),('${VICTIM}',name)]),top=True,color=killer.color,image=killer.get_icon())
					else:_bascenev1.broadcastmessage(babase.Lstr(resource='nameKilledText',subs=[('${NAME}',killer.getname()),('${VICTIM}',name)]),top=True,color=killer.color,image=killer.get_icon())
				else:_bascenev1.broadcastmessage(babase.Lstr(resource='nameDiedText',subs=[('${NAME}',name)]),top=True,color=player.color,image=player.get_icon())
		except Exception:logging.exception('Error announcing kill.')
def schedule_announcement(message,delay=.0,color=(1.,1.,1.),sound=None,volume=1.):
	_bascenev1.timer(delay,babase.CallStrict(_bascenev1.broadcastmessage,message,color=color))
	if sound:_bascenev1.timer(delay,babase.CallStrict(sound.play,volume=volume))
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._stats');orig_record=orig_module.PlayerRecord;orig_stats=orig_module.Stats;overlay_record=PlayerRecord
	for(name,value)in overlay_record.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_record,name,value)
	overlay_stats=Stats
	for(name,value)in overlay_stats.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_stats,name,value)
	public_api.PlayerRecord=orig_record;public_api.Stats=orig_stats;additions=[]
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])