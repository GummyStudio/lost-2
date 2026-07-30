from lost.lost import CharacterMoveset, AsymFactory
import bascenev1 as bs
import babase, random, math
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor.spaz import Spaz

class AgentSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 100

    move_speed = 0.85
    run_speed =  0.9
    ability1_cooldown = 1.0
    ability2_cooldown = 26
    ability3_cooldown = 0.2

    ability1_icon = 'C'
    ability2_icon = babase.charstr(babase.SpecialChar.TEST_ACCOUNT)
    ability3_icon = babase.charstr(babase.SpecialChar.LEFT_ARROW)

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
        }
        self.factory = AsymFactory.get()
        self.modes = ['Random', 'Body Block', 'Control']
        self.mode = 0
        self.last_clone_move = -999
        self.clone: Spaz = None
        bs.timer(0.001, self.handle_clone, repeat=True)
        self.controling_clone = False
        self.kill_clone_timer = None

    @property
    def clone_mode(self):
        return self.modes[self.mode]
    
    
    def handle_clone(self):
        if not self.clone:
            return
        if not self.clone.is_alive():
            return
        
        if self.clone_mode == 'Random':
            if not ((bs.time() - self.last_clone_move) >= 0.4):
                return
            self.last_clone_move = bs.time()
            self.clone.on_run(0)
            self.clone.on_move_left_right(random.choice([-1, 0, 1]))
            self.clone.on_move_up_down(random.choice([-1, 0, 1]))
            self.clone.on_run(1)

        elif self.clone_mode == 'Body Block':
            if not ((bs.time() - self.last_clone_move) >= 0.1):
                return
            
            # If we dont exist anymore, just go back to random.
            if not self.spaz.is_alive():
                self.mode = 0
                return
            self.last_clone_move = bs.time()
            spaz_pos = self.spaz.node.position
            clone_pos = self.clone.node.position

            dx = spaz_pos[0] - clone_pos[0]
            dz = spaz_pos[2] - clone_pos[2]
            dist = math.hypot(dx, dz)

            move_x = dx / dist
            move_z = dz / dist
            self.clone.on_run(0)
            self.clone.on_move_left_right(move_x)
            self.clone.on_move_up_down(-move_z)
            bs.timer(0.0011, bs.Call(self.clone.on_run, 1.0))
            
            
        elif self.clone_mode == 'Control':
            if self.controling_clone:
                
                self.clone.on_move_left_right(self.spaz.input_x)
                self.clone.on_move_up_down(self.spaz.input_y)
                self.clone.on_run(self.spaz.input_run)
                bs.timer(0.0011, bs.Call(self.spaz.safesetattr, self.spaz.node, 'move_left_right', 0))
                bs.timer(0.0011, bs.Call(self.spaz.safesetattr, self.spaz.node, 'move_up_down', 0))
                bs.timer(0.0011, bs.Call(self.spaz.safesetattr, self.spaz.node, 'run', 0))
               
                
            else:
                self.clone.on_move_left_right(0)
                self.clone.on_move_up_down(0)
                self.clone.on_run(0)
    
    def kill_clone(self):
        if self.clone:
            self.clone.handlemessage(bs.DieMessage())
            self.clone = None
            self.kill_clone_timer = None

    def ability1(self):
        self.controling_clone = not self.controling_clone
        PopupText(
            'Controling clone...' if self.controling_clone else 'Returning input.',
            position=self.spaz.node.position,
            scale=0.75
        ).autoretain()
    def ability2(self):
        self.kill_clone()

        self.clone = Spaz(
            color=self.spaz.color,
            highlight=self.spaz.highlight,
            character=self.spaz.character,
            source_player=None, start_invincible=False,
            is_killer=False
        )
        hurt = self.spaz.node.hurt
        self.clone.node.hurt = 0.1
        self.clone.node.hurt = hurt
        self.spaz.node.hurt = 0.1
        self.spaz.node.hurt = hurt
        self.clone.hitpoints = self.spaz.hitpoints
        self.clone.hitpoints_max = self.spaz.hitpoints_max
        self.clone.node.is_area_of_interest = self.spaz.node.is_area_of_interest
        self.clone.node.name = self.spaz.node.name
        self.clone.node.name_color = self.spaz.node.name_color
        self.clone.moveset._last_used_1 = self._last_used_1
        self.clone.moveset._last_used_2 = bs.time()
        self.clone.moveset._last_used_3 = self._last_used_3
        self.clone.handlemessage(bs.StandMessage(
            (
                self.spaz.node.position[0],
                self.spaz.node.position[1]-1.1,
                self.spaz.node.position[2],
            )
        ))
        self.kill_clone_timer = bs.Timer(15, self.kill_clone)
    def ability3(self):
        if self.mode+1 == len(self.modes):
            self.mode = 0
        else:
            self.mode += 1
        
        PopupText(
            self.clone_mode,
            position=self.spaz.node.position,
            scale=0.8
        ).autoretain()
        


        
 
   
        