from typing import override
import math
from lost.lost import (
    CharacterMoveset, 
    DamageMessage, 
    AsymFactory, 
)
import bascenev1 as bs
import babase, random

class PC(bs.Actor):
    
    def __init__(self, position: list[float]):
        super().__init__()
        self.position = position
        self.explode_sfx = bs.getsound('Collide')
        self.percent = 25.0
      
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': bs.getmesh('puck'),
                'color_texture': bs.gettexture('powerupCurse'),
                'mesh_scale': 0.5,
                'body': 'puck',
                'body_scale': 0.5,
                'position': position,
                'velocity': (0, 0, 0),
                'gravity_scale': 0.0,
                'materials': [
                    AsymFactory.get().no_collision,
                    # Give killer material so it can be placed in killer walls.
                    AsymFactory.get().killer_material
                ],
                'shadow_size': 0.5,
            },
        )
        
        self.text_node: bs.Node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': '25%',
                'in_world': True,
                'scale': 0.015,
                'color': (0.86, 0.86, 1.0),
                'h_align': 'center',
            }
        )
        self.node.connectattr('position', self.text_node, 'position')
        

        self.active = True
        bs.timer(1.6, bs.Call(self.add_percent, -1), repeat=True)

    def add_percent(self, amount: int = 2):
        if not self.exists():
            return
        self.percent = float(max(0, min(
            self.percent + amount, 100
        )))

        if int(self.percent) == 0:
            # expld
            self.handlemessage(bs.DieMessage())
   
        if self.text_node:
            self.text_node.text = f"{int(self.percent)}%"

    def can_teleport(self) -> bool:
        return self.active and (
            int(self.percent) > 74
        )

    def exists(self):
        return bool(self.node)
    
    def is_alive(self):
        return bool(self.node)
         
    @override
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self.exists() and not msg.immediate:
                self.explode_sfx.play()
                bs.emitfx(
                    position=self.position,
                    velocity=(0,0.25,0),
                    scale=0.5,
                    spread=0.1,
                )
                exl=bs.newnode(
                    'explosion',
                    attrs={
                        'position': self.position,
                        'velocity': (0,0,0),
                        'radius': 2,
                        'big': True,
                    },
                )
                scorch = bs.newnode(
                    'scorch',
                    attrs={
                        'position': self.position,
                        'size': 0.5,
                        'big': False,
                    },
                )
            

                bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
                bs.timer(13.0, scorch.delete)
                bs.timer(1.0, exl.delete)
            self.active = False
            self.text_node.delete()
            self.node.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else: 
            return super().handlemessage(msg)


class BonesKiller(CharacterMoveset):
    """bad war."""
    is_killer = True
    chase_theme_dir = 'BadwareTheme'
    hitpoints = 1000

    move_speed = 0.85
    run_speed = 1.0

    ability1_cooldown = 1
    ability2_cooldown = 20
    ability3_cooldown = 18

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = babase.charstr(babase.SpecialChar.STEAM_LOGO)
    ability3_icon = babase.charstr(babase.SpecialChar.DELETE) 
    
    def __init__(self, spaz):
        super().__init__(spaz)
       
        self.sfx = {
            'swing': bs.getsound('BadwareSwing'),
            'swing_hit': bs.getsound('BadwareSwingHit'),
            'place_windup': bs.getsound('My_wife_is_speaking'),
            'stunned': bs.getsound('BadwareStunned'),
            'rift': bs.getsound('BadwareRift'),
            
        }
        self.placing = False
        self.buffed = False
        self.pcs: list[PC] = []
    
    def ability1(self) -> None:
        self._punched_nodes = set()
        
        self.spaz.node.punch_pressed = True
        try: bs.timer(0.6, bs.Call(setattr, self.spaz.node, 'punch_pressed', False))
        except: pass
        self.play_sound('swing', position=self.spaz.node.position)

    def ability1_extra_conditions(self) -> bool:
        return not self.placing

    def ability2_extra_conditions(self) -> bool:
        return not self.placing
    
    def ability3_extra_conditions(self):
        return not self.placing and any(pc.can_teleport() for pc in self.pcs if pc.is_alive())

    def ability2(self) -> None:
        self.placing = True
        self.spaz.node.handlemessage('celebrate_l', 1.2*(1000))
        self.play_sound('place_windup', position=self.spaz.node.position)
        self.spaz.max_walk_speed *= 0.1
        self.spaz.max_run_speed *= 0.1

        def place():
            self.spaz.max_walk_speed /= 0.1
            self.spaz.max_run_speed /= 0.1
            if self.can_spaz_can_do_stuff():
                # Filter out dead PCs
                self.pcs = [pc for pc in self.pcs if pc.is_alive()]
                
                # Enforce max limit of 5 by deleting the oldest PC
                if len(self.pcs) >= 5:
                    oldest_pc = self.pcs.pop(0)
                    oldest_pc.handlemessage(bs.DieMessage(immediate=True))
                
                new_pc = PC(self.spaz.node.position).autoretain()
                self.pcs.append(new_pc)

            self.placing = False

        bs.timer(1.2, place)

    def ability3(self) -> None:
        if not self.spaz.node.exists():
            return
        

        # Clean up dead PCs
        self.pcs = [pc for pc in self.pcs if pc.is_alive()]
        
        # Filter PCs that are at 100% percent
        valid_pcs = [pc for pc in self.pcs if pc.can_teleport()]
        if not valid_pcs:
            return

        char_pos = self.spaz.node.position

        # Find the furthest PC at 100%
        def get_dist(pc: PC):
            p = pc.node.position
            return math.dist(char_pos, p)

        target_pc = max(valid_pcs, key=get_dist)

        target_light = bs.newnode(
            'light',
            owner=target_pc.node,
            attrs={
                'position': target_pc.node.position,
                'color': (3.0, 0.2, 0.2),
                'radius': 0.4,
                'volume_intensity_scale': 2.0
            }
        )

        bg = bs.newnode(
                'image',
                delegate=self,
                attrs={
                    'fill_screen': True,
                    'texture': bs.gettexture('white'),
                    'color': (1, 1, 1, 0.5),
                },
        )
        text = bs.newnode(
                'text',
                delegate=self,
                attrs={
                    'text': random.choice([
                        "Your PC Have been hacked :)"
                    ]
                    ),
                    'color': (1, 1, 1),
                    'in_world': False,
                    'position': (0, 0),
                },
        )
        self.placing = True
        self.spaz.handlemessage(bs.CelebrateMessage(3))
        self.spaz.max_walk_speed *= 0.1
        self.spaz.max_run_speed *= 0.1
        def do_teleport():
            # Reset our stats.
            self.placing = False
            self.spaz.max_walk_speed /= 0.1
            self.spaz.max_run_speed /= 0.1
            target_light.delete()
            bg.delete()
            text.delete()

            # and if everything goes well, teleport
            if target_pc.is_alive() and self.can_spaz_can_do_stuff():
                dest_pos = (
                    target_pc.position[0],
                    target_pc.position[1]-1,
                    target_pc.position[2],
                )
                
                # Teleport and buff
                self.spaz.handlemessage(bs.StandMessage(dest_pos))
                self.spaz.set_invincible(2.0)
                self.spaz.speed_boost(6)
                self.buffed = True
                bs.timer(6, bs.Call(setattr, self, 'buffed', False))
                


                if target_pc in self.pcs:
                    self.pcs.remove(target_pc)
                target_pc.handlemessage(bs.DieMessage())

            

        bs.timer(3.0, do_teleport)

    def handle_spaz_was_stunned(self, type):
        super().handle_spaz_was_stunned(type)
        self.play_sound('stunned')
        # Remove percent from our pcs
        for pc in self.pcs:
            pc.add_percent(-31)


    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=int(13*(2.8 if self.buffed else 1)),
                    spaz=self.spaz,
                    type='bones_punch',
                    hurt_sound=None,
                )
            )
            self.play_sound('swing_hit', position=self.spaz.node.position)
            self._punched_nodes.add(node)
            # Add percent to our pcs
            for pc in self.pcs:
                pc.add_percent(24.5)


        return False