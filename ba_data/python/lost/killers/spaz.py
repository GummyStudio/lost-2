from lost.factory import (
    AsymFactory,
    DamageMessage,
    StunMessage,
    SurvivorDetectedMessage,
)
from lost.character_moveset import CharacterMoveset
import bascenev1 as bs
import babase
import math

class LandMineTrap(bs.Actor):
    def __init__(self, position):
        super().__init__()
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': (0,0,0),
                    'mesh': bs.getmesh('landMine'),
                    'body': 'landMine',
                    'body_scale': 1.0,
                    'shadow_size': 0.44,
                    'color_texture': bs.gettexture('spectureBG'),
                    'reflection': 'powerup',
                    'reflection_scale': [1.0],
                    'materials': [AsymFactory.get().killer_trap_object_material],
                },
            )
        self.active = False
        self.position = position
        bs.timer(0.5, self.activate)
    
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
            node.handlemessage(
                            DamageMessage(
                                damage=10,
                                spaz=None,
                                type='spaz_slam',
                                hurt_sound=None,
                            )
                        )
            node.handlemessage(
                            StunMessage(
                                duration=1,
                                spaz=None,
                                type='spaz_slam',
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

class SpazKiller(CharacterMoveset):
    is_killer = True
    chase_theme_dir = 'spazChasetheme'
    low_theme_dir = 'spazLowHPtheme'
    hitpoints = 1500

    move_speed = 0.8
    run_speed =  1.0

    ability1_cooldown = 2.0
    ability2_cooldown = 5.0
    ability3_cooldown = 23

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = babase.charstr(babase.SpecialChar.TOP_BUTTON)
    ability3_icon = babase.charstr(babase.SpecialChar.DPAD_CENTER_BUTTON)
    
    description = (
        "Spaz is a very easy to play with killer, with his simple moveset.\n" 
        "Despite his simplicity, he is still able to kill survivors efficiently.\n\n"
        "{'type': 'edit_text', 'color': (1, 0.9, 0.9)}"
        "After being split apart from his companions in the world of Lost, "
        "Spaz had turned into one of the many people who had been corrupted, "
        "and now chase people till' their death..."
    )
    
    ability1_description = "Punches a survivor to deal small damage to them."
    ability2_description = "Dashes forward."
    ability3_description = "Spawn a land-mine trap that stuns survivors that touch it."
    

    def __init__(self, spaz):
        super().__init__(spaz)

        self.is_dashing = False
        self.trap = None

        self.sfx = {
            'punch': bs.getsound('Cool-swing'),
            'punch_hit': bs.getsound('Cool-hit'),
            'dash': bs.getsound('swish'),
            'slam': bs.getsound('explosion01'),
        }
        self.factory = AsymFactory.get()

  
    def ability1(self) -> None:
        self._punched_nodes = set()
        
        self.spaz.node.punch_pressed = True
        try: bs.timer(0.6, bs.Call(self.spaz.safesetattr, self.spaz.node, 'punch_pressed', False))
        except: pass
        self.play_sound('punch', position=self.spaz.node.position)


    def ability2_extra_conditions(self) -> bool:
        # no dash if dashing
        return not self.is_dashing

    def ability2(self) -> None:
       
        self.is_dashing = True
        self.play_sound('dash', position=self.spaz.node.position)

        self.spaz.impulse(
            x=5, y=1.3
        )

        bs.emitfx(
            position=self.spaz.node.position,
            velocity=(0, 0, 0),
            count=15,
            scale=1.2,
            spread=0.4,
            chunk_type='spark',
        )

        bs.timer(0.4, bs.Call(setattr, self, 'is_dashing', False))



    def ability3(self) -> None:
      

        pos = self.spaz.node.position
        self.play_sound('slam', position=pos)

        bs.emitfx(
            position=pos,
            velocity=(0, 0, 0),
            count=30,
            scale=2.0,
            spread=1.0,
            chunk_type='slime',
        )

        if self.trap:
            self.trap.handlemessage(bs.DieMessage(True))

        self.trap = LandMineTrap(self.spaz.node.position).autoretain()
                      
  
    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=20,
                    spaz=self.spaz,
                    type='spaz_punch',
                    hurt_sound=None,
                    
                )
            )
            self.play_sound('punch_hit', position=self.spaz.node.position)
            self._punched_nodes.add(node)

        return False