"""Base module for character movesets."""
import bascenev1 as bs
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.mainmenu import MainMenuActivity
from lost.lobby import Lobby

DEFAULT_ABILITY_DESC = "No description for this ability."
DEFAULT_CHAR_DESC = "One of the many characters from Lost...{'type': 'separator'}..whoops, i don't know what this one does. Sorry."

class CharacterMoveset:
    """ 
    
        A template to create a moveset that doesnt effect spaps.

        has stuff like the run speed and walk speed, 
        abilities, chase themes and all the nooks and crannys
    
    """
    is_killer = True
    """ are we kiler"""

    hitpoints = 100 # will be multiplied by ten


    chase_theme_dir = 'blank'
    """ bs.getsound(cls.chase_theme_dir) """

    low_theme_dir = 'blank'
    """bs.getsound(cls.low_theme_dir)"""

    move_speed = 0.8
    run_speed =  1.0
    """ spaps will take this into account """

    ability1_cooldown = 0
    ability2_cooldown = 0
    ability3_cooldown = 0
    """ cooldowns """
    
    description: str = DEFAULT_CHAR_DESC
    """A general description for your character;
    This will show up in this character's info card.
    You can fit as much info as you want here (aka, lore)
    but try to make it not TOO long. Line breaks are 
    automatically done."""
    
    ability1_description = DEFAULT_ABILITY_DESC
    ability2_description = DEFAULT_ABILITY_DESC
    ability3_description = DEFAULT_ABILITY_DESC
    """Descriptions for each of your abilities;
    These will show up in this character's info card.
    Try to keep them short so they fit nicely.
    Line breaks are automatically done."""

    ability1_icon: str
    ability2_icon: str
    ability3_icon: str
    """ ability icons that show up on the spazito """


    def __init__(self, spaz: Spaz):
        self._last_used_1 = -999
        self._last_used_2 = -999
        self._last_used_3 = -999
        self.spaz: Spaz = spaz
        self._punched_nodes = set()
        self._ability_ui_nodes: list[dict] = []

        # instead of annoyingly putting sfx in a factory, you can just use this.
        self.sfx = {}
      
        icons = [self.ability1_icon, self.ability2_icon, self.ability3_icon]
        offsets = [-0.35, 0.0, 0.35]

        for i in range(3):
            icon_node = bs.newnode(
                'text',
                owner=self.spaz.node,
                attrs={
                    'text': icons[i],
                    'in_world': True,
                    'scale': 0.010,
                    'color': (1.0, 1.0, 1.0),
                    'h_align': 'center',
                    'v_align': 'center',
                },
            )
            timer_node = bs.newnode(
                'text',
                owner=self.spaz.node,
                attrs={
                    'text': '',
                    'in_world': True,
                    'scale': 0.012,
                    'color': (1.0, 0.8, 0.8), 
                    'h_align': 'center',
                    'v_align': 'center',
                },
            )
            math_node = bs.newnode(
                'math',
                owner=self.spaz.node,
                attrs={
                    'input1': (offsets[i], 1.4, 0.0), 
                    'operation': 'add',
                },
            )

            self.spaz.node.connectattr('torso_position', math_node, 'input2')
            math_node.connectattr('output', icon_node, 'position')
            math_node.connectattr('output', timer_node, 'position')

            self._ability_ui_nodes.append({
                'icon': icon_node,
                'timer': timer_node,
            })

        # refres
        self._ui_update_timer = bs.Timer(
            0.1,
            bs.WeakCall(self._update_ability_ui),
            repeat=True,
        )

    def _update_ability_ui(self) -> None:
        if not self.spaz.is_alive() or not self._ability_ui_nodes:
            self._ui_update_timer = None
            return

        now = bs.time()
        cooldowns = [self.ability1_cooldown, self.ability2_cooldown, self.ability3_cooldown]
        last_used = [self._last_used_1, self._last_used_2, self._last_used_3]

        for i in range(3):
            elapsed = now - last_used[i]
            remaining = cooldowns[i] - elapsed
            ui = self._ability_ui_nodes[i]

            if remaining > 0:
                # we on coldown
                ui['icon'].color = (0.3, 0.3, 0.3)
                ui['icon'].opacity = 0.4
                ui['timer'].text = str(int(remaining) + 1)
            else:
                # ready
                ui['icon'].color = (1.0, 1.0, 1.0)
                ui['icon'].opacity = 1.0
                ui['timer'].text = ''
    
    def play_sound(self, sfx: str, volume=1, position=None):
        sfx_inc = None
        if not self.spaz:
            return
        if not self.spaz.is_alive():
            return
        if position is None:
            position = self.spaz.node.position
        if self.sfx.get(sfx, None):
            sfx_inc = self.sfx.get(sfx)
            sfx_inc.play(volume, position=position)
        
        return sfx
    

    def expire(self):
        self.spaz = None
        self._ui_update_timer = None
    
    def node_not_punched_nodes(self, node):
        return (node not in self._punched_nodes)

    
    def can_spaz_can_do_stuff(self):
        if not self.spaz:
            return False
        return not (
            not self.spaz.node
            or self.spaz._dead
            or self.spaz.frozen
            or self.spaz.node.knockout > 0.0
            or self.spaz.stunned
        )

    def can_do_ability1(self):
        return bool(
            (bs.time() - self._last_used_1) >= self.ability1_cooldown
            and self.can_spaz_can_do_stuff() and self.ability1_extra_conditions()
        )  
    def can_do_ability2(self):
        return bool(
            (bs.time() - self._last_used_2) >= self.ability2_cooldown
            and self.can_spaz_can_do_stuff() and self.ability2_extra_conditions()
        )  
    def can_do_ability3(self):
        return bool(
            (bs.time() - self._last_used_3) >= self.ability3_cooldown
            and self.can_spaz_can_do_stuff() and self.ability3_extra_conditions()
        )  
    
    def do_ability1(self):
        from bascenev1lib.mainmenu import MainMenuActivity
        if self.can_do_ability1():
            if not isinstance(bs.getactivity(), (Lobby, MainMenuActivity)):
                self._last_used_1 = bs.time()
            self.ability1()
    def do_ability2(self):
        from bascenev1lib.mainmenu import MainMenuActivity
        if self.can_do_ability2():
            if not isinstance(bs.getactivity(), (Lobby, MainMenuActivity)):
                self._last_used_2 = bs.time()
            self.ability2()
    def do_ability3(self):
        from bascenev1lib.mainmenu import MainMenuActivity
        if self.can_do_ability3():
            if not isinstance(bs.getactivity(), (Lobby, MainMenuActivity)):
                self._last_used_3 = bs.time()
            self.ability3()

    def ability1_extra_conditions(self):
        """ 
            extra conditions for ability1

            should be ovverriden by the moveset, 
            so like if doing an action, something else doesnt happpen. 
        """
        return True
    def ability2_extra_conditions(self):
        """ 
            extra conditions for ability2

            should be ovverriden by the moveset, 
            so like if doing an action, something else doesnt happpen. 
        """
        return True
    def ability3_extra_conditions(self):
        """ 
            extra conditions for ability3

            should be ovverriden by the moveset, 
            so like if doing an action, something else doesnt happpen. 
        """
        return True
    
    def ability1(self):
        raise NotImplementedError(f'{self.__class__.__qualname__}.ability1 in moveset not changed')
    def ability2(self):
        raise NotImplementedError(f'{self.__class__.__qualname__}.ability2 in moveset not changed')
    def ability3(self):
        raise NotImplementedError(f'{self.__class__.__qualname__}.ability3 in moveset not changed')

    def spaz_lost_all_hp(self, type):
        # By default we die here.
        self.spaz.handlemessage(
            bs.DieMessage(how=bs.DeathType.GENERIC)
        )
        if self.spaz.exists():

            # Special case: died to specific things will lead to interaction
            if type in ['ali_slam']:
                self.spaz.impulse(x=2, y=17, direction=self.spaz.node.velocity)
                self.spaz.shatter(True)

    def handle_spaz_was_stunned(self, type):
        """ wjhat do we do when we get stunned? """
    def handle_spaz_punched_something(self, collision: bs.Collision):
        """ 
            spaz punched something, give us the collision and we handle it. 
            return FALSE if you don't want the spaz to do any of its vanilla quirks 
            otherwise return True
        """
        return False
        
    def handle_spaz_hit_stun(self, type):
        """ what the character does when they hit a stun. """
    
    def handle_spaz_did_damage(self, type):
        """ what the character does when they deal damage. """

    def handle_recieved_damage(self, damage: float, type: str):
        """ can we recieve damage? Return True if yes, return False if No"""
        return True