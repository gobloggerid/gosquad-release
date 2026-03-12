# ba_meta require api 9
import bascenev1 as ba
import random
from bascenev1lib.actor import spaz

def myOnJumpPress(Slade):
    def wrapper(self):
        is_moving = abs(self.node.move_up_down) >= 0.5 or abs(self.node.move_left_right) >= 0.5
        if not self.node.exists(): return
        t = 0
        self.last_jump_time_ms = -9999
        if t - self.last_jump_time_ms >= self._jump_cooldown:
            self.node.jump_pressed = True
            if t - self.last_punch_time_ms<=20 and is_moving and self.node.jump_pressed and self.node.punch_pressed:
            	
                self.node.handlemessage("impulse",self.node.position[0],self.node.position[1]-3,self.node.position[2],self.node.velocity[0],self.node.velocity[1],self.node.velocity[2],50*self.node.run,10*self.node.run,0,0,self.node.velocity[0],self.node.velocity[1],self.node.velocity[2])
                self.node.handlemessage("impulse",self.node.position[0],self.node.position[1]-5,self.node.position[2],self.node.velocity[0],self.node.velocity[1],self.node.velocity[2],50*self.node.run,20*self.node.run,0,0,self.node.velocity[0],self.node.velocity[1],self.node.velocity[2])
                self.node.handlemessage("impulse",self.node.position[0],self.node.position[1]-5,self.node.position[2],0,10,0,50,20,0,0,0,10,0)
                
                ba.emitfx(position=self.node.position,
                    chunk_type='sweat',
                    count=12,
                    scale=3.0,
                    spread=0.6);
                ba.emitfx(position=self.node.position,
                    chunk_type='spark',
                    count=12,
                    scale=1.0,
                    spread=0.4);
                ba.emitfx(position=(self.node.position[0],self.node.position[1]-0.3,self.node.position[2]), velocity=(self.node.velocity[0]*5,self.node.velocity[1]*2,self.node.velocity[2]), count=random.randrange(12,20), scale=2.4, spread=0.40, chunk_type='sweat')
            self.last_jump_time_ms = t
        self._turbo_filter_add_press('jump')
    return wrapper

# ba_meta export babase.Plugin
class Droopyyyy(ba.Plugin):
    def __init__(self):
        spaz.Spaz.on_jump_press = myOnJumpPress(spaz.Spaz.on_jump_press)
