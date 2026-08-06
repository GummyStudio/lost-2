from lost.factory import (
    AsymFactory,
    DamageMessage,
    StunMessage,
    SurvivorDetectedMessage,
)
from lost.character_moveset import CharacterMoveset
import bascenev1 as bs
import babase

class LandMine(bs.Actor):
    def __init__(self, position, velocity):
        super().__init__()
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': velocity,
                    'mesh': bs.getmesh('landMine'),
                    'body': 'landMine',
                    'body_scale': 0.776,
                    'shadow_size': 0.44,
                    'color_texture': bs.gettexture('shrapnel1Color'),
                    'reflection': 'powerup',
                    'reflection_scale': [1.0],
                    'materials': [AsymFactory.get().killer_trap_object_material],
                },
            )
        self.impulse(x=1, y=0.5)
        self.active = False
        self.position = position
        bs.timer(0.2, self.activate)
        bs.timer(1, bs.Call(self.handlemessage, bs.DieMessage()))
    
    def exists(self):
        return bool(self.node)

    def is_alive(self):
        return self.active

    def activate(self):
        self.active = True
        

   

    def handlemessage(self, msg):
        if isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, SurvivorDetectedMessage):
            if not self.is_alive():
                return
            node = bs.getcollision().opposingnode
            
            node.getdelegate(bs.Actor).impulse(x=0.8, y=1)
            bs.getsound('explosion02').play()
            node.handlemessage(
                            DamageMessage(
                                damage=10,
                                spaz=None,
                                type='ninja_mine',
                                hurt_sound=None,
                            )
                        )
            node.handlemessage(
                            StunMessage(
                                duration=1,
                                spaz=None,
                                type='ninja_mine',
                                knockback_settings={
                                    'x': 3,
                                    'y': 5,
                                    'direction': (0, 1, 0)
                                },
                                use_node_knockout_message=True
                            )
                        )
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            self.active = False
            self.node.delete()
        return super().handlemessage(msg)


class NinjaKiller(CharacterMoveset):
    is_killer = True
    chase_theme_dir = 'ninjaChasetheme'
    hitpoints = 450
    
    description = (
        "Snake Shadow is a killer that both hits and goes pretty fast, "
        "but doesn't do as much damage. However, get him angry.. and he'll hit HARD."
    )
    ability1_description = "Punches forward to deal small damage, or BIG damage if he's enraged."
    ability2_description = "Throws a mine that shortly disappears but stuns if it hits."
    ability3_description = "Initiates rage mode, which increases overall speed and punch cooldown."

    move_speed = 0.8
    run_speed =  1.0

    ability1_cooldown = 1
    ability2_cooldown = 8
    ability3_cooldown = 44

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = babase.charstr(babase.SpecialChar.FIREBALL)
    ability3_icon = babase.charstr(babase.SpecialChar.OUYA_BUTTON_A)
    
    

    def __init__(self, spaz):
        super().__init__(spaz)

        self.is_dashing = False
        self.trap = None

        self.sfx = {
            'swing': bs.getsound('punchSwish'),
            'punch_hit': bs.getsound('punchStrong02'),
            'fire_punch_hit': bs.getsound('punchStrong01'),
            'roar': bs.getsound('Hes_not_happy'),

        }
        self.factory = AsymFactory.get()
        self.spaz.node.boxing_gloves = True
        self._last_used_3 = -20
        self.transforming = False
        self.throwing_mine = False

        self.fire_mode = False
        self.light = bs.Node(None)
        bs.timer(0.1, self.fire_particals, repeat=True)

  
    def ability1(self) -> None:
        self.play_sound('swing')
        self._punched_nodes = set()
        self.spaz.node.punch_pressed = True
        try: bs.timer(0.6, bs.Call(self.spaz.safesetattr, self.spaz.node, 'punch_pressed', False))
        except: pass
        if self.fire_mode:
            self._last_used_1 = bs.time() + 3

    def ability2(self) -> None:
        self.throwing_mine = True
        self.spaz.handlemessage(bs.CelebrateMessage(0.13))
        def throw():
            self.spaz.node.punch_pressed = True
            self.spaz.node.punch_pressed = False
            try: bs.timer(0.6, bs.Call(setattr, self, 'throwing_mine', False))
            except: pass
            LandMine(self.spaz.node.position, self.spaz.node.velocity)
        bs.timer(0.13, throw)

        
    # dont wanna do other abilities if transforming
    def ability1_extra_conditions(self):
        return not self.transforming and not self.throwing_mine 
    def ability2_extra_conditions(self):
        return not self.transforming
    def ability3_extra_conditions(self):
        return not self.throwing_mine and not self.transforming
    
    def fire_particals(self):
        if not self.spaz:
            return
        if not self.fire_mode:
            return
        bs.emitfx(
                    position=self.spaz.node.position,
                    chunk_type='sweat',
                    velocity=(
                        0,
                        5,
                        0,
                    ),
                    count=min(30, 1 + int(800 * 0.04)),
                    scale=0.9,
                    spread=0.28,
                )


    def enter_fire_mode(self):
        if self.spaz.exists():
                self.spaz.max_walk_speed /= 0.01
                self.spaz.node.invincible = False
                self.spaz.set_invincible(5)
                self.spaz.speed_boost(10)
                self.fire_mode = True
                self.play_sound('roar')
                self.spaz.node.color = (4.2, 0, 0)
                self.spaz.node.highlight = (0.254, 0, 0)
                self.transforming = False
                self.light = bs.newnode(
                    'light',
                    owner=self.spaz.node,
                    attrs={
                        'volume_intensity_scale': 4.0,
                        'color': (1,0,0),
                    },
                ) 
                self.spaz.node.connectattr('position', self.light, 'position')
            
    
    def leave_fire_mode(self):
        if self.spaz.exists():
            self.light.delete()
            self.fire_mode = False
            self.spaz.node.color = bs.app.classic.spaz_appearances['Snake Shadow'].default_color
            self.spaz.node.highlight = bs.app.classic.spaz_appearances['Snake Shadow'].default_highlight


    def ability3(self) -> None:
        self.transforming = True
        self.ability3_cooldown += 5
        self.spaz.max_walk_speed *= 0.01
        self.spaz.node.invincible = True
        self.spaz.handlemessage(bs.CelebrateMessage(2.0))
            
        bs.timer(2, self.enter_fire_mode)
        bs.timer(2+10, self.leave_fire_mode)
                

        
      

    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        # throwing mine, punch animation does nothin'
        if self.throwing_mine:
            return
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=30 if self.fire_mode else 15,
                    spaz=self.spaz,
                    type='ninja_fire_punch' if self.fire_mode else 'ninja_punch',
                    hurt_sound=None,
                    
                )
            )
            self.play_sound('fire_punch_hit' if self.fire_mode else 'punch_hit', position=self.spaz.node.position)
            self._punched_nodes.add(node)
            if self.fire_mode:
                node.getdelegate(bs.Actor).impulse(x=0.8, y=1)


        return False

    def handle_spaz_was_stunned(self, type):
        # Always ragdoll
        self.spaz.node.handlemessage('knockout', 20)
    
    def handle_recieved_damage(self, damage, type):
        # fire mode no damage
        return not self.fire_mode