from typing import override, Any
from lost.lost import (
    CharacterMoveset, 
    DamageMessage, 
    AsymFactory, 
    SurvivorDetectedMessage,
    SurvivorUnDetectedMessage
)
from bascenev1lib.gameutils import SharedObjects
import bascenev1 as bs
import random, math, babase

class MusicBox(bs.Actor):
    
    def __init__(self, position: list[float]):
        super().__init__()
        self.position = position
      
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'crate',
                'body_scale': 4,
                'position': position,
                'velocity': (0, 0, 0),
                'gravity_scale': 0.0,
                'materials': [
                    AsymFactory.get().killer_trap_object_material,
                    AsymFactory.get().no_wall_collide
                ],
                'shadow_size': 0,
            },
        )
        
        self.item_node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': bs.getmesh('box'),
                'color_texture': bs.gettexture('white'),
                'mesh_scale': 0.35,
                'gravity_scale': 0.0,
                'body': 'box',
                'position': position,
                'shadow_size': 1.0,
                'materials': [
                    AsymFactory.get().no_collision
                ],
            },
        )
        self.tick_timer = bs.Timer(0.01, bs.Call(self._tick), repeat=True)
        self.item_node.velocity = (0, 0, 0) 
        self._rotate()
        self.active = True
        bs.timer(37, bs.Call(self.handlemessage, bs.DieMessage()))
    
    def _rotate(self):
        if not self.node.exists() or not self.item_node.exists():
            return

        dir_x = 0.2
        dir_z = 0
        pos = self.item_node.position
        force = 20
        self.item_node.handlemessage(
            'impulse',
            pos[0],
            pos[1],
            pos[2]+0.2,
            0, 0, 0,
            force,
            force,
            0,
            0,
            dir_x,
            0,
            dir_z,
        )
        bs.timer(0.1, bs.Call(self.do_rotate))
    
    def do_rotate(self):
        if not self.node.exists() or not self.item_node.exists():
            return
        self.item_node.velocity = (0, 0, 0) 
        bs.timer(2, bs.Call(self._rotate))

    def _tick(self):
        if not self.node.exists():
            return
        
        self.node.position = self.position
        self.item_node.position = (
                self.node.position[0],
                self.node.position[1]+0.5,
                self.node.position[2],
            )
    
        
         
        
    @override
    def handlemessage(self, msg):
        if isinstance(msg, SurvivorDetectedMessage):
            if not self.active:
                return
            col = bs.getcollision()
            node = col.opposingnode 

            if node.getnodetype() != 'spaz':
                return

            if node.getdelegate(bs.Actor):
                node.getdelegate(bs.Actor).max_walk_speed *= 0.85
                node.getdelegate(bs.Actor).max_run_speed *= 0.75


        elif isinstance(msg, SurvivorUnDetectedMessage):
            if not self.active:
                return
            col = bs.getcollision()
            node = col.opposingnode 

            if node.getnodetype() != 'spaz':
                return

            if node.getdelegate(bs.Actor):
                node.getdelegate(bs.Actor).max_walk_speed /= 0.85
                node.getdelegate(bs.Actor).max_run_speed /= 0.75
        
        


        elif isinstance(msg, bs.DieMessage):
            self.active = False
            
            if not self.node.exists() or not self.item_node.exists():
                self.node.delete()
                self.item_node.delete()
                return
            if msg.immediate:
                self.node.delete()
                self.item_node.delete()
            else:
                bs.animate(
                    self.item_node, 'mesh_scale', {0: 
                                                   self.item_node.mesh_scale, 
                                                   0.2: 0.0}
                )
                bs.timer(0.2, bs.Call(self.node.delete))
                bs.timer(0.2, bs.Call(self.item_node.delete))
                

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else: 
            return super().handlemessage(msg)

class KillerWall(bs.Actor):
    
    def __init__(self, position: list[float]):
        super().__init__()
        self.position = position
      
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': bs.getmesh('box'),
                'color_texture': bs.gettexture('achievementWall'),
                'body': 'crate',
                'body_scale': 1.5,
                'position': position,
                'velocity': (0, 0.1, 0),
                'gravity_scale': 2.0,
                'materials': [
                    AsymFactory.get().killer_door_material,
                ],
                'shadow_size': 0.3,
            },
        )
        
        bs.timer(65, bs.Call(self.handlemessage, bs.DieMessage()))
        self.tick_timer = bs.Timer(0.01, bs.Call(self._tick), repeat=True)
    def _tick(self):
            if not self.node.exists():
                return
            
            self.node.position = self.position
          
            
    
        
    @override
    def handlemessage(self, msg):

        if isinstance(msg, bs.DieMessage):
           self.node.delete()
           self.tick_timer = None
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else: 
            return super().handlemessage(msg)
        

class WizardKiller(CharacterMoveset):
    """im so artful ."""
    is_killer = True
    chase_theme_dir = 'MasterpieceofTheRichesV2'
    hitpoints = 250

    move_speed = 0.75
    run_speed = 1.0

    ability1_cooldown = 1.65
    ability2_cooldown = 20
    ability3_cooldown = 18

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = babase.charstr(babase.SpecialChar.OCULUS_LOGO)
    ability3_icon = babase.charstr(babase.SpecialChar.EYE_BALL)
    
    def __init__(self, spaz):
        super().__init__(spaz)
       
        self.sfx = {
            'swing': bs.getsound('ArtfulSwing'),
            'swing_hit': bs.getsound('ArtfulSwingHit'),
            'place_windup': bs.getsound('ArtfulPlaceWindup'),
            'place_object': bs.getsound('ArtfulPlaceCopywrite'),
           
        }
        self.placing = False
    
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
        return not self.placing


    def ability2(self) -> None:
        self.placing = True
        self.spaz.node.handlemessage('celebrate_l', 2*(1000))
        self.play_sound('place_windup', position=self.spaz.node.position)
        self.spaz.max_walk_speed *= 0.1
        self.spaz.max_run_speed *= 0.1
        def place():
            self.spaz.max_walk_speed /= 0.1
            self.spaz.max_run_speed /= 0.1
            if self.can_spaz_can_do_stuff():
                self.play_sound('place_object', position=self.spaz.node.position)
                KillerWall(self.spaz.node.position).autoretain()
            self.placing = False
        bs.timer(2, place)

       
        


    def ability3(self) -> None:
        self.placing = True
        self.spaz.node.handlemessage('celebrate_r', 2*(1000))
        self.play_sound('place_windup', position=self.spaz.node.position)
        self.spaz.max_walk_speed *= 0.1
        self.spaz.max_run_speed *= 0.1
        def place():
            self.spaz.max_walk_speed /= 0.1
            self.spaz.max_run_speed /= 0.1
            if self.can_spaz_can_do_stuff():
                self.play_sound('place_object', position=self.spaz.node.position)
                MusicBox(self.spaz.node.position).autoretain()
            self.placing = False
        bs.timer(2, place)

      

  
    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=15,
                    spaz=self.spaz,
                    type='spaz_punch',
                    hurt_sound=None,
                    
                )
            )
            self.play_sound('swing_hit', position=self.spaz.node.position)
            self._punched_nodes.add(node)

        return False
