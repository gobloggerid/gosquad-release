# Released under the MIT License. See LICENSE for details.
# Modified for gosquad server by goblogger.
#

from __future__ import annotations
import logging,weakref
from dataclasses import dataclass
from random import choice
from typing import TYPE_CHECKING
import _bascenev1,babase
from bascenev1._gameutils import animate,animate_array
from bascenev1._profile import get_player_profile_colors
from better_profanity import profanity
from unidecode import unidecode
if TYPE_CHECKING:from collections.abc import Sequence;from typing import Any;import bascenev1
MAX_QUICK_CHANGE_COUNT=30
QUICK_CHANGE_INTERVAL=.05
QUICK_CHANGE_RESET_INTERVAL=1.
custom_names={}
class JoinInfo:
	def __init__(self,lobby):
		from bascenev1._nodeactor import NodeActor;self._state=0;self._press_to_punch=babase.charstr(babase.SpecialChar.LEFT_BUTTON);self._press_to_bomb=babase.charstr(babase.SpecialChar.RIGHT_BUTTON);self._joinmsg=babase.Lstr(resource='pressAnyButtonToJoinText');can_switch_teams=len(lobby.sessionteams)>1;keyboard=_bascenev1.getinputdevice('Keyboard','#1',doraise=False)
		if keyboard is not None:self._update_for_keyboard(keyboard)
		flatness=1. if babase.app.env.vr else .0;self._text=NodeActor(_bascenev1.newnode('text',attrs={'position':(0,-40),'h_attach':'center','v_attach':'top','h_align':'center','color':(.7,.7,.95,1.),'flatness':flatness,'text':self._joinmsg}));variant=babase.app.env.variant;vart=type(variant)
		if variant is vart.DEMO or variant is vart.ARCADE:self._messages=[self._joinmsg]
		else:msg1=babase.Lstr(resource='pressToSelectProfileText',subs=[('${BUTTONS}',babase.charstr(babase.SpecialChar.UP_ARROW)+' '+babase.charstr(babase.SpecialChar.DOWN_ARROW))]);msg2=babase.Lstr(resource='pressToOverrideCharacterText',subs=[('${BUTTONS}',babase.Lstr(resource='bombBoldText'))]);msg3=babase.Lstr(value='${A} < ${B} >',subs=[('${A}',msg2),('${B}',self._press_to_bomb)]);self._messages=([babase.Lstr(resource='pressToSelectTeamText',subs=[('${BUTTONS}',babase.charstr(babase.SpecialChar.LEFT_ARROW)+' '+babase.charstr(babase.SpecialChar.RIGHT_ARROW))])]if can_switch_teams else[])+[msg1]+[msg3]+[self._joinmsg]
		self._timer=_bascenev1.Timer(4.,babase.WeakCallStrict(self._update),repeat=True)
	def _update_for_keyboard(self,keyboard):classic=babase.app.classic;assert classic is not None;punch_key=keyboard.get_button_name(classic.get_input_device_mapped_value(keyboard,'buttonPunch'));self._press_to_punch=babase.Lstr(resource='orText',subs=[('${A}',babase.Lstr(value="'${K}'",subs=[('${K}',punch_key)])),('${B}',self._press_to_punch)]);bomb_key=keyboard.get_button_name(classic.get_input_device_mapped_value(keyboard,'buttonBomb'));self._press_to_bomb=babase.Lstr(resource='orText',subs=[('${A}',babase.Lstr(value="'${K}'",subs=[('${K}',bomb_key)])),('${B}',self._press_to_bomb)]);self._joinmsg=babase.Lstr(value='${A} < ${B} >',subs=[('${A}',babase.Lstr(resource='pressPunchToJoinText')),('${B}',self._press_to_punch)])
	def _update(self):assert self._text.node;self._text.node.text=self._messages[self._state];self._state=(self._state+1)%len(self._messages)
@dataclass
class PlayerReadyMessage:chooser:bascenev1.Chooser
@dataclass
class ChangeMessage:what:str;value:int
class Chooser:
	def __del__(self):
		if self._text_node:self._text_node.delete()
	def __init__(self,vpos,sessionplayer,lobby):self._deek_sound=_bascenev1.getsound('deek');self._click_sound=_bascenev1.getsound('click01');self._punchsound=_bascenev1.getsound('punch01');self._swish_sound=_bascenev1.getsound('punchSwish');self._errorsound=_bascenev1.getsound('error');self._mask_texture=_bascenev1.gettexture('characterIconMask');self._vpos=vpos;self._lobby=weakref.ref(lobby);self._sessionplayer=sessionplayer;self._inited=False;self._dead=False;self._text_node=None;self._profilename='';self._profilenames=[];self._ready=False;self._character_names=[];self._last_change=0,0;self._profiles={};app=babase.app;assert app.classic is not None;self.reload_profiles();self._selected_team_index=self.lobby.next_add_team;self._random_color,self._random_highlight=get_player_profile_colors(None);char_index_offset=app.classic.lobby_random_char_index_offset;self._random_character_index=(sessionplayer.inputdevice.id+char_index_offset)%len(self._character_names);self._profileindex=self._select_initial_profile();self._profilename=self._profilenames[self._profileindex];self._text_node=_bascenev1.newnode('text',delegate=self,attrs={'position':(-100,self._vpos),'maxwidth':160,'shadow':.5,'vr_depth':-20,'h_align':'left','v_align':'center','v_attach':'top'});animate(self._text_node,'scale',{0:0,.1:1.});self.icon=_bascenev1.newnode('image',owner=self._text_node,attrs={'position':(-130,self._vpos+20),'mask_texture':self._mask_texture,'vr_depth':-10,'attach':'topCenter'});animate_array(self.icon,'scale',2,{0:(0,0),.1:(45,45)});self._sessionplayer.setname(babase.Lstr(resource='choosingPlayerText').evaluate(),real=False);self._character_index=self._random_character_index;self._color=self._random_color;self._highlight=self._random_highlight;self.update_from_profile();self.update_position();self._inited=True;self._set_ready(False)
	def _select_initial_profile(self):
		app=babase.app;assert app.classic is not None;profilenames=self._profilenames;inputdevice=self._sessionplayer.inputdevice;dprofilename=app.config.get('Default Player Profiles',{}).get(inputdevice.name+' '+inputdevice.unique_identifier)
		if dprofilename is not None and dprofilename in profilenames:
			if dprofilename=='__account__'and not inputdevice.is_remote_client and app.classic.lobby_account_profile_device_id is None:app.classic.lobby_account_profile_device_id=inputdevice.id
			return profilenames.index(dprofilename)
		if not inputdevice.is_remote_client and not inputdevice.is_controller_app:
			if app.classic.lobby_account_profile_device_id is None and'__account__'in profilenames:app.classic.lobby_account_profile_device_id=inputdevice.id
		if inputdevice.id==app.classic.lobby_account_profile_device_id and'__account__'in profilenames:return profilenames.index('__account__')
		if inputdevice.is_controller_app and'_random'in profilenames:return profilenames.index('_random')
		if inputdevice.is_remote_client and'__account__'in profilenames:return profilenames.index('__account__')
		while app.classic.lobby_random_profile_index<len(profilenames)and profilenames[app.classic.lobby_random_profile_index]in('_random','__account__','_edit'):app.classic.lobby_random_profile_index+=1
		if app.classic.lobby_random_profile_index<len(profilenames):profileindex=app.classic.lobby_random_profile_index;app.classic.lobby_random_profile_index+=1;return profileindex
		assert'_random'in profilenames;return profilenames.index('_random')
	@property
	def sessionplayer(self):return self._sessionplayer
	@property
	def ready(self):return self._ready
	def set_vpos(self,vpos):self._vpos=vpos
	def set_dead(self,val):self._dead=val
	@property
	def sessionteam(self):return self.lobby.sessionteams[self._selected_team_index]
	@property
	def lobby(self):
		lobby=self._lobby()
		if lobby is None:raise babase.NotFoundError('Lobby does not exist.')
		return lobby
	def get_lobby(self):return self._lobby()
	def update_from_profile(self):
		assert babase.app.classic is not None;self._profilename=self._profilenames[self._profileindex]
		if self._profilename=='_edit':0
		elif self._profilename=='_random':self._character_index=self._resolve_random_character();self._color=self._random_color;self._highlight=self._random_highlight
		else:
			character=self._profiles[self._profilename]['character']
			if character not in self._character_names and character in babase.app.classic.spaz_appearances:self._character_names.append(character)
			self._character_index=self._character_names.index(character);self._color,self._highlight=get_player_profile_colors(self._profilename,profiles=self._profiles)
		self._update_icon();self._update_text()
	def reload_profiles(self):
		app=babase.app;assert app.classic is not None;input_device=self._sessionplayer.inputdevice;is_remote=input_device.is_remote_client;is_test_input=input_device.is_test_input
		if is_remote:self._character_names=['Spaz']
		else:self._character_names=self.lobby.character_names_local_unlocked
		if is_remote:self._profiles=input_device.get_player_profiles()
		else:self._profiles=app.config.get('Player Profiles',{})
		self._profiles=app.classic.json_prep(self._profiles)
		for profile in list(self._profiles.items()):
			if profile[1].get('character','')not in app.classic.spaz_appearances:profile[1]['character']='Spaz'
		self._profiles['_random']={};variant=babase.app.env.variant;vart=type(variant);arcade_or_demo=variant is vart.ARCADE or variant is vart.DEMO
		if arcade_or_demo:
			if'__account__'in self._profiles:del self._profiles['__account__']
		if not is_remote and not is_test_input and not arcade_or_demo:self._profiles['_edit']={}
		self._profilenames=list(self._profiles.keys());self._profilenames.sort(key=lambda x:x.lower())
		if self._profilename in self._profilenames:self._profileindex=self._profilenames.index(self._profilename)
		else:self._profileindex=0;self._profilename=self._profilenames[self._profileindex]
	def update_position(self):
		assert self._text_node;spacing=350;sessionteams=self.lobby.sessionteams;offs=spacing*-.5*len(sessionteams)+spacing*self._selected_team_index+250
		if len(sessionteams)>1:offs-=35
		animate_array(self._text_node,'position',2,{0:self._text_node.position,.1:(-100+offs,self._vpos+23)});animate_array(self.icon,'position',2,{0:self.icon.position,.1:(-130+offs,self._vpos+22)})
	def get_character_name(self):return self._character_names[self._character_index]
	def _do_nothing(self):0
	def _getname(self,full=False):
		from gocommon.gosetting import getsetting;name_raw=name=self._profilenames[self._profileindex];clamp=False
		if name=='_random':
			try:
				if getsetting()['customNames']:
					global custom_names;device=self._sessionplayer.inputdevice.id
					if device not in custom_names:custom_names[device]=self._get_custom_name()
					name=custom_names[device]
				else:name=self._sessionplayer.inputdevice.get_default_player_name()
			except Exception:logging.exception('Error getting _random chooser name.');name='Invalid'
			clamp=not full
		elif name=='__account__':
			try:name=self._sessionplayer.inputdevice.get_v1_account_name(full)
			except Exception:logging.exception('Error getting account name for chooser.');name='Invalid'
			clamp=not full
		elif name=='_edit':name=babase.Lstr(resource='createEditPlayerText',fallback_resource='editProfileWindow.titleNewText').evaluate()
		elif full:
			try:
				if self._profiles[name_raw].get('global',False):icon=self._profiles[name_raw]['icon']if'icon'in self._profiles[name_raw]else babase.charstr(babase.SpecialChar.LOGO);name=icon+name
			except Exception:logging.exception('Error applying global icon.')
		else:clamp=True
		if clamp:
			if len(name)>10:name=name[:10]+'...'
		return name
	def _set_ready(self,ready):
		classic=babase.app.classic;assert classic is not None;profilename=self._profilenames[self._profileindex]
		if profilename=='_edit'and ready:
			with babase.ContextRef.empty():classic.profile_browser_window();babase.set_main_ui_input_device(self._sessionplayer.inputdevice.id)
			return
		if not ready:self._sessionplayer.assigninput(babase.InputType.LEFT_PRESS,babase.CallStrict(self.handlemessage,ChangeMessage('team',-1)));self._sessionplayer.assigninput(babase.InputType.RIGHT_PRESS,babase.CallStrict(self.handlemessage,ChangeMessage('team',1)));self._sessionplayer.assigninput(babase.InputType.BOMB_PRESS,babase.CallStrict(self.handlemessage,ChangeMessage('character',1)));self._sessionplayer.assigninput(babase.InputType.UP_PRESS,babase.CallStrict(self.handlemessage,ChangeMessage('profileindex',-1)));self._sessionplayer.assigninput(babase.InputType.DOWN_PRESS,babase.CallStrict(self.handlemessage,ChangeMessage('profileindex',1)));self._sessionplayer.assigninput((babase.InputType.JUMP_PRESS,babase.InputType.PICK_UP_PRESS,babase.InputType.PUNCH_PRESS),babase.CallStrict(self.handlemessage,ChangeMessage('ready',1)));self._ready=False;self._update_text();self._sessionplayer.setname('untitled',real=False)
		else:
			self._sessionplayer.assigninput((babase.InputType.LEFT_PRESS,babase.InputType.RIGHT_PRESS,babase.InputType.UP_PRESS,babase.InputType.DOWN_PRESS,babase.InputType.JUMP_PRESS,babase.InputType.BOMB_PRESS,babase.InputType.PICK_UP_PRESS),self._do_nothing);self._sessionplayer.assigninput((babase.InputType.JUMP_PRESS,babase.InputType.BOMB_PRESS,babase.InputType.PICK_UP_PRESS,babase.InputType.PUNCH_PRESS),babase.CallStrict(self.handlemessage,ChangeMessage('ready',0)));input_device=self._sessionplayer.inputdevice;name=input_device.name;unique_id=input_device.unique_identifier;device_profiles=babase.app.config.setdefault('Default Player Profiles',{});special='_random','_edit','__account__';have_custom_profiles=any(p not in special for p in self._profiles);profilekey=name+' '+unique_id
			if profilename=='_random'and not have_custom_profiles:
				if profilekey in device_profiles:del device_profiles[profilekey]
			else:device_profiles[profilekey]=profilename
			babase.app.config.commit();full_name=unidecode(self._getname(full=True))
			if profanity.contains_profanity(full_name):self._sessionplayer.setname('Censored','Censored Name',real=True)
			else:self._sessionplayer.setname(self._getname(),self._getname(full=True),real=True)
			self._ready=True;self._update_text();self._store_name(self._sessionplayer.get_v1_account_id(),self._getname(full=True));_bascenev1.getsession().handlemessage(PlayerReadyMessage(self))
	def _handle_ready_msg(self,ready):
		force_team_switch=False
		if not self._ready:
			if babase.app.config.get('Auto Balance Teams',False):
				lobby=self.lobby;sessionteams=lobby.sessionteams
				if len(sessionteams)>1:
					team_player_counts={}
					for sessionteam in sessionteams:team_player_counts[sessionteam.id]=len(sessionteam.players)
					for chooser in lobby.choosers:
						if chooser.ready:team_player_counts[chooser.sessionteam.id]+=1
					largest_team_size=max(team_player_counts.values());smallest_team_size=min(team_player_counts.values())
					if largest_team_size!=smallest_team_size and team_player_counts[self.sessionteam.id]>=largest_team_size:force_team_switch=True
		if force_team_switch:self._errorsound.play();self.handlemessage(ChangeMessage('team',1))
		else:self._punchsound.play();self._set_ready(ready)
	def _handle_repeat_message_attack(self):
		now=babase.apptime();count=self._last_change[1]
		if now-self._last_change[0]<QUICK_CHANGE_INTERVAL:
			count+=1
			if count>MAX_QUICK_CHANGE_COUNT:_bascenev1.disconnect_client(self._sessionplayer.inputdevice.client_id)
		elif now-self._last_change[0]>QUICK_CHANGE_RESET_INTERVAL:count=0
		self._last_change=now,count
	def handlemessage(self,msg):
		if isinstance(msg,ChangeMessage):
			self._handle_repeat_message_attack()
			if self._dead:logging.error('chooser got ChangeMessage after dying');return
			if not self._text_node:logging.error('got ChangeMessage after nodes died');return
			if msg.what=='team':
				sessionteams=self.lobby.sessionteams
				if len(sessionteams)>1:self._swish_sound.play()
				self._selected_team_index=(self._selected_team_index+msg.value)%len(sessionteams);self._update_text();self.update_position();self._update_icon()
			elif msg.what=='profileindex':
				if len(self._profilenames)==1:_bascenev1.getsound('error').play()
				else:self._deek_sound.play();self._profileindex=(self._profileindex+msg.value)%len(self._profilenames);self.update_from_profile()
			elif msg.what=='character':self._click_sound.play();self._character_index=(self._character_index+msg.value)%len(self._character_names);self._update_text();self._update_icon()
			elif msg.what=='ready':self._handle_ready_msg(bool(msg.value))
	def _update_text(self):
		assert self._text_node is not None
		if self._ready:text=babase.Lstr(value=self._sessionplayer.getname(full=True));text=babase.Lstr(value='${A} (${B})',subs=[('${A}',text),('${B}',babase.Lstr(resource='readyText'))])
		else:text=babase.Lstr(value=self._getname(full=True))
		can_switch_teams=len(self.lobby.sessionteams)>1;fin_color=babase.safecolor(self.get_color())+(1,)
		if not self._inited:animate_array(self._text_node,'color',4,{.15:fin_color,.25:(2,2,2,1),.35:fin_color})
		elif can_switch_teams:animate_array(self._text_node,'color',4,{0:self._text_node.color,.1:fin_color})
		else:self._text_node.color=fin_color
		self._text_node.text=text
	def get_color(self):
		val:0
		if self.lobby.use_team_colors:val=self.lobby.sessionteams[self._selected_team_index].color
		else:val=self._color
		if len(val)!=3:print('get_color: ignoring invalid color of len',len(val));val=0,1,0
		return val
	def get_highlight(self):
		if self._profilenames[self._profileindex]=='_edit':return 0,1,0
		highlight=list(self._highlight)
		if self.lobby.use_team_colors:
			for(i,sessionteam)in enumerate(self.lobby.sessionteams):
				if i!=self._selected_team_index:
					max_val=.0;max_index=0
					for j in range(3):
						if sessionteam.color[j]>max_val:max_val=sessionteam.color[j];max_index=j
					that_color_for_us=highlight[max_index];our_second_biggest=max(highlight[(max_index+1)%3],highlight[(max_index+2)%3]);diff=that_color_for_us-our_second_biggest
					if diff>0:highlight[max_index]-=diff*.6;highlight[(max_index+1)%3]+=diff*.3;highlight[(max_index+2)%3]+=diff*.2
		return highlight
	def getplayer(self):return self._sessionplayer
	def _update_icon(self):
		assert babase.app.classic is not None
		if self._profilenames[self._profileindex]=='_edit':tex=_bascenev1.gettexture('black');tint_tex=_bascenev1.gettexture('black');self.icon.color=1,1,1;self.icon.texture=tex;self.icon.tint_texture=tint_tex;self.icon.tint_color=0,1,0;return
		try:tex_name=babase.app.classic.spaz_appearances[self._character_names[self._character_index]].icon_texture;tint_tex_name=babase.app.classic.spaz_appearances[self._character_names[self._character_index]].icon_mask_texture
		except Exception:logging.exception('Error updating char icon list');tex_name='neoSpazIcon';tint_tex_name='neoSpazIconColorMask'
		tex=_bascenev1.gettexture(tex_name);tint_tex=_bascenev1.gettexture(tint_tex_name);self.icon.color=1,1,1;self.icon.texture=tex;self.icon.tint_texture=tint_tex;clr=self.get_color();clr2=self.get_highlight();can_switch_teams=len(self.lobby.sessionteams)>1
		if not self._inited:animate_array(self.icon,'color',3,{.15:(1,1,1),.25:(2,2,2),.35:(1,1,1)})
		if can_switch_teams:animate_array(self.icon,'tint_color',3,{0:self.icon.tint_color,.1:clr})
		else:self.icon.tint_color=clr
		self.icon.tint2_color=clr2;self._sessionplayer.set_icon_info(tex_name,tint_tex_name,clr,clr2)
	def _get_custom_name(self):
		from gocommon.gosetting import getsetting;from textlibs.manager import textlist;custom=textlist.getall('custom_names')
		if not getsetting()['builtinNames']:return choice(custom)
		return choice(custom+_bascenev1.get_random_names())
	def _resolve_random_character(self):
		from gocommon.gosetting import getsetting;settings=getsetting().get('spazSettings',{})
		if settings.get('overrideRandomCharacter',False):
			char=settings.get('character','Bombman')
			if char in self._character_names:return self._character_names.index(char)
		return self._random_character_index
	def _store_name(self,acid,name):
		import json;from gobase.godata import Profile;existing=Profile.get(acid).get('last_names',[])
		if isinstance(existing,str):existing=json.loads(existing)
		data={'last_name':name};clamped=name[:10]
		if clamped not in existing:existing.append(clamped);existing=existing[-6:];data['last_names']=existing
		try:Profile.set(acid,data)
		except Exception as e:print(e)
class Lobby:
	def __del__(self):
		sessionplayers=[c.sessionplayer for c in self.choosers if c.sessionplayer]
		for sessionplayer in sessionplayers:sessionplayer.resetinput()
	def __init__(self):
		from bascenev1._coopsession import CoopSession;from bascenev1._team import SessionTeam;session=_bascenev1.getsession();self._use_team_colors=session.use_team_colors
		if session.use_teams:self._sessionteams=[weakref.ref(team)for team in session.sessionteams]
		else:self._dummy_teams=SessionTeam();self._sessionteams=[weakref.ref(self._dummy_teams)]
		v_offset=-150 if isinstance(session,CoopSession)else-50;self.choosers=[];self.base_v_offset=v_offset;self.update_positions();self._next_add_team=0;self.character_names_local_unlocked=[];self._vpos=0;self.reload_profiles();self._join_info_text=None
	@property
	def next_add_team(self):return self._next_add_team
	@property
	def use_team_colors(self):return self._use_team_colors
	@property
	def sessionteams(self):
		allteams=[]
		for tref in self._sessionteams:team=tref();assert team is not None;allteams.append(team)
		return allteams
	def get_choosers(self):return self.choosers
	def create_join_info(self):return JoinInfo(self)
	def reload_profiles(self):
		from bascenev1lib.actor.spazappearance import get_appearances;assert babase.app.classic is not None;self.character_names_local_unlocked=get_appearances();self.character_names_local_unlocked.sort(key=lambda x:x.lower());babase.app.classic.accounts.ensure_have_account_player_profile()
		for chooser in self.choosers:
			try:chooser.reload_profiles();chooser.update_from_profile()
			except Exception:logging.exception('Error reloading profiles.')
	def update_positions(self):
		self._vpos=-100+self.base_v_offset
		for chooser in self.choosers:chooser.set_vpos(self._vpos);chooser.update_position();self._vpos-=48
	def check_all_ready(self):return all(chooser.ready for chooser in self.choosers)
	def add_chooser(self,sessionplayer):self.choosers.append(Chooser(vpos=self._vpos,sessionplayer=sessionplayer,lobby=self));self._next_add_team=(self._next_add_team+1)%len(self._sessionteams);self._vpos-=48
	def remove_chooser(self,player):
		found=False;chooser=None
		for chooser in self.choosers:
			if chooser.getplayer()is player:found=True;chooser.set_dead(True);self.choosers.remove(chooser);break
		if not found:logging.exception('remove_chooser did not find player %s.',player)
		elif chooser in self.choosers:logging.exception('chooser remains after removal for %s.',player)
		self.update_positions()
	def remove_all_choosers(self):self.choosers=[];self.update_positions()
	def remove_all_choosers_and_kick_players(self):
		for chooser in list(self.choosers):
			if chooser.sessionplayer:chooser.sessionplayer.remove_from_game()
		self.remove_all_choosers()
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._lobby');orig_chooser=orig_module.Chooser;overlay_chooser=Chooser
	for(name,value)in overlay_chooser.__dict__.items():
		if name in{'__module__','__dict__','__weakref__','__doc__'}:continue
		setattr(orig_chooser,name,value)
	public_api.Chooser=orig_chooser;additions=[]
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])