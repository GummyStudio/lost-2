import bascenev1 as bs
import babase
from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, StunMessage, KillerDetectedMessage
import random

class DashHitbox(bs.Actor):
    def __init__(self,position, moveset):
        super().__init__()
        self.moveset = moveset
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': (0,0,0),
                    'body': 'sphere',
                    'body_scale': 2,
                    'mesh_scale': 0.0,
                    'shadow_size': 0.44,
                    'materials': [AsymFactory.get().survivor_trap_object_material],
                },
            )
        self.active = True
        
       
        bs.timer(0.11, bs.WeakCall(self.handlemessage, bs.DieMessage()))
    
    def on_expire(self):
        self.owner = None
        self.moveset = None
        
    
    def exists(self):
        return bool(self.node)

    def is_alive(self):
        return bool(self.node)

        

   

    def handlemessage(self, msg):
        if isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, KillerDetectedMessage):
            if not self.moveset:
                return
            if not self.active:
                return
            if not self.is_alive():
                return
            self.active = False
            
            node = bs.getcollision().opposingnode
            # tell da owner we got em
            self.moveset.dash_hit_spaz(node.getdelegate(bs.Actor))
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            self.active = False
            self.node.delete()
        return super().handlemessage(msg)
    
class KronkSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 115
    
    description = (
        "Kronk is a surprisingly aggressive support class, "
        "helping his teammates by simply beating up the killer."
        "{'type': 'separator'}"
        "Or well, in this case, just stunning them."
    )
    ability1_description = "Punches a killer to slightly stun and damage them."
    ability2_description = "Attempt to block an attack. Punch shortly afterwards to do a parry and strongly stun the killer."
    ability3_description = "Charge forward to hit and stun a killer."

    move_speed = 0.85
    run_speed = 0.9
    ability1_cooldown = 55
    ability2_cooldown = 22
    ability3_cooldown = 35

    ability1_icon = babase.charstr(babase.SpecialChar.SKULL)
    ability2_icon = babase.charstr(babase.SpecialChar.PAUSE_BUTTON)
    ability3_icon = 'C'

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'block_start': bs.getsound('Blockstart'),
            'block_success': bs.getsound('Blocksuccess'),
            'punch_windup': bs.getsound('Punchwindup'),
            'punch_hit': bs.getsound('Guest1337punch'),
            'punch_parry': bs.getsound('Guestparry'),
            'dash_sfx': bs.getsound('kronkFall'),
            'dash_hit': bs.getsound('Chargehit'),
            'dash_stop': bs.getsound('Chargingtimeout'),
        }
        self.factory = AsymFactory.get()
        
        self.is_blocking = False
        self.has_parry_counter = False
        self.block_timer = None
        self.is_dashing = False 
        self.dash_timer = None
        self.dash_sfx = bs.Node(None)
        self.cancel_dash_timer = None
    
    def create_dash_sfx(self):
        self.dash_sfx = bs.newnode('sound', attrs={
            'sound': self.sfx.get('dash_sfx'), 'volume': 5,
        })

    def ability1_extra_conditions(self):
        return not self.is_dashing and not self.is_blocking
    def ability2_extra_conditions(self):
        return not self.is_dashing and not self.is_blocking
    def ability3_extra_conditions(self):
        return not self.is_dashing and not self.is_blocking

    

    def ability1(self):
        self._punched_nodes = set()
        self.play_sound('punch_windup')
        punch_dur = 0.5
        if self.has_parry_counter:
            punch_dur = 0.12
        self.spaz.node.handlemessage('celebrate_l', punch_dur*1000)
      
        self.spaz.max_walk_speed *= 0.2
        self.spaz.max_run_speed *= 0.1
        def punch():
            self.spaz.max_walk_speed /= 0.2
            self.spaz.max_run_speed /= 0.1
            self.spaz.impulse(x=12 if self.has_parry_counter else 7, y=1)
            self.spaz.node.punch_pressed = True
            self.spaz.node.punch_pressed = False
            
        bs.timer(punch_dur, punch)
    
    def ability2(self):
     #block
        self.is_blocking = True
        self.play_sound('block_start', position=self.spaz.node.position)
        self.spaz.handlemessage(bs.CelebrateMessage(1.2))
        
        self.block_timer = bs.timer(1.2, bs.WeakCall(self._stop_blocking))
       


  
        
    def _stop_blocking(self):
        self.is_blocking = False
        self.block_timer = None
       

    def handle_recieved_damage(self, damage, type):
        if self.is_blocking:
            self._stop_blocking()
            self.has_parry_counter = True
            self.spaz.speed_boost(0.25)
            #  Reset cooldown
            self._last_used_1 = -999
            
            self.play_sound('block_success', position=self.spaz.node.position)
            bs.timer(1, bs.Call(setattr, self, 'has_parry_counter', False))
            
            return False
            
        return True

    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return False

        if self.node_not_punched_nodes(node):# and len(self._punched_nodes) == 0: hehe 
            self._punched_nodes.add(node)
            if self.has_parry_counter:
                
                self.has_parry_counter = False 
                
                node.handlemessage(
                    DamageMessage(
                        damage=35,  
                        spaz=self.spaz,
                        type='kronk_parry',
                        hurt_sound=None,
                    )
                )
                node.handlemessage(StunMessage(duration=3.5, knockback_settings={
                    'x': 18,
                    'y': 9,
                    'direction': node.velocity
                }))
                self.play_sound('punch_parry', position=self.spaz.node.position)
            else:
                node.handlemessage(
                    DamageMessage(
                        damage=10,
                        spaz=self.spaz,
                        type='kronk_punch',
                        hurt_sound=None,
                    )
                )
                node.getdelegate(bs.Actor).impulse(
                    x=-4.5,
                    y=-0.2,
                    direction=node.velocity
                )
                def revert():
                    if not node:
                        return
                    node.getdelegate(bs.Actor).max_walk_speed /= 0.5
                    node.getdelegate(bs.Actor).max_run_speed /= 0.2
                node.getdelegate(bs.Actor).max_walk_speed *= 0.5
                node.getdelegate(bs.Actor).max_run_speed *= 0.2
                bs.timer(0.6, revert)
                self.play_sound('punch_hit', position=self.spaz.node.position)

        return False

    def cancel_dash(self):
        self._last_used_3 = bs.time()
        self.is_dashing = False
        self.dash_timer = None
        self.spaz.allow_movement = True
        self.dash_sfx.delete()
        self.cancel_dash_timer = None
        self.play_sound('dash_stop')
    
    def dash(self):
        if not self.spaz.exists():
            self.dash_sfx.delete()
            return
        if not self.is_dashing:
            self.cancel_dash()
            return
    
        # make sure its false
        self.spaz.allow_movement = False
        
        
        dir_x = self.spaz.input_x* 0.35
        dir_y = -1.0
        dir_z = -self.spaz.input_y * 0.35
        target_speed = 5.0 
  
        cur_vx, cur_vy, cur_vz = self.spaz.node.velocity
        current_speed_in_dir = (cur_vx * dir_x) + (cur_vy * dir_y) + (cur_vz * dir_z)
        speed_difference = target_speed - current_speed_in_dir

        impulse_scale = max(0.0, speed_difference / target_speed)

        self.spaz.impulse(
            x=4.5 * impulse_scale, 
            y=-2 * impulse_scale, 
            direction=(dir_x, dir_y, dir_z)
        )

    
        # and create le hitox
        DashHitbox(self.spaz.node.position, self).autoretain()
    
  
    
    def dash_hit_spaz(self, spaz):
        if not self.is_dashing:
            return
        if not spaz:
            return
        self.play_sound(
            'dash_hit'
        )
        
        spaz.handlemessage(
            DamageMessage(
                damage=5,
                type='kronk_dash'
            )
        )
        spaz.impulse(
                    x=90.5,
                    y=0.2,
                    direction=self.spaz.node.velocity
                )
        self.cancel_dash()
            
            

    def ability3(self):
        self.spaz.allow_movement = False
        self.is_dashing = True
        self.create_dash_sfx()
        self.dash_timer = bs.Timer(0.1, self.dash, repeat=True)
        self.spaz.handlemessage(bs.CelebrateMessage(1.2))
        self.cancel_dash_timer = bs.Timer(1.2, self.cancel_dash)
        


   