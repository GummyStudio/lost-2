from lost.factory import (
    AsymFactory,
    DamageMessage,
    StunMessage,
    KillerDetectedMessage,
    SurvivorDetectedMessage,
)
from lost.character_moveset import CharacterMoveset
import bascenev1 as bs, random
import babase

class B9000DeathBlast(bs.Actor):
 

    def __init__(
        self,
        *,
        position=(0.0, 1.0, 0.0),
    ):
        """Instantiate with given values."""

        # bah; get off my lawn!
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        super().__init__()
        from bascenev1lib.gameutils import SharedObjects

        shared = SharedObjects.get()
        factory = AsymFactory.get()

        self.radius = 2.0
        velocity = (0, 0, 0)

        # Set our position a bit lower so we throw more things upward.
        rmats = (factory.survivor_trap_object_material, shared.attack_material)
        self.node = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': (position[0], position[1] - 0.1, position[2]),
                'scale': (self.radius, self.radius, self.radius),
                'type': 'sphere',
                'materials': rmats,
            },
        )

        bs.timer(0.05, self.node.delete)

        # Throw in an explosion and flash.
        evel = (velocity[0], max(-1.0, velocity[1]), velocity[2])
        explosion = bs.newnode(
            'explosion',
            attrs={
                'position': position,
                'velocity': evel,
                'radius': self.radius,
                'big': True,
            },
        )
    

        bs.timer(1.0, explosion.delete)

        bs.emitfx(
            position=position,
            velocity=velocity,
            count=int(4.0 + random.random() * 4),
            emit_type='tendrils',
            tendril_type='smoke',
        )
        bs.emitfx(
            position=position,
            emit_type='distortion',
            spread=1.0 ,
        )

        # And emit some shrapnel.
        if False:
            pass

        else:  # Regular or land mine bomb shrapnel.

            def emit() -> None:
                if True:
                    bs.emitfx(
                        position=position,
                        velocity=velocity,
                        count=int(4.0 + random.random() * 8),
                        chunk_type='rock',
                    )
                    bs.emitfx(
                        position=position,
                        velocity=velocity,
                        count=int(4.0 + random.random() * 8),
                        scale=0.5,
                        chunk_type='rock',
                    )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=30,
                    scale=0.7,
                    chunk_type='spark',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(18.0 + random.random() * 20),
                    scale=0.8,
                    spread=1.5,
                    chunk_type='spark',
                )

                

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        lcolor = (1, 0.3, 0.1)
        light = bs.newnode(
            'light',
            attrs={
                'position': position,
                'volume_intensity_scale': 10.0,
                'color': lcolor,
            },
        )

        scl = random.uniform(0.6, 0.9)
        scorch_radius = light_radius = self.radius
       

        iscale = 1.6
        bs.animate(
            light,
            'intensity',
            {
                0: 2.0 * iscale,
                scl * 0.02: 0.1 * iscale,
                scl * 0.025: 0.2 * iscale,
                scl * 0.05: 17.0 * iscale,
                scl * 0.06: 5.0 * iscale,
                scl * 0.08: 4.0 * iscale,
                scl * 0.2: 0.6 * iscale,
                scl * 2.0: 0.00 * iscale,
                scl * 3.0: 0.0,
            },
        )
        bs.animate(
            light,
            'radius',
            {
                0: light_radius * 0.2,
                scl * 0.05: light_radius * 0.55,
                scl * 0.1: light_radius * 0.3,
                scl * 0.3: light_radius * 0.15,
                scl * 1.0: light_radius * 0.05,
            },
        )
        bs.timer(scl * 3.0, light.delete)

        # Make a scorch that fades over time.
        scorch = bs.newnode(
            'scorch',
            attrs={
                'position': position,
                'size': scorch_radius * 0.5,
                'big': True,
            },
        )
     
        bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
        bs.timer(13.0, scorch.delete)

  
    def handlemessage(self, msg):
        assert not self.expired

        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()

        elif isinstance(msg, KillerDetectedMessage):
            node = bs.getcollision().opposingnode 
            node.handlemessage(DamageMessage(
                damage=50, type='b9000_death_blast',
                )
            )  
            node.handlemessage(
                            StunMessage(
                                duration=4,
                                spaz=None,
                                type='b9000_death_blast',
                                knockback_settings={
                                    'x': -5,
                                    'y': 8,
                                    'direction': (
                                        -node.velocity[0],
                                        node.velocity[1],
                                        -node.velocity[2]
                                    )
                                },
                                use_node_knockout_message=True
                            )
                        )

        else:
            return super().handlemessage(msg)
        return None

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
                    'body_scale': 1.25,
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
    
class B9000Survivor(CharacterMoveset):
    is_killer = False
    hitpoints = 200
    

    move_speed = 0.85
    run_speed =  0.9
    ability1_cooldown = 40
    ability2_cooldown = 0.0
    ability3_cooldown = 35

    ability1_icon = babase.charstr(babase.SpecialChar.RIGHT_ARROW)
    ability2_icon = ''
    ability3_icon = '+'

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'dash_end': bs.getsound('b9000dashEnd'),
            'dash_start': bs.getsound('b9000DashStart'), 
            'dash_loop': bs.getsound('b9000dashIdle'), 
            'dash_hit': bs.getsound('b9000DashHIT'),
            'dash_slam1': bs.getsound('b9000DashSlam1'),
            'dash_slam2': bs.getsound('b9000DashSlam2'),
            'dash_hurt': bs.getsound('b9000dash_atk'),

            'heal_start': bs.getsound('b9000HealStart'), 
            'heal': bs.getsound('b9000Heal'), 
            'heal_end': bs.getsound('b9000Healend'), 

            'die': bs.getsound('b9000DEATH'),
            'death_is_coming': bs.getsound('ggbro'),
        }
        self.factory = AsymFactory.get()
        self.healing = False
        self.is_dashing = False 
        self.dash_timer = None
        self.dash_sfx = bs.Node(None)
        self.cancel_dash_timer = None
        self.hitting_timer = None

        self.grabbed_the_killer = False
        self.die_upon_ungrab = False
        self.die_warning_sfx = bs.Node(None)
    
    def spaz_lost_all_hp(self, type):
        if self.spaz and self.spaz.exists():
            self.play_sound('die')
            self.spaz.impulse(
                x=random.uniform(-2, 2),
                y=-2, 
                direction=self.spaz.node.velocity
            )
            B9000DeathBlast(position=self.spaz.node.position).autoretain()

        super().spaz_lost_all_hp(type)
    
    def create_dash_sfx(self):
        self.dash_sfx = bs.newnode('sound', attrs={
            'sound': self.sfx.get('dash_loop'), 'volume': 1,
        })

    
    def ability1_extra_conditions(self):
        return not self.healing and not self.is_dashing and not self.grabbed_the_killer
    def ability3_extra_conditions(self):
        return (
            not self.healing and
            # hp too high, just dont do it.
            self.spaz.hitpoints < 1500 and
            not self.is_dashing and
            not self.grabbed_the_killer
        )

    def ability1(self):
        self.spaz.node.invincible = True
        self.spaz.allow_movement = False
        self.is_dashing = True
        self.create_dash_sfx()
        self.play_sound('dash_start')
        self.dash_timer = bs.Timer(0.1, self.dash, repeat=True)
        self.spaz.handlemessage(bs.CelebrateMessage(5.2))
        self.cancel_dash_timer = bs.Timer(5.2, self.cancel_dash)
        


   
    def cancel_dash(self):
        if self.die_upon_ungrab:
            self.spaz_lost_all_hp(type='die_upon_ungrab')
        self.die_warning_sfx.delete()
        self.is_dashing = False
        self.dash_timer = None
        self.spaz.allow_movement = True
        self.grabbed_the_killer = False
        self.dash_sfx.delete()
        self.cancel_dash_timer = None
        self.play_sound('dash_end')
        self.spaz.node.invincible = False
        self.hitting_timer = None
        
            
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
        target_speed = 20
  
        cur_vx, cur_vy, cur_vz = self.spaz.node.velocity
        current_speed_in_dir = (cur_vx * dir_x) + (cur_vy * dir_y) + (cur_vz * dir_z)
        speed_difference = target_speed - current_speed_in_dir

        impulse_scale = max(0.0, speed_difference / target_speed)

        self.spaz.impulse(
            x=2.5 * impulse_scale, 
            y=-2 * impulse_scale, 
            direction=(dir_x, dir_y, dir_z)
        )

    
        # and create le hitox

        # dont create if we grabbed the killer.
        if not self.grabbed_the_killer:
            DashHitbox(self.spaz.node.position, self).autoretain()
        else:
            # if we grabbed the killer, then knock em out.
            if self.spaz.node.hold_node:
                self.spaz.node.hold_node.handlemessage("knockout", 200)
    
  
    
    def dash_hit_spaz(self, spaz):
        if not self.is_dashing:
            return
        if not spaz:
            return
        
        if spaz.node.invincible:
            # na.
            return
        
        self.cancel_dash_timer = None
        self.play_sound('dash_hit')
        self.spaz.node.hold_node = spaz.node
        # grab em. and knock em out.
        self.grabbed_the_killer = True
        self.spaz.hitpoints = min(self.spaz.hitpoints-90, self.spaz.hitpoints_max)
        self.spaz.node.hurt = (
            1.0 - float(self.spaz.hitpoints) / self.spaz.hitpoints_max
        )
        # if were dead, then just mark us
        if self.spaz.hitpoints <= 0 and not self.die_upon_ungrab:
            self.spaz.hitpoints = 100
            self.die_upon_ungrab = True
            self.die_warning_sfx = bs.newnode('sound', attrs={
                    'sound': self.sfx.get('death_is_coming'), 'volume': 1,
            })
        self.stun_time = 1.5
        self.hits = 0
        self.max_hits = random.randint(7, 9)

        def slam():
            if not self.spaz.exists():
                return
            self.spaz.node.hold_node = None
            spaz.handlemessage(DamageMessage(
                damage=35, type='b9000_dash',
                )
            )
            v= (
                    self.spaz.node.move_left_right*2,
                    1,
                    -self.spaz.node.move_up_down*2
                )
            self.play_sound(random.choice(['dash_slam1', 'dash_slam2']))
            
            if not self.die_upon_ungrab:
            
                self.spaz.hitpoints = min(self.spaz.hitpoints-330, self.spaz.hitpoints_max)
                self.spaz.node.hurt = (
                    1.0 - float(self.spaz.hitpoints) / self.spaz.hitpoints_max
                )
            # if were dead, then just mark us
            if self.spaz.hitpoints <= 0:
                self.spaz.hitpoints = 100
                self.die_upon_ungrab = True
            

            # Marked... increase stun time
            if self.die_upon_ungrab:
                self.stun_time += 2.0
            
            # Reduce stuntime based on how many copies of B9000 is still alive.
            self.stun_time *= max(0.20, 1.0 - (0.2 * (self.stack - 1)))
            # stun
            spaz.handlemessage(
                StunMessage(
                    self.stun_time, spaz=self.spaz,
                    type='b9000_slam', knockback_settings={
                        'x': 35, 'y': 7, 'direction': v
                    }
                )
            )
            # finaly
            self.cancel_dash()

        def hit():
            if not self.die_upon_ungrab:
                self.spaz.hitpoints = min(self.spaz.hitpoints-27, self.spaz.hitpoints_max)
                self.spaz.node.hurt = (
                    1.0 - float(self.spaz.hitpoints) / self.spaz.hitpoints_max
                )
            # if were dead, then just mark us
            if self.spaz.hitpoints <= 0 and not self.die_upon_ungrab:
                self.spaz.hitpoints = 100
                self.die_upon_ungrab = True
                self.die_warning_sfx = bs.newnode('sound', attrs={
                    'sound': self.sfx.get('death_is_coming'), 'volume': 1,
                })
                # Also, reset our hits counter so we suffer more lol
                self.max_hits = 13
                self.hits = 0
           
            # if were marked for death, dont add stun time.
            if not self.die_upon_ungrab:
                self.stun_time += 0.28
                self.play_sound('dash_hurt')
                spaz.handlemessage(DamageMessage(
                    damage=5, type='b9000_dash',
                    )
                )
                
            self.hits += 1

            # Okay, if we him enough times, then slam em
            if self.hits >= self.max_hits:
                slam()
                return
        
        self.hitting_timer = None
        self.hitting_timer = bs.Timer(0.25, hit, repeat=True)

        

       
        

       
        

            
        
  
    def ability3(self):
        self.healing = True
        self.play_sound('heal_start')
        self.spaz.allow_movement = False
        self.spaz.hitpoints = min(self.spaz.hitpoints+70, self.spaz.hitpoints_max)
        self.spaz.node.hurt = (
            1.0 - float(self.spaz.hitpoints) / self.spaz.hitpoints_max
        )
        def end_heal():
            if self.healing:
                self.spaz.allow_movement = True
                self.play_sound('heal_end')
                self.healing = False
                bs.animate_array(
                    self.spaz.node, 'color', 3, {
                        0: (0, 0, 3),
                        1.0: self.spaz.color,
                    }
                )
        def heal():
            if self.healing and self.spaz and self.spaz.is_alive():
                # if our hp is over 150 end it
                if self.spaz.hitpoints >= 1500:
                    end_heal()
                    return
                
                self.play_sound('heal')
                self.spaz.hitpoints = min(self.spaz.hitpoints+70, self.spaz.hitpoints_max)
                self.spaz.node.hurt = (
                    1.0 - float(self.spaz.hitpoints) / self.spaz.hitpoints_max
                )
                bs.animate_array(
                    self.spaz.node, 'color', 3, {
                        0: (0, 3, 0),
                        0.2: self.spaz.color,
                    }
                )


                
        
        heal_cycles = 7
        for _ in range(heal_cycles):
            bs.timer(1.5*_, heal)
        bs.timer(1.5*heal_cycles, end_heal)
        
    
    def handle_recieved_damage(self, damage, type):
        # recursioutsn,
        if self.healing and not type == 'healing_damage':
            
            # take the damage again
            self.spaz.allow_movement = True
            self.spaz.handlemessage(DamageMessage(
                damage=damage, type='healing_damage',
            ))
            self.play_sound('heal_end')
            self.healing = False

            
           
        return True




    def ability2(self):
        pass
 
  

    
    
        