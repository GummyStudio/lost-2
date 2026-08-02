from lost.lost import (
    CharacterMoveset, DamageMessage, AsymFactory, 
    KillerDetectedMessage, StunMessage,
    SurvivorDetectedMessage, SurvivorUnDetectedMessage
)
import bascenev1 as bs
import babase
from bascenev1lib.actor.popuptext import PopupText

class Dispenser(bs.Actor):
    def __init__(self,position, idle_sound):
        super().__init__()
        self.idle_sfx = bs.newnode('sound', attrs={
            'sound': idle_sound,
            'loop': True,
            'volume': 0.55,
        })
        self.hp = 35
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': (
                        position[0], position[1]+1, position[2]
                    ),
                    'velocity': (0,0,0),
                    'mesh': bs.getmesh('tnt'),
                    'body': 'box',
                    'body_scale': 1.0,
                    'mesh_scale': 0.95,
                    'shadow_size': 0.44,
                    'color_texture': bs.gettexture('flagPoleColor'),
                    'reflection': 'powerup',
                    'reflection_scale': [-2.0],
                    'materials': [AsymFactory.get().survivor_trap_object_material],
                },
            )
        self.expl_snd = bs.getsound('BoomBuilder')
        self.hitbox = bs.newnode(
                'region',
                delegate=self,
                attrs={
                    'scale': (1.35, 1.62, 1.65),
                    'type': 'sphere',
                    'materials': [AsymFactory.get().killer_trap_object_material],
                },
            )
        self.node.connectattr('position', self.hitbox, 'position')
        
        self.active = True
        self.nodes = []
        bs.timer(1, self.heal, repeat=True)
       
    def heal(self):
        if not self.active:
            return
        if not self.is_alive():
            return
        PopupText(
                '+',
                position=self.node.position,
                color=(0.5, 1, 0.5),
            ).autoretain()
            
        for node in self.nodes:
            if not node.exists():
                continue
            if node.getnodetype() != 'spaz':
                return
            node.getdelegate(bs.Actor).hitpoints = min(node.getdelegate(bs.Actor).hitpoints+10, node.getdelegate(bs.Actor).hitpoints_max)
            node.hurt = (
                1.0 - float(node.getdelegate(bs.Actor).hitpoints) / node.getdelegate(bs.Actor).hitpoints_max
            )
            PopupText(
                '+',
                position=node.position,
                color=(0.5, 1, 0.5),
            ).autoretain()
            
    
    def exists(self):
        return bool(self.node)

    def is_alive(self):
        return bool(self.node)

  

   

    def handlemessage(self, msg):
        if isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, DamageMessage):
            if not self.active:
                return
            if not self.is_alive():
                return
            
            self.hp -= msg.damage

            if self.hp <= 0:
                self.handlemessage(bs.DieMessage())
        elif isinstance(msg, KillerDetectedMessage):
            if not self.active:
                return
            if not self.is_alive():
                return
            node = bs.getcollision().opposingnode
            # check if they are punching
            try:
                was_punching = bool(node.punch_pressed)
            except: was_punching = False
            if was_punching:
                
                    self.handlemessage(bs.DieMessage())
                    
        elif isinstance(msg, SurvivorDetectedMessage):
            if not self.active:
                return
            if not self.is_alive():
                return
            node = bs.getcollision().opposingnode
            if node.getnodetype() != 'spaz':
                return
            if node not in self.nodes:
                self.nodes.append(node)
        elif isinstance(msg, SurvivorUnDetectedMessage):
            if not self.active:
                return
            if not self.is_alive():
                return
            node = bs.getcollision().opposingnode
            if node.getnodetype() != 'spaz':
                return
            if node in self.nodes:
                self.nodes.remove(node)
        elif isinstance(msg, bs.DieMessage):
            if self.active and self.node:
                self.expl_snd.play()
                bs.emitfx(
                    position=self.node.position,
                    velocity=(0,0.25,0),
                    scale=2,
                    spread=0.1,
                )
                exl=bs.newnode(
                    'explosion',
                    attrs={
                        'position': self.node.position,
                        'color': (1, 0.5, 0.5),
                        'velocity': (0,0,0),
                        'radius': 2.8,
                        'big': True,
                    },
                )
                scorch = bs.newnode(
                    'scorch',
                    attrs={
                        'position': self.node.position,
                        'size': 1.2,
                        'big': True,
                    },
                )
            

                bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
                bs.timer(13.0, scorch.delete)
                bs.timer(1.0, exl.delete)
            self.active = False
            self.hitbox.delete()
            self.node.delete()
            self.idle_sfx.delete()
            
        return super().handlemessage(msg)
    
class GhostTrap(bs.Actor):
    def __init__(self,position):
        super().__init__()
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': (0,0,0),
                    'mesh': bs.getmesh('powerup'),
                    'body': 'crate',
                    'body_scale': 1.1,
                    'mesh_scale': 0.95,
                    'shadow_size': 0.44,
                    'color_texture': bs.gettexture('achievementFlawlessVictory'),
                    'reflection': 'powerup',
                    'reflection_scale': [0.0],
                    'materials': [AsymFactory.get().survivor_trap_object_material],
                },
            )
        self.active = True
    
    def exists(self):
        return bool(self.node)

    def is_alive(self):
        return bool(self.node)

    def activate(self):
        self.active = True
        if self.exists():
            self.node.reflection_scale = [-2.0]
        

   

    def handlemessage(self, msg):
        if isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, KillerDetectedMessage):
            if not self.active:
                return
            if not self.is_alive():
                return
            node = bs.getcollision().opposingnode
            # check if they are punching
            try:
                was_punching = bool(node.punch_pressed)
            except: was_punching = False
            bs.getsound('explosion04').play()

            
            node.handlemessage(
                            DamageMessage(
                                damage=20,
                                spaz=None,
                                type='ninja_trap',
                                hurt_sound=None,
                            )
                        )
            # slow em
            def revert():
                node.getdelegate(bs.Actor).max_walk_speed /= 0.7
                node.getdelegate(bs.Actor).max_run_speed /= 0.01
            node.getdelegate(bs.Actor).max_walk_speed *= 0.7
            node.getdelegate(bs.Actor).max_run_speed *= 0.01
            bs.timer(2, revert)

            # stun em
            if not was_punching:
                node.handlemessage(
                            StunMessage(
                                duration=3,
                                spaz=None,
                                type='ninja_trap',
                                knockback_settings={
                                    'x': -2,
                                    'y': 2,
                                    'direction': node.velocity
                                },
                                use_node_knockout_message=True
                            )
                        )
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            self.active = False
            self.node.delete()
        return super().handlemessage(msg)
    
class PirateSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 100

    move_speed = 0.85
    run_speed =  0.9
    ability1_cooldown = 0.0
    ability2_cooldown = 22
    ability3_cooldown = 37

    ability1_icon = ''
    ability2_icon = babase.charstr(babase.SpecialChar.STEAM_LOGO)
    ability3_icon = babase.charstr(babase.SpecialChar.LOGO)

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'bomb_throw': bs.getsound('Taph_mine_throw'),
            'dispenser_idle': bs.getsound('IdleDispenserr'),
            'building_dispenser': bs.getsound('BuildDispenserr'),
            'explosion': bs.getsound('BoomBuilder'),

        }
        self.throwing_bomb=False
        self.factory = AsymFactory.get()
        self.create_dispenser_timer = None
        self.dispenser: Dispenser | None = None
        

    def ability1(self):
        pass
        
        
    def ability2_extra_conditions(self):
        return not self.throwing_bomb
    def ability3_extra_conditions(self):
        return not self.throwing_bomb

    def handle_recieved_damage(self, damage, type):
        # uhhhhhh
        # we trying to build a dispenser, die
        if self.create_dispenser_timer is not None:
            self.create_dispenser_timer = None
            self.throwing_bomb = False
            self.spaz.max_run_speed /= 0.1
            self.spaz.max_walk_speed /= 0.1
            self.play_sound('explosion')


        return True

    def spaz_lost_all_hp(self, type):
        super().spaz_lost_all_hp(type)
        if self.dispenser:
            self.dispenser.handlemessage(bs.DieMessage())
    
        
        
    def ability2(self):
        if self.dispenser:
            self.dispenser.handlemessage(bs.DieMessage())
            self.dispenser = None
        self.throwing_bomb = True
        self.play_sound('building_dispenser')
        self.spaz.max_run_speed *= 0.1
        self.spaz.max_walk_speed *= 0.1
        self.spaz.handlemessage(bs.CelebrateMessage(6))
        
        
        def throw():
            self.create_dispenser_timer = None
            self.spaz.max_run_speed /= 0.1
            self.spaz.max_walk_speed /= 0.1
            
            self.throwing_bomb = False
            Dispenser(self.spaz.node.position, self.sfx.get('dispenser_idle')).autoretain()
        self.create_dispenser_timer = bs.Timer(6,throw)
    def ability3(self):
        self.throwing_bomb = True
        
        self.spaz.node.hold_node = GhostTrap(self.spaz.node.position).autoretain().node
        bs.timer(3, bs.WeakCall(self.play_sound, 'bomb_throw'))
        def throw():
            self.spaz.node.bomb_pressed = True
            self.spaz.node.bomb_pressed = False
            self.throwing_bomb = False
        bs.timer(1,throw)

   
 
   
  

    
    
        