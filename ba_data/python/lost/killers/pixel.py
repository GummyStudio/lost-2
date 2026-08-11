import math
from lost.factory import (
    DamageMessage,
    AsymFactory
)
from lost.character_moveset import CharacterMoveset
import bascenev1 as bs
import babase, random
from bascenev1lib.actor.spaz import Spaz

class PixelMinion(CharacterMoveset):
    """minion"""
    is_killer = True
    hitpoints = 25
    move_speed = 0.65

    ability1_cooldown = 0.0
    ability2_cooldown = 0.0
    ability3_cooldown = 0.0

    ability1_icon = ''
    ability2_icon = ''
    ability3_icon = ''


    def __init__(self, spaz):
        super().__init__(spaz)
       
        self.sfx = {
            'swing_hit': bs.getsound('1xMinionHitNew'),
        }
        self.default_aggro_range = 4
        self.default_deaggro_range = 6.6
        self.attack_range = 1


        self.aggro_range = self.default_aggro_range
        self.deaggro_range = self.default_deaggro_range
        self.damage = 10
        self.target_survivor = None

        self.owner_moveset: PixelKiller = None
        self.tick_timer = bs.Timer(0.1, self._tick, repeat=True)
        self.idle_sfx = bs.newnode(
                 type='sound',
                 attrs={
                     'sound': bs.getsound('1xMinionIdleNew'),
                     'positional': True,
                     'volume': 0.5,
                     'loop': True,
                 },
        )
        self.spaz.node.connectattr('position', self.idle_sfx, 'position')
        self.idle_sound = bs.newnode('sound')
    
    def _tick(self):
        # im lazy
        try:
            if not self.spaz or not self.spaz.is_alive():
                return

            if not self.can_spaz_can_do_stuff():
                return
            if not self.owner_moveset:
                return

            my_pos = self.spaz.node.position

            # if we have a target and is still valid and in de-aggro range jst de aggro ig.
            if self.target_survivor:
                target_spaz = self.target_survivor
                if not target_spaz or not target_spaz.is_alive() or target_spaz.node:
                    self.target_survivor = None
                    return
                else:
                    dist = math.dist(my_pos, target_spaz.node.position)
                    if dist > self.deaggro_range:
                        self.target_survivor = None
                        return
                

            # search
            if not self.target_survivor:
                activity = bs.getactivity()
                survivors = activity.survivors
                activity = None


                closest_dist = self.aggro_range
                best_target = None

                for survivor in survivors:
                    s_spaz = survivor.actor
                    if s_spaz and s_spaz.is_alive() and s_spaz.node:
                        dist = math.dist(my_pos, s_spaz.node.position)
                        if dist < closest_dist:
                            closest_dist = dist
                            best_target = s_spaz

                self.target_survivor = best_target
                

            # we have one! get em
            if self.target_survivor:
                t_pos = self.target_survivor.node.position
                dist = math.dist(my_pos, t_pos)

                # move
                dx = t_pos[0] - my_pos[0]
                dz = t_pos[2] - my_pos[2]

                if dist > 0.1:
                    self.spaz.on_move_left_right(dx / dist)
                    self.spaz.on_move_up_down(-(dz / dist))

                # in range!
                if dist <= self.attack_range:
                    self.punch()
            else:
                # no one..
                self.spaz.on_move_left_right(0.0)
                self.spaz.on_move_up_down(0.0)
        except Exception as e: 
            print(e)
    
    def punch(self) -> None:
        if not self.spaz.is_alive():
            return
        if self.spaz.node.punch_pressed:
            return
        self._punched_nodes = set()
        
        self.spaz.node.punch_pressed = True
        try: bs.timer(0.5, bs.Call(setattr, self.spaz.node, 'punch_pressed', False))
        except: pass
        # kay, be unable to do anything until a bit.
        self.aggro_range = 0.0
        self.deaggro_range = -1
        self.target_survivor = None
        def revert():
            self.aggro_range = self.default_aggro_range
            self.deaggro_range = self.default_deaggro_range
        bs.timer(5, revert)
    
    def spaz_lost_all_hp(self, type):
        super().spaz_lost_all_hp(type)
        # ow, remove our selves so we dont get grabbed by our owner.
        if self.spaz in self.owner_moveset.minions:
            self.owner_moveset.minions.remove(self.spaz)
        

        # also, always gib.
        self.spaz.shatter(True)

        # clean
        self.tick_timer = None
        self.idle_sfx.delete()

  
   

    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=self.damage,
                    spaz=self.spaz,
                    type='pixel_minion_punch',
                    hurt_sound=None,
                )
            )
            self.play_sound('swing_hit', position=self.spaz.node.position)
            # temporarily weaken them.
            def revert():
                if not node:
                    return
                node.getdelegate(bs.Actor).max_walk_speed /= 0.98
                node.getdelegate(bs.Actor).max_run_speed /= 0.98
                node.getdelegate(bs.Actor).damage_scale /= 1.15
            node.getdelegate(bs.Actor).max_walk_speed *= 0.98
            node.getdelegate(bs.Actor).max_run_speed *= 0.98
            node.getdelegate(bs.Actor).damage_scale *= 1.15
            bs.timer(3, revert)
            self._punched_nodes.add(node)
            


        return False

class MinionVenus(bs.Actor):
    
    def __init__(self, position: list[float], moveset):
        super().__init__()
        self.position = position
        self.moveset = moveset
        self.percent = 0
        self.reveal_sfx = bs.getsound('plantexplode')
      
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'mesh': bs.getmesh('bombSticky'),
                'color_texture': bs.gettexture('egg3'),
                'mesh_scale': 0.0,
                'body': 'puck',
                'body_scale': 0.0,
                'position': (
                    position[0],
                    position[1] + 0.2,
                    position[2]
                ),
                'velocity': (0, 0, 0),
                'gravity_scale': 0.0,
                'materials': [
                    AsymFactory.get().no_collision,
                ],
                'shadow_size': 0.5,
                'reflection': 'powerup',
                'reflection_scale': [-1.0],
            },
        )

        self.text_node: bs.Node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': '0%',
                'in_world': True,
                'scale': 0.015,
                'color': (0.86, 0.86, 1.0),
                'position': (self.position[0]-0.35, self.position[1] + .5, self.position[2]),
            }
        )
        scl = 1.5
        bs.animate(
            self.node,
            'mesh_scale',
            {
                0.0: 0.0,
                0.2: scl*1.2,
                0.35: scl*1.1,
                0.45: scl,
            },
        )
        self.active = True
        bs.timer(1.6, bs.Call(self.add_percent, 3.7), repeat=True)
        try:
            if self.getactivity().lms:
                bs.timer(0.8, bs.Call(self.add_percent, 4.71), repeat=True)
        except: pass

    def add_percent(self, amount: int = 2):
        if not self.exists():
            return
        if not self.active:
            return
        self.percent = float(max(0, min(
            self.percent + amount, 100
        )))

        if int(self.percent) == 100:
            # spawn guy and DIE!
            self.spawn_dude()
            self.handlemessage(bs.DieMessage())
   
        if self.text_node:
            self.text_node.text = f"{int(self.percent)}%"

    def exists(self):
        return bool(self.node)
    
    def is_alive(self):
        return bool(self.node)

    def spawn_dude(self):
                if not self.active:
                    return
                self.reveal_sfx.play()
                # Create spaps
                char = 'VenusMinion'
                minion = Spaz(
                    character=char,
                    color=bs.app.classic.spaz_appearances[char].default_color,
                    highlight=bs.app.classic.spaz_appearances[char].default_highlight,
                    source_player=None,
                    start_invincible=True,
                    is_killer=True,
                ).autoretain()
                
                minion.handlemessage(bs.StandMessage(position=(
                    self.position[0],
                    self.position[1] - 1.0,
                    self.position[2]
                    )))
                minion.node.is_area_of_interest = False
                # okay, now set the minions moveset owner to be our owner??
                minion.moveset.owner_moveset = self.moveset
                # also if were in the movesets list remove ourselves cause were of no use
                if self in self.moveset.minion_spawners:
                    self.moveset.minion_spawners.remove(self)
                # and add the minion to the movesets minion list
                self.moveset.minions.append(minion)
        
         
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            self.active = False

            if msg.immediate:
                self.node.delete()
                self.text_node.delete()
            
            elif self.is_alive():
                self.text_node.text = '100%'
                scl = self.node.mesh_scale
                bs.animate(
                    
                    self.node,
                    'mesh_scale',
                    {
                        0.0: scl,
                        0.2: scl*1.4,
                        0.35: scl*0.4,
                        0.45: 0.0,
                    },
                )
                bs.animate_array(
                    self.text_node,
                    'color',
                    4,
                    {
                        0.0: (1,0,0,1),
                        0.45: (1,0,0,0),
                    },
                )
                scorch = bs.newnode(
                    'scorch',
                    attrs={
                        'position': self.position,
                        'size': 2.5,
                        'big': False,
                    },
                )
                scorch.color = (0.46, 0, 0.46)
                bs.emitfx(
                    position=self.position,
                    velocity=(0,0.25,0),
                    count=4,
                    scale=2.5,
                    spread=0.1,
                )
            

                bs.animate(scorch, 'presence', {3.000: 1, 26.000: 0})
                bs.timer(26.0, scorch.delete)
                bs.timer(0.45, self.node.delete)
                bs.timer(0.45, self.text_node.delete)
            
                
                
            
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else: 
            return super().handlemessage(msg)


class PixelKiller(CharacterMoveset):
    """ woman thta spawns miinons"""
    is_killer = True
    chase_theme_dir = 'FirstBornAzureLayer4'
    hitpoints = 670 # sixth seventh!! kys aw ok

    move_speed = 0.85
    run_speed = 1.0

    ability1_cooldown = 1.55
    ability2_cooldown = 6#0.85
    ability3_cooldown = 16

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = 'U'
    ability3_icon = babase.charstr(babase.SpecialChar.PARTY_ICON) 


    def __init__(self, spaz):
        super().__init__(spaz)
       
        self.sfx = {
            'swing': bs.getsound('1xnewslashaud'),
            'swing_hit': bs.getsound('1xSlashHitNew'),
            'plant': bs.getsound('plant'),
        }
        self.minion_spawners: list[MinionVenus] = []
        self.minions: list[Spaz] = []
        self.spawning_a_spawner = False

    def ability1_extra_conditions(self):
        return not self.spawning_a_spawner
    def ability2_extra_conditions(self):
        return not self.spawning_a_spawner
    def ability3_extra_conditions(self):
        return not self.spawning_a_spawner
    
    def ability1(self) -> None:
        self._punched_nodes = set()
        
        self.spaz.node.punch_pressed = True
        try: bs.timer(0.6, bs.Call(setattr, self.spaz.node, 'punch_pressed', False))
        except: pass
        self.play_sound('swing', position=self.spaz.node.position)

    def ability2(self) -> None:
        if self.spaz.node.hold_node:

            # ok, grab the guy were holding.
            minion_held = self.spaz.node.hold_node.getdelegate(Spaz)
            assert isinstance(minion_held, Spaz)
            
            self.spaz.node.bomb_pressed = True
            self.spaz.node.bomb_pressed = False
            # Force cooldown.
            self._last_used_2 = bs.time()

            # idk who we threw but if its not a minion then idk gang
            if not minion_held:
                return
            # add an impulse to the throw cuz lowk the default throw
            # sucks ass when it comes to spazes
            minion_held.impulse(
                x=3,
                y=4,
                direction= (
                    self.spaz.node.move_left_right*2,
                    1,
                    -self.spaz.node.move_up_down*2
                )
            )

            return
        self.spaz.node.pickup_pressed = True
        self.spaz.node.pickup_pressed = False
        # Force cooldown.
        self._last_used_2 = bs.time()-5.8

        killer_pos = self.spaz.node.position
        closest_minion = None
        closest_dist = 2.5

        # find the MINION
        valid_minions = []
        for minion in self.minions:
            if minion and minion.is_alive() and minion.node:
                valid_minions.append(minion)
                dist = math.dist(killer_pos, minion.node.position)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_minion = minion

        # clean up
        self.minions = valid_minions

        # ok grab him
        if closest_minion:
            self.spaz.node.hold_body = 1 # grab the torso, always.
            self.spaz.node.hold_node = closest_minion.node
            
            
        
    def ability3(self) -> None:
        self.spawning_a_spawner = True
        dur = 0.23
        self.spaz.node.handlemessage('celebrate_r', dur*(1000))
        def spawn():
            
            if self.spawning_a_spawner:
                spawner = MinionVenus(
                    position=self.spaz.node.position,
                    moveset=self
                )
                self.play_sound('plant')
                self.minion_spawners.append(spawner)
                self.spawning_a_spawner = False
        bs.timer(dur, spawn)
    
    def handle_spaz_was_stunned(self, type):
        super().handle_spaz_was_stunned(type)
        if self.spawning_a_spawner:
            self.spawning_a_spawner = False
        if self.spaz.node.hold_node:
            self.spaz.node.hold_node = None
            # Force cooldown.
            self._last_used_2 = bs.time()

        
   

    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            node.handlemessage(
                DamageMessage(
                    damage=14,
                    spaz=self.spaz,
                    type='pixel_punch',
                    hurt_sound=None,
                )
            )
            self.play_sound('swing_hit', position=self.spaz.node.position)
            self._punched_nodes.add(node)
            


        return False