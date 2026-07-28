from lost.lost import CharacterMoveset, DamageMessage, AsymFactory
import bascenev1 as bs
import babase


class ZoeSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 80

    move_speed = 0.85
    run_speed =  0.9
    ability1_cooldown = 25
    ability2_cooldown = 45
    ability3_cooldown = 0.0

    ability1_icon = babase.charstr(babase.SpecialChar.MOON)
    ability2_icon = babase.charstr(babase.SpecialChar.DOWN_ARROW)
    ability3_icon = ''

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'respawn': bs.getsound('Two_time_respawnnew'),
            'stab_hit': bs.getsound('Two_time_stab_hit'),
        }
        self.factory = AsymFactory.get()
        self.oblation = 0
        self.second_life = False
        self.light = bs.Node(None)

    def ability1(self):
        self._punched_nodes = set()
        
        self.spaz.node.punch_pressed = True
        self.spaz.node.punch_pressed = False
        self.spaz.max_walk_speed *= 0.1
        
        def revert():
            self.spaz.impulse(x=4.5, y=1)
            self.spaz.max_walk_speed /= 0.1
        bs.timer(0.1, revert)
        
    def ability2(self):
        self.spaz.max_walk_speed *= 0.02
        
        def revert():
            self.spaz.impulse(x=6, y=1)
            self.spaz.max_walk_speed /= 0.02
        bs.timer(0.1, revert)
    def ability3(self):
        # Doesnt do anything
        pass

   
 
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
            self.oblation += 35
            self._punched_nodes.add(node)
            def revert():
                node.getdelegate(bs.Actor).max_walk_speed /= 0.5
                node.getdelegate(bs.Actor).max_run_speed /= 0.2
            node.getdelegate(bs.Actor).max_walk_speed *= 0.5
            node.getdelegate(bs.Actor).max_run_speed *= 0.2
            bs.timer(2, revert)

        return False
    
    def respawn(self):
        if self.second_life:
            return
        if not self.spaz.is_alive():
            return
        # stat changes
        self.second_life = True
        self.spaz.hitpoints = 400
        self.spaz.hitpoints_max = 400
        self.spaz.node.hurt = 0
        self.spaz.handlemessage(bs.StandMessage(self.spaz.getactivity().map.get_ffa_start_position(
            list(self.spaz.getactivity().killers)
            )))
        self.spaz.node.hockey = True

        self.play_sound('respawn', position=self.spaz.node.position)
        # get stat buffs
        self.spaz.set_invincible(5)
        self.spaz.speed_boost(2)

        # Also give us a light telling the killer were on a second life
        self.light = bs.newnode(
            'light',
            owner=self.spaz.node,
            attrs={
                'volume_intensity_scale': 10.0,
                'color': self.spaz.node.color,
            },
        ) 
        self.spaz.node.connectattr('position', self.light, 'position')
    
    def die(self):
        super().spaz_lost_all_hp()
        self.light.delete()
        

    def spaz_lost_all_hp(self):
        # First off, if were on a second life die.
        if self.second_life:
            self.die()
            return
        
        # If we arent, check if oblation is at full, then respawn.
        if self.oblation > 99:
            self.respawn()
        else:
            # Otherwise die...
            self.die()

    
    
        