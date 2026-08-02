from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, StunMessage, SurvivorDetectedMessage
import bascenev1 as bs
import babase
import math, random
from bascenev1lib.actor.spaz import Spaz
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
                    'body_scale': 3,
                    'mesh_scale': 0.0,
                    'shadow_size': 0.44,
                    'materials': [AsymFactory.get().killer_trap_object_material],
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
        elif isinstance(msg, SurvivorDetectedMessage):
            if not self.moveset:
                return
            if not self.active:
                return
            if not self.is_alive():
                return
            self.active = False
            
            node = bs.getcollision().opposingnode
            # tell da owner we got em
            self.moveset.dash_hit_spaz(node.getdelegate(Spaz))
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            self.active = False
            self.node.delete()
        return super().handlemessage(msg)
    

class AliKiller(CharacterMoveset):
    is_killer = True
    chase_theme_dir = 'aliChase'
    hitpoints = 1111

    move_speed = 0.65
    run_speed =  1.0

    ability1_cooldown = 2.0
    ability2_cooldown = 32
    ability3_cooldown = 35

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = babase.charstr(babase.SpecialChar.FEDORA)
    ability3_icon = babase.charstr(babase.SpecialChar.FAST_FORWARD_BUTTON)

    def __init__(self, spaz):
        super().__init__(spaz)

        self.is_dashing = False
        
        self.sfx = {
            'swing': bs.getsound('Noli_stab'),
            'swing_hit': bs.getsound('Hitggg'),
            'dash_sfx': bs.getsound('NewVoidRush'),
            'dash_hit': bs.getsound('Noli_void_rush_first_dash'),
            'dash_hit2': bs.getsound('Noli_void_rush_second_dash'),
            'dash_kill': bs.getsound('Noli_void_rush_second_dash_hit_sfx'),
            'dash_cancel': bs.getsound('Cancel_rush')
        }
        self.hit_spazes = set()
        self.factory = AsymFactory.get()
        self.dash_timer = None
        self.awaiting_dash_input = False
        self.combo = 0
        self.dash_sfx = bs.Node(None)
        self.cancel_dash_timer = None
        # kowl dwon
        self._last_used_3 = bs.time() - 25
        self.clone: Spaz = None
        self.kill_clone_timer = None
        bs.timer(0.001, self.handle_clone, repeat=True)
        self.is_clone = False
    

    def create_dash_sfx(self):
        self.dash_sfx = bs.newnode('sound', attrs={
            'sound': self.sfx.get('dash_sfx'), 'volume': 5,
        })
    

  
    def ability1(self) -> None:
        self._punched_nodes = set()
        
        self.spaz.node.punch_pressed = True
        try: bs.timer(0.6, bs.Call(self.spaz.safesetattr, self.spaz.node, 'punch_pressed', False))
        except: pass
        self.play_sound('swing')

    def ability1_extra_conditions(self) -> bool:
        return not self.is_dashing
    def ability2_extra_conditions(self) -> bool:
        return not self.is_dashing

    def cancel_dash(self):
        self._last_used_3 = bs.time()
        self.is_dashing = False
        self.dash_timer = None
        self.spaz.allow_movement = True
        self.awaiting_dash_input = False
        self.combo = 0
        self.hit_spazes = set()
        self.dash_sfx.delete()
        self.cancel_dash_timer = None
        self.play_sound('dash_cancel')
    
    
    def dash(self):
        if not self.spaz.exists():
            self.dash_sfx.delete()
            return
        if not self.is_dashing:
            self.cancel_dash()
            return
        if self.awaiting_dash_input:
            # Waiting for dash...
            self.dash_sfx.delete()
            return
        # make sure its false
        self.spaz.allow_movement = False
        
        
        dir_x = self.spaz.input_x #* 0.15
        dir_y = -1.0
        dir_z = -self.spaz.input_y #* 0.15
        target_speed = 16.0 
  
        cur_vx, cur_vy, cur_vz = self.spaz.node.velocity
        current_speed_in_dir = (cur_vx * dir_x) + (cur_vy * dir_y) + (cur_vz * dir_z)
        speed_difference = target_speed - current_speed_in_dir

        impulse_scale = max(0.0, speed_difference / target_speed)

        self.spaz.impulse(
            x=4.5 * impulse_scale, 
            y=-1.5 * impulse_scale, 
            direction=(dir_x, dir_y, dir_z)
        )

    
        # and create le hitox
        DashHitbox(self.spaz.node.position, self).autoretain()
    



    def start_dashing(self):
        self.hit_spazes = set()
        self.spaz.allow_movement = False
        if self.can_spaz_can_do_stuff():
            self.create_dash_sfx()
            self.dash_timer = bs.Timer(0.1, self.dash, repeat=True)
            # Cancel if we take too long
            self.cancel_dash_timer = None
            self.cancel_dash_timer = bs.Timer(4, self.cancel_dash)


        else:
            # somethin' happened, cancel.
            self.cancel_dash()
    
    def dash_hit_spaz(self, spaz):
        if not self.is_dashing:
            return
        if not spaz:
            return
        self.play_sound(
            random.choice(['dash_hit', 'dash_hit2'])
        )
        
        if spaz in self.hit_spazes:
            # kill em
            self.dash_hit_spaz_again(spaz)
        else:
            # otherwise just do 10 damage and add to our combo
            self.combo += 1
            spaz.handlemessage(
                DamageMessage(
                    damage=1 if self.is_clone else 10, spaz=self.spaz,
                    visual_damage=10 if self.is_clone else None,
                    type='ali_rush'
                )
            )
            
            # and stop.
            self.awaiting_dash_input = True
            # put on cool down so our guys can hav etime to react
            self._last_used_3 = bs.time() - 34
            self.spaz.impulse(x=-2)
            self.hit_spazes.add(spaz)

            # Cancel if we take too long
            self.cancel_dash_timer = None
            self.cancel_dash_timer = bs.Timer(3.5, self.cancel_dash)

            
    
    def dash_hit_spaz_again(self, spaz):
        if not self.is_dashing:
            return
        combo = self.combo
        # Cancel the dash entirely.
        self.cancel_dash()

        # and do a sick anmation
        self.play_sound('dash_kill')
        # grab bro
        self.spaz.node.hold_node = spaz.node
        # knock em out so they cant do any sneaky blocks
        spaz.node.handlemessage('knockout', 5*(1000))
        def drop():
            dmg = 30 + (3.5 * combo)
            spaz.handlemessage(DamageMessage(
                damage=dmg*0.1 if self.is_clone else dmg, spaz=self.spaz, type='ali_slam',
                visual_damage=dmg if self.is_clone else None
            ))
            self.spaz.node.hold_node = None
            spaz.handlemessage(StunMessage(2, spaz=self.spaz, type='ali_slam', knockback_settings={
                'x': 0,
                'y': -7,
                'direction': (0, -5, 0)
            }, use_node_knockout_message=True))
            # slow us for a bit.
            self.spaz.max_walk_speed *= 0.2
            self.spaz.max_run_speed *= 0.1
            def revert():
                self.spaz.max_walk_speed /= 0.2
                self.spaz.max_run_speed /= 0.1
            bs.timer(3.5, revert)
            
        bs.timer(0.35, drop)



    
    def handle_spaz_was_stunned(self, type):
        # if were stunned while awaiting input, cancel entirely.
        if self.awaiting_dash_input:
            self.cancel_dash()

    def ability3(self) -> None:

        # We are awaiting input, start again.
        if self.awaiting_dash_input:
            self.awaiting_dash_input = False
            self.spaz.allow_movement = True
            self._last_used_3 = bs.time() - 34
            self.create_dash_sfx()
            self.dash_timer = bs.Timer(0.1, self.dash, repeat=True)
            self.cancel_dash_timer = None
            self.cancel_dash_timer = bs.Timer(4.0, self.cancel_dash)
            
            return

        # If were dashing, cancel.
        if self.is_dashing:
            self.cancel_dash()
            
            return

    
        
        # Otherwise, initialize it
        self._last_used_3 = bs.time() - 34
        self.is_dashing = True
        bs.timer(0.5, self.start_dashing)
  
    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=3 if self.is_clone else 23,
                    spaz=self.spaz,
                    type='ali_punch',
                    hurt_sound=None,
                    visual_damage=23 if self.is_clone else None
                    # hehe cloner
                    
                )
            )
            self._punched_nodes.add(node)
            self.play_sound('swing_hit')

        return False
    
    def handle_clone(self):
        if not self.clone:
            return
        if not self.clone.is_alive():
            return
        
        
        if self.spaz.is_alive():
            clone_pos = self.clone.node.position
            target_spaz = None
            min_dist = float('inf')

            activity = bs.getactivity()
            
            for player in activity.survivors:
                if not player.actor.is_alive():
                    continue
                spaz = player.actor
                if not spaz or not spaz.is_alive():
                    continue
                s_pos = spaz.node.position
                dist = math.hypot(s_pos[0] - clone_pos[0], s_pos[2] - clone_pos[2])

                if dist < min_dist:
                    min_dist = dist
                    target_spaz = spaz

            if target_spaz:
                target_pos = target_spaz.node.position
            elif self.spaz.is_alive():
                target_pos = self.spaz.node.position
            else:
                return

            dx = target_pos[0] - clone_pos[0]
            dz = target_pos[2] - clone_pos[2]
            dist = math.hypot(dx, dz)

            move_x = dx / dist
            move_z = dz / dist
            self.clone.on_run(0.8)
            # move just ever so slower
            slownes = 0.9
            self.clone.on_move_left_right(move_x*slownes)
            self.clone.on_move_up_down(-move_z*slownes)
            
      

            if target_spaz and dist < 1.0:
                self.clone.on_run(0.15)
                self.clone.on_punch_press()
                self.clone.on_punch_release()
            
            if target_spaz and dist < 1.7 or self.clone.moveset.awaiting_dash_input:
                self.clone.on_bomb_press()
                self.clone.on_bomb_release()


                
       
    
    def kill_clone(self):
        if self.clone:
            position = self.clone.node.position
            velocity = (0, 1, 0)
            self.clone.handlemessage(bs.DieMessage(immediate=True))
            self.clone = None
            self.kill_clone_timer = None
            bs.emitfx(
                    position=position,
                    velocity=(0,0.25,0),
                    scale=0.5,
                    spread=0.1,
                )
             
            scorch = bs.newnode(
                    'scorch',
                    attrs={
                        'position': position,
                        'size': 2,
                        'big': True,
                    },
            )
            bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
            bs.timer(13.0, scorch.delete)
            bs.emitfx(
                position=position,
                velocity=velocity,
                count=int(1.0 + random.random() * 4),
                emit_type='tendrils',
                tendril_type='thin_smoke',
            )
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
                spread=1.0,
            )

    
    def ability2(self):
        self.kill_clone()

        self.clone = Spaz(
            color=self.spaz.color,
            highlight=self.spaz.highlight,
            character=self.spaz.character,
            source_player=None, start_invincible=False,
            is_killer=True
        )
        hurt = self.spaz.node.hurt
        self.clone.node.hurt = 0.1
        self.clone.node.hurt = hurt
        self.spaz.node.hurt = 0.1
        self.spaz.node.hurt = hurt
        self.clone.hitpoints = self.spaz.hitpoints
        self.clone.hitpoints_max = self.spaz.hitpoints_max
        self.clone.node.is_area_of_interest = self.spaz.node.is_area_of_interest
        self.clone.node.name = self.spaz.node.name
        self.clone.node.name_color = self.spaz.node.name_color
        self.clone.moveset._last_used_1 = self._last_used_1
        self.clone.moveset._last_used_2 = bs.time()
        self.clone.moveset._last_used_3 = self._last_used_3
        self.clone.handlemessage(bs.StandMessage(
            (
                self.spaz.node.position[0],
                self.spaz.node.position[1]-1.1,
                self.spaz.node.position[2],
            )
        ))
        # tell em we clone so we do less damage
        self.clone.moveset.is_clone = True
        self.kill_clone_timer = bs.Timer(17, self.kill_clone)
    
        


        
 
   
        