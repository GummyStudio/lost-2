import bascenev1 as bs
import babase
from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, StunMessage
from lost.killers.maskedman import Beam as shooter # dont feel like copypasting allat lol

class BearSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 100

    move_speed = 0.80 # 0.7 if gun or bash equipped
    run_speed = 0.95 # ditto
    ability1_cooldown = 2.0
    ability2_cooldown = 2.0
    ability3_cooldown = 0.2

    ability1_icon = babase.charstr(babase.SpecialChar.OCULUS_LOGO)
    ability2_icon = babase.charstr(babase.SpecialChar.FIREBALL)
    ability3_icon = babase.charstr(babase.SpecialChar.PLAY_BUTTON)


    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {  
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
        
        self.gun_equipped = False
        self.has_shot_before = False
        self.bash_equipped = False
        self.bash_charges = 0

    def ability1(self):
        
        # -- Bash -- Gunhound pulls out her BB Gun, and she starts to charge her gunbash with 1 charge every second.
        #            When the attack key is pressed, she will release her charges. See ability3
        
        if self.bash_equipped == False and self.gun_equipped == False:
            self.play_sound('bash_equip')
            self.bash_equipped = True
            self.bash_equip_celebration_loop()
            bs.timer(1,bs.Call(self.bash_flash, (1,0,0), 1)) #red
        else:
            pass
    def bash_flash(self, color, charge_amount):
    
        if charge_amount >= 3:
            charge_amount = 3 # make sure we don't get an error for not having a sound for charge 5
        
        # store colors
        playecolore = self.spaz.node.color
        playehilit = self.spaz.node.highlight
        
        # play the according charge sound
        self.play_sound('bash_ch'+str(charge_amount))
        
        # bs animate array! hooraye.
        bs.animate_array(self.spaz.node, "color", 3, {
            0:color,
            1:playecolore
            }
        )
        bs.animate_array(self.spaz.node, "highlight", 3, {
            0:color,
            1:playehilit
            }
        )
        print(self.bash_charges)
        self.bash_charges += 1
        print(self.bash_charges)
        
        
        # JOHN SWITCHCASE because i can't fucking chain bs.timers??? This shit sucks.
        # gummy: dude fuck off im rewriting all ts becuase yousuck ass
        # budfdie: sorry bro its 5am i cant code for shit at this hours
        # gummy: ok no problem bro i spare you :3
        # and then we make out furiously and passionately
        if self.bash_charges == 1:
            bs.timer(1,bs.Call(self.bash_flash, (1,1,0), 2)) # yellow
        elif self.bash_charges == 2:
            bs.timer(1,bs.Call(self.bash_flash, (0,1,0), 3)) # green! this is where you press atk
        elif self.bash_charges == 3:
            bs.timer(1,bs.Call(self.bash_flash, (1,1,0), 4)) # yellow
        elif self.bash_charges == 4:
            bs.timer(1,bs.Call(self.bash_flash, (1,0,0), 5)) # red, last chance to press atk...
        else:
            self.bash_charges = 0 # haha you missed
            
       
    def small_slowdown(self):
        self.move_speed /= 1.2
        self.run_speed /= 1.2
        bs.timer(0.6, small_slowdown_recover)
    def small_slowdown_recover(self):
        self.move_speed *= 1.2
        self.run_speed *= 1.2
    def ability2(self):
        
        # -- Shoot -- Gunhound will start holding her shotgun, although she cannot sprint in this state.

        if self.gun_equipped == False and self.bash_equipped == False:
            self.play_sound('gun_equip')
            self.gun_equipped = True
            self.gun_equip_celebration_loop()
            self.move_speed /= 1.142857
            self.run_speed /= 1.35714
        elif self.gun_equipped == True and self.bash_equipped == False:
            self.play_sound('gun_unequip')
            self.gun_equipped = False
            self.move_speed *= 1.142857
            self.run_speed *= 1.35714
            
            
    def ability3_extra_conditions(self):
        if not self.gun_equipped and not self.bash_equipped:
            return False


    def ability3(self):
        
        # -- Attack -- Basically just the M1 counterpart to Lost as an ability, will use her currently equipped weapon.
        # Bash: Will give debuffs according to its charge
        # Shoot: Will give debuffs and then stun
        
        def shoot(): # taken strait outta masked man!
            if not self.spaz.node:
                return
            self.spaz.node.punch_pressed = True
            try: 
                bs.timer(0, bs.Call(setattr, self.spaz.node, 'punch_pressed', False))
            except: 
                pass
            x = self.spaz.node.move_left_right
            z = -self.spaz.node.move_up_down
            pos = self.spaz.node.torso_position
            pos = (
                pos[0] + x,
                pos[1],
                pos[2] + z,
            )
            beam = shooter.Beam(
                position=pos,
                owner=self.spaz,
                tex_text='bonesColorMask' # first red thing i saw ok
            ).autoretain()
            beam.node.velocity = (x*20, 0, z*20)
            mag = -460
            ppos = self.spaz.node.position
            punchdir = self.spaz.node.velocity
            self.spaz.node.handlemessage(
                'kick_back',
                ppos[0],
                ppos[1],
                ppos[2],
                punchdir[0],
                punchdir[1],
                punchdir[2],
                mag,
            )
            direction = bs.Vec3(x, 0.1, z)
            direction = direction * 5
            pos = self.spaz.node.torso_position
            bs.emitfx(
                position=pos,
                chunk_type='spark',
                velocity=direction,
                count=30,
                scale=0.7,
                spread=0.35,
            )
        self.play('gun_shoot')
        time = 0.7
        self.spaz.node.handlemessage('celebrate_l', time*1000)
        bs.timer(time, shoot)
        

    def gun_equip_celebration_loop(self):
        if self.gun_equipped:
            self.spaz.node.handlemessage('celebrate', 2)
            bs.timer(0.1,self.gun_equip_celebration_loop)
    def bash_equip_celebration_loop(self):
        if self.bash_equipped:
            self.spaz.node.handlemessage('celebrate_l', 2)
            bs.timer(0.1,self.bash_equip_celebration_loop)
   