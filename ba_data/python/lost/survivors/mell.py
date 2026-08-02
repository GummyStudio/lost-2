from lost.lost import CharacterMoveset, DamageMessage, AsymFactory, SurvivorDetectedMessage, StunMessage, KillerDetectedMessage
import bascenev1 as bs
import babase

class HealingItem(bs.Actor):
    def __init__(self,position, velocity, node):
        super().__init__()
        self.node = bs.newnode(
            'prop',
            delegate=self,
            owner=node,
            attrs={
                'body': 'box',
                'position': position,
                'velocity': velocity,
                'mesh': bs.getmesh('powerup'),
                'light_mesh': bs.getmesh('powerupSimple'),
                'shadow_size': 0.5,
                'color_texture': bs.gettexture('powerupHealth'),
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': [AsymFactory.get().killer_trap_object_material],
            },
        )

        
        self.owner = node
        self.impulse(x=7, y=4)
        self.active = False
        bs.timer(1.6, self.activate)
        try: bs.timer(40, bs.Call(self.safesetattr, self.node, 'flashing', True))
        except: pass
        bs.timer(45, bs.WeakCall(self.handlemessage, bs.DieMessage()))
    
    def on_expire(self):
        self.owner = None
        
    
    def exists(self):
        return bool(self.node)

    def is_alive(self):
        return bool(self.node)

    def activate(self):
        self.active = True
       
        

   

    def handlemessage(self, msg):
        if isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, SurvivorDetectedMessage):
            if not self.active:
                return
            if not self.is_alive():
                return
            
            node = bs.getcollision().opposingnode
            if node == self.owner:
                return
         
            node.getdelegate(bs.Actor).hitpoints = min(node.getdelegate(bs.Actor).hitpoints+50, node.getdelegate(bs.Actor).hitpoints_max)
            node.hurt = (
                1.0 - float(node.getdelegate(bs.Actor).hitpoints) / node.getdelegate(bs.Actor).hitpoints_max
            )

            def heal():
                if not node.exists():
                    return
                node.getdelegate(bs.Actor).hitpoints = min(node.getdelegate(bs.Actor).hitpoints+30, node.getdelegate(bs.Actor).hitpoints_max)
                node.hurt = (
                    1.0 - float(node.getdelegate(bs.Actor).hitpoints) / node.getdelegate(bs.Actor).hitpoints_max
                )

            for _ in range(10):
                bs.timer(0.1*_, heal)
            bs.getsound('powerup01').play()
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            self.active = False
            self.node.delete()
        return super().handlemessage(msg)

class TauntHitbox(bs.Actor):
    def __init__(self,position):
        super().__init__()
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': (0,0,0),
                    'body': 'sphere',
                    'body_scale': 5,
                    'mesh_scale': 0.0,
                    'shadow_size': 0.44,
                    'materials': [AsymFactory.get().survivor_trap_object_material],
                },
            )
        self.active = True
       
        bs.timer(0.1, bs.WeakCall(self.handlemessage, bs.DieMessage()))
    
    def on_expire(self):
        self.owner = None
        
    
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
            self.active = False
            
            node = bs.getcollision().opposingnode
            
            node.getdelegate(bs.Actor).impulse(
                x=-18, y=9
            )
            bs.getsound('tauntHit').play(1.5)
            node.handlemessage(StunMessage(
                duration=1.5,
                type='mell_taunt',
                use_node_knockout_message=True,
            ))
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            self.active = False
            self.node.delete()
        return super().handlemessage(msg)
    
class MellSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 80

    move_speed = 0.85
    run_speed =  0.9
    ability1_cooldown = 0.0
    ability2_cooldown = 45
    ability3_cooldown = 20

    ability1_icon = ''
    ability2_icon = babase.charstr(babase.SpecialChar.RIGHT_ARROW)
    ability3_icon = babase.charstr(babase.SpecialChar.PLAY_STATION_CROSS_BUTTON)

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'throw': bs.getsound('ElliotPizzaToss'),
            'speed': bs.getsound('ElliotRushHour'),
            'taunt': bs.getsound('Yeah_come_get_some_ya_freakin_wuss')
        }
        self.throwing_bomb=False
        self.factory = AsymFactory.get()
        

    def ability1(self):
        pass
        
        
    def ability2_extra_conditions(self):
        return not self.throwing_bomb
    def ability1_extra_conditions(self):
        return not self.throwing_bomb
        
    def taunt(self):
        if self.spaz:
            if self.spaz.is_alive():
                self.play_sound('taunt')
                self.spaz.handlemessage(bs.CelebrateMessage(0.7))
                def taunt():
                    if self.spaz:
                        if self.spaz.is_alive():
                            TauntHitbox(self.spaz.node.position).autoretain()
                bs.timer(0.7, taunt)
    def ability2(self):
        self.spaz.speed_boost(2)
        self.play_sound('speed')
        bs.timer(0.5, self.taunt)

       
    def ability3(self):
        self.throwing_bomb = True
        
        self.spaz.handlemessage(bs.CelebrateMessage(1.2))
        
        def throw():
            if self.spaz:
                self.play_sound('throw')
                HealingItem(self.spaz.node.position, self.spaz.node.velocity, self.spaz.node).autoretain()
                self.throwing_bomb = False
        bs.timer(1.2,throw)

   
 
    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=10,
                    spaz=self.spaz,
                    type='zoe_stab',
                    hurt_sound=None,
                )
            )
            self.play_sound('stab_hit', position=self.spaz.node.position)
            

        return False
    
  

    
    
        