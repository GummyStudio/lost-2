import bascenev1 as bs
import babase
from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, StunMessage

class BearSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 100

    move_speed = 0.80 # 0.7 if gun or bash equipped
    run_speed = 0.95 # ditto
    ability1_cooldown = 30
    ability2_cooldown = 40
    ability3_cooldown = 1.0

    ability1_icon = babase.charstr(babase.SpecialChar.OCULUS_LOGO)
    ability2_icon = babase.charstr(babase.SpecialChar.FIREBALL)
    ability3_icon = babase.charstr(babase.SpecialChar.PLAY_BUTTON)


    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'block_start': bs.getsound('Blockstart'),# holy kronk steal
            'block_success': bs.getsound('Blocksuccess'),
            'punch_windup': bs.getsound('Punchwindup'),
            'punch_hit': bs.getsound('Guest1337punch'),
            'punch_parry': bs.getsound('Guestparry'),
            
            
            'gun_equip': bs.getsound('gh_equipgun'),
            'gun_unequip': bs.getsound('gh_unequipgun'),
            'gun_shoot': bs.getsound('gh_shootgun'),
            'bash_equip': bs.getsound('gh_bashequip'),
            'bash_swing': bs.getsound('gh_bashswing'),
            'bash_hit': bs.getsound('gh_bashhit'),
            'bash_ch1': bs.getsound('gh_charge1'),
            'bash_ch2': bs.getsound('gh_charge2'),
            'bash_ch3': bs.getsound('gh_charge2'),
            
        }
        self.factory = AsymFactory.get()
        
        # -- guest shit so it doesnt fucking die from no variable
        
        self.is_blocking = False
        self.has_parry_counter = False
        self.block_timer = None
        
        
        self.is_using_literally_anything = False
        self.gun_equipped = False
        self.bash_equipped = False
        self.bash_charges = 1
        
        
    def ability1_extra_conditions(self):
        return self.gun_equipped

    

    def ability1(self):
        
        # -- Bash -- Gunhound pulls out her BB Gun, when pressing the attack key she starts to charge her gunbash with 1 charge every second.
        #            When the attack key is pressed again, she will release her charges. See ability3
        
        if bash_equipped == False and gun_equipped == False:
            self.play_sound('bash_equip')
            bash_equipped = True
            self.bash_equip_celebration_loop()
        elif bash_equipped == True and gun_equipped == False:
            self.play_sound('bash_equip')
            bash_equipped = False
        else:
            pass
        
        # self.play_sound('punch_windup')
        # punch_dur = 0.5
        # if self.has_parry_counter:
            # punch_dur = 0.12
        # self.spaz.node.handlemessage('celebrate_l', punch_dur*1000)
      
        # self.spaz.max_walk_speed *= 0.2
        # self.spaz.max_run_speed *= 0.1
        # def punch():
            # self.spaz.impulse(x=5 if self.has_parry_counter else 2, y=1)
            # self.spaz.node.punch_pressed = True
            # self.spaz.node.punch_pressed = False
            # self.spaz.max_walk_speed /= 0.2
            # self.spaz.max_run_speed /= 0.1
        # bs.timer(punch_dur, punch)
    
    def ability2(self):
        
        # -- Shoot -- Gunhound will start holding her shotgun, although she cannot jump or sprint in this state.
        
        if gun_equipped == False and bash_equipped == False:
            
        
        
     # #block
        # self.is_blocking = True
        # self.play_sound('block_start', position=self.spaz.node.position)
        # self.spaz.handlemessage(bs.CelebrateMessage(1.2))
        
        # self.block_timer = bs.timer(1.2, bs.WeakCall(self._stop_blocking))

    def gun_equip_celebration_loop(self):
        while gun_equipped:
            self.spaz.node.handlemessage('celebrate', 2)
    def bash_equip_celebration_loop(self):
        while bash_equipped:
            self.spaz.node.handlemessage('celebrate_l', 2)
  
        
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

   