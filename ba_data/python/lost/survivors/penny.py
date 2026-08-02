from lost.lost import (
    CharacterMoveset, DamageMessage, AsymFactory,
     KillerDetectedMessage, StunMessage
)
import bascenev1 as bs
import babase

class BombCrystal(bs.Actor):
    def __init__(self,position):
        super().__init__()
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': (
                        position[0], position[1]+1, position[2]
                    ),
                    'velocity': (0,0,0),
                    'mesh': bs.getmesh('bomb'),
                    'body': 'sphere',
                    'body_scale': 1.0,
                    'mesh_scale': 0.95,
                    'shadow_size': 0.44,
                    'color_texture': bs.gettexture('flagColor'),
                    'reflection': 'powerup',
                    'reflection_scale': [-2.0],
                    'materials': [AsymFactory.get().destroy_on_wall_collide],
                },
            )
        self.expl_snd = bs.getsound('Crystal_Pitch_Explosion')
        
        self.active = True
        bs.timer(5, bs.Call(self.handlemessage, bs.DieMessage()))
        bs.timer(0.7, self.create_hitbox)

    def create_hitbox(self):
        if self.node:
            self.hitbox = bs.newnode(
                'region',
                delegate=self,
                attrs={
                    'scale': (1.35, 1.62, 1.65),
                    'type': 'sphere',
                    'materials': [AsymFactory.get().survivor_trap_object_material],
                },
            )
            self.node.connectattr('position', self.hitbox, 'position')
    
    def exists(self):
        return bool(self.node)

    def is_alive(self):
        return bool(self.node)

  

   

    def handlemessage(self, msg):
        if isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, KillerDetectedMessage):
            if not self.active:
                return
            if not self.is_alive():
                return
            node = bs.getcollision().opposingnode
            
            

            
            node.handlemessage(
                            DamageMessage(
                                damage=20,
                                spaz=None,
                                type='crystal_bomb',
                                hurt_sound=None,
                            )
                        )
            
            def revert():
                if not node:
                    return
                node.getdelegate(bs.Actor).resonance = min(
                    0, node.getdelegate(bs.Actor).resonance - 1
                )

               
            if not hasattr(node.getdelegate(bs.Actor), 'resonance'):
                node.getdelegate(bs.Actor).resonance = 0
            node.getdelegate(bs.Actor).resonance += 1
            bs.timer(82, revert)

            
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            if self.active and self.node:
                self.expl_snd.play()
                bs.emitfx(
                    position=self.node.position,
                    velocity=(0,0.25,0),
                    scale=0.5,
                    spread=0.1,
                )
                exl=bs.newnode(
                    'explosion',
                    attrs={
                        'position': self.node.position,
                        'color': (1, 0.5, 0.5),
                        'velocity': (0,0,0),
                        'radius': 0.8,
                        'big': False,
                    },
                )
                scorch = bs.newnode(
                    'scorch',
                    attrs={
                        'position': self.node.position,
                        'size': 0.2,
                        'big': True,
                    },
                )
            

                bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
                bs.timer(13.0, scorch.delete)
                bs.timer(1.0, exl.delete)
            self.active = False
            self.hitbox.delete()
            self.node.delete()
            
        return super().handlemessage(msg)
    
class PennySurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 60

    move_speed = 0.85
    run_speed =  0.9
    ability1_cooldown = 35
    ability2_cooldown = 0.0
    ability3_cooldown = 16

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = ''
    ability3_icon = babase.charstr(babase.SpecialChar.LOGO)

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'windup': bs.getsound('Hatchet_Swing'),
            #'punch_hit': bs.getsound(''),

        }
        self.factory = AsymFactory.get()
        self.shatter_hp_max = 35
        self.shatter_hp = 20
        self.shield = bs.newnode(
                'shield',
                owner=self.spaz.node,
                # pink
                attrs={'color': (2,  0.41, 0.71), 'radius': 0.75, 'hurt': 1.0 - (self.shatter_hp / self.shatter_hp_max)},
            )
        self.spaz.node.connectattr('position_center', self.shield, 'position')
        
        
        
        bs.timer(0.1, self._tick, repeat=True)
    
    def ability2(self):
        pass
    
    def _tick(self):
        if not self.spaz.is_alive():
            return
        self.shield.hurt = 1.0 - (self.shatter_hp / self.shatter_hp_max)
        if self.shatter_hp == 0:
            self.shield.radius = 0.0
        else:
            self.shield.radius = 0.75
        
    
    def handle_recieved_damage(self, damage, type):
        # we gave some shatter hp, deal that instead.
        if self.shatter_hp:
            # we have reduced 40%  damage from shatter hp
            damage *= 0.6
            if damage >= self.shatter_hp:
                self.shatter_hp = 0
            else:
                self.shatter_hp -= damage
            
            return False
        else:
            return True

    def ability1(self):
        self._punched_nodes = set()
        self.play_sound('windup')
        punch_dur = 0.25
       
        self.spaz.node.handlemessage('celebrate_l', punch_dur*1000)
      
        self.spaz.max_walk_speed *= 0.2
        self.spaz.max_run_speed *= 0.1
        def punch():
            self.spaz.max_walk_speed /= 0.2
            self.spaz.max_run_speed /= 0.1
            self.spaz.impulse(x=5, y=1)
            self.spaz.node.punch_pressed = True
            self.spaz.node.punch_pressed = False
            
        bs.timer(punch_dur, punch) 

    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode
        if not hasattr(node.getdelegate(bs.Actor), 'resonance'):
            node.getdelegate(bs.Actor).resonance = 0

        if node.getnodetype() != 'spaz':
            return False

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            self._punched_nodes.add(node)
            killer_resonance = int(getattr(
                node.getdelegate(bs.Actor), 'resonance', 0
            ))
            damage = 11 * (1+killer_resonance)
            node.handlemessage( 
                    DamageMessage(
                        damage=damage,  
                        spaz=self.spaz,
                        type='penny_punch',
                        hurt_sound=None,
                    )
            )
            
            if killer_resonance == 0:
                def revert():
                    if not node:
                        return
                    node.getdelegate(bs.Actor).max_walk_speed /= 0.5
                    node.getdelegate(bs.Actor).max_run_speed /= 0.2
                node.getdelegate(bs.Actor).max_walk_speed *= 0.5
                node.getdelegate(bs.Actor).max_run_speed *= 0.2
                bs.timer(1, revert)
                return
            elif killer_resonance > 0:
                if killer_resonance == 1:
                    stun_duration = 1.5
                    self.shatter_hp = min(
                        self.shatter_hp + 5, self.shatter_hp_max)
                elif killer_resonance == 2:
                    stun_duration = 2.5
                    self.shatter_hp = min(
                        self.shatter_hp + 15, self.shatter_hp_max)
                elif killer_resonance == 3:
                    stun_duration = 3.0
                    self.shatter_hp = min(
                        self.shatter_hp + 20, self.shatter_hp_max)
                else:
                    stun_duration = 4.5
                    self.shatter_hp = min(
                        self.shatter_hp + 30, self.shatter_hp_max)

            node.getdelegate(bs.Actor).resonance = min(
                0, node.getdelegate(bs.Actor).resonance - 1
            )
            node.handlemessage(StunMessage(duration=stun_duration, knockback_settings={
                    'x': 2,
                    'y': 1,
                    'direction': node.velocity
            }))

            
            self.play_sound('punch_hit', position=self.spaz.node.position)
            
        return False 
    
    def ability3(self):
        self.play_sound('bomb_windup')
       
        self.spaz.node.hold_node = BombCrystal(self.spaz.node.position).autoretain().node
      
        def throw():
            self.spaz.node.bomb_pressed = True
            self.spaz.node.bomb_pressed = False
        bs.timer(0.6, throw) 

