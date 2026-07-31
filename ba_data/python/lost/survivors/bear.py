from typing import override, Any
import bascenev1 as bs # pyright: ignore[reportMissingImports]
import babase # pyright: ignore[reportMissingImports] # shut UPPPPP vs code dont cry because i only imported survivors folder
from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, StunMessage, Lobby, KillerDetectedMessage # importing lobby so i can cancel cd
from bascenev1lib.actor.popuptext import PopupText
import random
from bascenev1lib.gameutils import SharedObjects
import bascenev1 as bs
import babase

class Beam(bs.Actor): # strait from naked man
    def __init__(
        self,
        position: tuple[float],
        owner: bs.Actor,
    ):
        super().__init__()
        self.mesh = bs.getmesh('bomb')
        self.tex = bs.gettexture('bonesColorMask')
        self.scale = 0.9
        self.bscale = 1.2
        self.owner = owner
        self.hurtpoints = random.randint(300, 1000)
        shared = SharedObjects.get()
        asymf = AsymFactory.get()
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'sphere',
                'body_scale': self.bscale,
                'position': position,
                'mesh': self.mesh,
                'mesh_scale': 0,
                'light_mesh': self.mesh,
                'shadow_size': self.bscale,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'gravity_scale': 0,
                'materials': (
                    asymf.survivor_trap_object_material, 
                    shared.object_material,
                    asymf.no_wall_collide,
                ),
            },
        )
        self.dying = False
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.2: self.scale})
        
    @override
    def handlemessage(self, msg: Any) -> Any:
        if self.expired:
            return None
            
        if isinstance(msg, bs.DieMessage):
            self.dying = True
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(self.node, 'mesh_scale', {0: self.scale, 0.1: 0})
                bs.timer(0.1, self.node.delete)
                
        elif isinstance(msg, KillerDetectedMessage):
            collision = bs.getcollision()
            toucher = collision.opposingnode
            if not toucher:
                return None
            ishittable = toucher.getnodetype() in ['spaz']
            if self.dying:
                return
            if not ishittable:
                return None
            actor = toucher.getdelegate(bs.Actor)
            other_beam = toucher.getdelegate(Beam)
            if (
                not actor
                or not actor.is_alive()
                or actor is self.owner
                or other_beam
                or self.dying
            ):
                return None
            bs.emitfx(
                position=self.node.position,
                chunk_type='spark',
                velocity=self.node.velocity,
                count=65,
                scale=2.0,
                spread=0.8,
            )
            dmg = 20
            # ew.
            actor.handlemessage(
                DamageMessage(
                    damage=int(dmg),
                    spaz=self.owner,
                    type='gh_bullet',
                )
            )
            if owner.landed_first_shot:
                actor.handlemessage(
                    StunMessage(
                    duration=3, knockback_settings={
                        'x': 7,
                        'y': 5,
                        'direction': node.velocity
                        }
                    )
                )
                owner.landed_first_shot = False
            else:
                owner.landed_first_shot = True
            self.handlemessage(bs.DieMessage())
            
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else:
            return super().handlemessage(msg)
        return None

class BearSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 100

    move_speed = 0.80 # 0.7 if gun or bash equipped
    run_speed = 0.95 # ditto
    ability1_cooldown = 20.0
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
        self.landed_first_shot = False
        self.bash_equipped = False
        self.bash_charges = 0
        self.stored_bash_charges = 0 # this one is never changed, except when using bash again, good for using functions

    def ability1(self):
        
        # -- Bash -- Gunhound pulls out her BB Gun, and she starts to charge her gunbash with 1 charge every second.
        #            When the attack key is pressed, she will release her charges. See ability3
        
        if self.bash_equipped == False and self.gun_equipped == False:
            self.bash_charges = 0
            self.stored_bash_charges = 0
            self.play_sound('bash_equip')
            self.bash_equipped = True
            self.bash_equip_celebration_loop()
            bs.timer(1,bs.Call(self.bash_flash, (1,0,0), 1)) #red
        else:
            pass
    def bash_flash(self, color, charge_amount):
        if self.bash_charges == -1:
            return
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

        self.bash_charges += 1
        
        # JOHN SWITCHCASE because i can't fucking chain bs.timers??? This shit sucks.
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
            self.bash_equipped = False
            self.small_slowdown()
            
       
    def small_slowdown(self):
        self.move_speed /= 1.2
        self.run_speed /= 1.2
        bs.timer(0.6, self.small_slowdown_recover) # type: ignore
    def small_slowdown_recover(self):
        self.move_speed *= 1.2
        self.run_speed *= 1.2

    def ability2(self):
        
        # -- Shoot -- Gunhound will start holding her shotgun, although she cannot sprint in this state.
        self.has_shot_before = False
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

    def ability3(self):
        
        # -- Attack -- Basically just the M1 counterpart to Lost as an ability, will use her currently equipped weapon.
        # Bash: Will give debuffs according to its charge
        # Shoot: Will give debuffs and then stun on second use
        
        if self.gun_equipped == True:
            self.gun_equipped = False
            def do_literally_everything():
                def shoot(): # taken strait outta masked man!
                    if not self.spaz.node:
                        return
                    self.spaz.node.punch_pressed = True
                    try: 
                        bs.timer(0, bs.Call(self.spaz.safesetattr, self.spaz.node, 'punch_pressed', False))
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
                    beam = Beam(
                        position=pos,
                        owner=self.spaz
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
                self.play_sound('gun_shoot')
                time = 0.4
                self.spaz.node.handlemessage('celebrate_l', time*1000)
                def bee_ess_tmer():
                    bs.timer(time, shoot)
                bee_ess_tmer()
            do_literally_everything()
            if self.has_shot_before == False:
                bs.timer(1,do_literally_everything)
                self.has_shot_before = True
            if isinstance(bs.getactivity(), Lobby):
                pass
            else:
                self.ability2_cooldown = 41
                self._last_used_2 = bs.time()-1
        elif self.bash_equipped == True:
            self.bash_equipped = False
            self.stored_bash_charges = self.bash_charges
            self.bash_charges = -1
            self._punched_nodes = set()
        
            self.spaz.node.punch_pressed = True
            self.spaz.node.punch_pressed = False
            self.spaz.max_walk_speed *= 0.1
            
            def revert():
                self.spaz.impulse(x=4.5, y=1)
                self.spaz.max_walk_speed /= 0.1
            bs.timer(0.1, revert)
        else:
            PopupText(
                'Nothing in your\nhands to fire.',
                position=self.spaz.node.position,
                scale=1.0
            ).autoretain()
    
    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        if self.stored_bash_charges == 0: # too early
            walk_slwdn = 0.8
            run_slwdn = 0.9
        elif self.stored_bash_charges == 1: # eh
            walk_slwdn = 0.6
            run_slwdn = 0.8
        elif self.stored_bash_charges == 2: # p good
            walk_slwdn = 0.5
            run_slwdn = 0.6
        elif self.stored_bash_charges == 3: # perfect
            walk_slwdn = 0.4
            run_slwdn = 0.5
        elif self.stored_bash_charges >= 4: # too late
            walk_slwdn = 0.8
            run_slwdn = 0.9
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=30,
                    spaz=self.spaz,
                    type='gh_bash',
                    hurt_sound='bash_hit',
                )
            )
            self.play_sound('bash_swing', position=self.spaz.node.position)
            self._punched_nodes.add(node)
            def revert():
                if not node:
                    return
                node.getdelegate(bs.Actor).max_walk_speed /= walk_slwdn
                node.getdelegate(bs.Actor).max_run_speed /= run_slwdn
            node.getdelegate(bs.Actor).max_walk_speed *= walk_slwdn
            node.getdelegate(bs.Actor).max_run_speed *= run_slwdn
            bs.timer(2, revert)

        return False



    def gun_equip_celebration_loop(self):
        if self.gun_equipped:
            self.spaz.node.handlemessage('celebrate', 2)
            bs.timer(0.1,self.gun_equip_celebration_loop)
    def bash_equip_celebration_loop(self):
        if self.bash_equipped:
            self.spaz.node.handlemessage('celebrate_l', 2)
            bs.timer(0.1,self.bash_equip_celebration_loop)
   