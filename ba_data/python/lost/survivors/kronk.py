import bascenev1 as bs
import babase
from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, StunMessage

class KronkSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 115

    move_speed = 0.85
    run_speed = 0.9
    ability1_cooldown = 55
    ability2_cooldown = 22
    ability3_cooldown = 0.0

    ability1_icon = babase.charstr(babase.SpecialChar.SKULL)
    ability2_icon = babase.charstr(babase.SpecialChar.PAUSE_BUTTON)
    ability3_icon = ''

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'block_start': bs.getsound('Blockstart'),
            'block_success': bs.getsound('Blocksuccess'),
            'punch_windup': bs.getsound('Punchwindup'),
            'punch_hit': bs.getsound('Guest1337punch'),
            'punch_parry': bs.getsound('Guestparry'),
        }
        self.factory = AsymFactory.get()
        
        self.is_blocking = False
        self.has_parry_counter = False
        self.block_timer = None

    def ability1_extra_conditions(self):
        return not self.is_blocking

    

    def ability1(self):
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
            self.spaz.impulse(x=5 if self.has_parry_counter else 2, y=1)
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
       

    def handle_recieved_damage(self):
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

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
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
                    'x': 13,
                    'y': 6,
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
                self.play_sound('punch_hit', position=self.spaz.node.position)

        return False

    def ability3(self):
        pass

   