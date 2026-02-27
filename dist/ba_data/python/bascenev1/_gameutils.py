# Released under the MIT License. See LICENSE for details.
# Modified for gosquaq server.
#

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING,NewType
import _bascenev1,babase
if TYPE_CHECKING:from collections.abc import Sequence;import bascenev1
Time=NewType('Time',float)
BaseTime=NewType('BaseTime',float)
TROPHY_CHARS={'1':babase.SpecialChar.TROPHY1,'2':babase.SpecialChar.TROPHY2,'3':babase.SpecialChar.TROPHY3,'0a':babase.SpecialChar.TROPHY0A,'0b':babase.SpecialChar.TROPHY0B,'4':babase.SpecialChar.TROPHY4}
@dataclass
class GameTip:text:str;icon:bascenev1.Texture|None=None;sound:bascenev1.Sound|None=None
def get_trophy_string(trophy_id):
	if trophy_id in TROPHY_CHARS:return babase.charstr(TROPHY_CHARS[trophy_id])
	return'?'
def animate(node,attr,keys,loop=False,offset=0):
	items=list(keys.items());items.sort();curve=_bascenev1.newnode('animcurve',owner=node,name='Driving '+str(node)+" '"+attr+"'");mult=1000;curve.times=[int(mult*time)for(time,val)in items];curve.offset=int(_bascenev1.time()*1e3)+int(mult*offset);curve.values=[val for(time,val)in items];curve.loop=loop
	if not loop:_bascenev1.timer((int(mult*items[-1][0])+1000)/1e3,curve.delete)
	try:globalsnode=_bascenev1.getactivity().globalsnode
	except babase.ActivityNotFoundError:globalsnode=_bascenev1.getsession().sessionglobalsnode
	globalsnode.connectattr('time',curve,'in');curve.connectattr('out',node,attr);return curve
def animate_array(node,attr,size,keys,*,loop=False,offset=0):
	combine=_bascenev1.newnode('combine',owner=node,attrs={'size':size});items=list(keys.items());items.sort();mult=1000
	try:globalsnode=_bascenev1.getactivity().globalsnode
	except babase.ActivityNotFoundError:globalsnode=_bascenev1.getsession().sessionglobalsnode
	for i in range(size):
		curve=_bascenev1.newnode('animcurve',owner=node,name='Driving '+str(node)+" '"+attr+"' member "+str(i));globalsnode.connectattr('time',curve,'in');curve.times=[int(mult*time)for(time,val)in items];curve.values=[val[i]for(time,val)in items];curve.offset=int(_bascenev1.time()*1e3)+int(mult*offset);curve.loop=loop;curve.connectattr('out',combine,'input'+str(i))
		if not loop:_bascenev1.timer((int(mult*items[-1][0])+1000)/1e3,curve.delete)
	combine.connectattr('output',node,attr)
	if not loop:_bascenev1.timer((int(mult*items[-1][0])+1000)/1e3,combine.delete)
def set_allow_kick_idle_players(allow,*,persist=True):
	new_status=bool(allow)
	try:globalsnode=_bascenev1.getactivity().globalsnode;globalsnode.allow_kick_idle_players=new_status
	except babase.ActivityNotFoundError:
		try:globalsnode=_bascenev1.getsession().sessionglobalsnode;globalsnode.allow_kick_idle_players=new_status
		except babase.SessionNotFoundError:pass
	if persist:
		cfg=babase.app.config
		if cfg.get('Kick Idle Players',False)!=new_status:cfg['Kick Idle Players']=new_status;cfg['Garbage Collection Mode']='disabled';cfg.apply_and_commit()
def show_damage_count(damage,position,direction,dead=False):
	lifespan=1.;app=babase.app;assert app.classic is not None;do_big=app.ui_v1.uiscale is babase.UIScale.SMALL or app.env.vr;txtnode=_bascenev1.newnode('text',attrs={'text':damage,'in_world':True,'h_align':'center','flatness':1.,'shadow':1. if do_big else .7,'color':(.2,.2,.2,1)if dead else(1,.25,.25,1),'scale':.015 if do_big else .01});tcombine=_bascenev1.newnode('combine',owner=txtnode,attrs={'size':3});tcombine.connectattr('output',txtnode,'position');v_vals=[];pval=.0;vval=.07;count=6
	for i in range(count):v_vals.append((float(i)/count,pval));pval+=vval;vval*=.5
	p_start=position[0];p_dir=direction[0];animate(tcombine,'input0',{i[0]*lifespan:p_start+p_dir*i[1]for i in v_vals});p_start=position[1];p_dir=direction[1];animate(tcombine,'input1',{i[0]*lifespan:p_start+p_dir*i[1]for i in v_vals});p_start=position[2];p_dir=direction[2];animate(tcombine,'input2',{i[0]*lifespan:p_start+p_dir*i[1]for i in v_vals});animate(txtnode,'opacity',{.7*lifespan:1.,lifespan:.0});_bascenev1.timer(lifespan,txtnode.delete)
def cameraflash(duration=999.):
	from bascenev1._nodeactor import NodeActor;x_spread=10;y_spread=5;positions=[[-x_spread,-y_spread],[0,-y_spread],[0,y_spread],[x_spread,-y_spread],[x_spread,y_spread],[-x_spread,y_spread]];times=[0,2700,1000,1800,500,1400];activity=_bascenev1.getactivity();activity.camera_flash_data=[]
	for i in range(6):light=NodeActor(_bascenev1.newnode('light',attrs={'position':(positions[i][0],0,positions[i][1]),'radius':1.,'lights_volumes':False,'height_attenuated':False,'color':(.2,.2,.8)}));sval=1.87;iscale=1.3;tcombine=_bascenev1.newnode('combine',owner=light.node,attrs={'size':3,'input0':positions[i][0],'input1':0,'input2':positions[i][1]});assert light.node;tcombine.connectattr('output',light.node,'position');xval=positions[i][0];yval=positions[i][1];spd=.5+random.random();spd2=.5+random.random();animate(tcombine,'input0',{.0:xval+0,.069*spd:xval+1e1,.143*spd:xval-1e1,.201*spd:xval+0},loop=True);animate(tcombine,'input2',{.0:yval+0,.15*spd2:yval+1e1,.287*spd2:yval-1e1,.398*spd2:yval+0},loop=True);animate(light.node,'intensity',{.0:0,.02*sval:0,.05*sval:.8*iscale,.08*sval:0,.1*sval:0},loop=True,offset=times[i]);_bascenev1.timer((times[i]+random.randint(1,int(duration))*40*sval)/1e3,light.node.delete);activity.camera_flash_data.append(light)
def apply():
	import importlib;public_api=importlib.import_module('bascenev1');orig_module=importlib.import_module('bascenev1._gameutils');additions=['set_allow_kick_idle_players']
	for name in additions:setattr(orig_module,name,globals()[name]);setattr(public_api,name,globals()[name])