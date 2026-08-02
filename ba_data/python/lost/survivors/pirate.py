from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, KillerDetectedMessage, StunMessage
import bascenev1 as bs
import babase

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
        self.active = False
        bs.timer(3, self.activate)
    
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
    ability2_cooldown = 0.0
    ability3_cooldown = 37

    ability1_icon = ''
    ability2_icon = ''
    ability3_icon = babase.charstr(babase.SpecialChar.LOGO)

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'bomb_throw': bs.getsound('Taph_mine_throw')
        }
        self.throwing_bomb=False
        self.factory = AsymFactory.get()
        

    def ability1(self):
        pass
        
        
    def ability2_extra_conditions(self):
        return not self.throwing_bomb
    def ability1_extra_conditions(self):
        return not self.throwing_bomb
        
        
    def ability2(self):
        pass
    def ability3(self):
        self.throwing_bomb = True
        
        self.spaz.node.hold_node = GhostTrap(self.spaz.node.position).autoretain().node
        bs.timer(3, bs.WeakCall(self.play_sound, 'bomb_throw'))
        def throw():
            self.spaz.node.bomb_pressed = True
            self.spaz.node.bomb_pressed = False
            self.throwing_bomb = False
        bs.timer(1,throw)

   
 
   
  

    
    
        