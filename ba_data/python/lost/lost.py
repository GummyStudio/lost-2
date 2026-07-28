import bascenev1 as bs
from bascenev1._activitytypes import TransitionActivity
import random
from bascenev1lib import maps
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.gameutils import SharedObjects

import math
# FIXME: Merge this with bs.app.classic
killers = ['Spaz', 'Snake Shadow', 'Easter Bunny']


class DamageMessage:
    """ a message  that says how much damage someone should take"""

    def __init__(self, 
                 damage: float = 0, 
                 spaz: Spaz = None,
                type: str = 'normal',
                 hurt_sound: str | None = None
        ):
        self.damage = damage
        self.spaz = spaz # the person who hit us
        self.hittype = type
        if hurt_sound:
            self.hurt_sound = getattr(AsymFactory.get(), hurt_sound, None)
        else:
            self.hurt_sound = None
        


class StunMessage:
    """ a message that tells the person to be stunned for how long"""

    def __init__(
            self, 
            duration: float, 
            spaz: Spaz = None,
            type: str = 'normal',
            use_node_knockout_message: bool = False,
            knockback_settings: dict | None = None,
            hurt_sound: str | None = None
        ):
        self.duration = duration
        self.spaz = spaz # the person who hit us
        self.hittype = type
        self.node_knockout_message = use_node_knockout_message
        self.knockback_settings = knockback_settings
        if hurt_sound:
            self.hurt_sound = getattr(AsymFactory.get(), hurt_sound, None)
        else:
            self.hurt_sound = None
        # Example:
        {
            "direction": (0, 1, 0),
            "x": 800,
            "y": 30,
        }

class SurvivorDetectedMessage:
    """ send this to any object in need to detect a survivor. """

class KillerDetectedMessage:
    """ send this to any object in need to detect a killer. """

class CharacterMoveset:
    """ 
    
        A template to create a moveset that doesnt effect spaps.

        has stuff like the run speed and walk speed, 
        abilities, chase themes and all the nooks and crannys
    
    """
    is_killer = True
    """ are we kiler"""

    hitpoints = 100 # will be multiplied by ten


    chase_theme_dir = 'empty'
    """ bs.getsound(cls.chase_theme_dir) """

    move_speed = 0.8
    run_speed =  1.0
    """ spaps will take this into account """

    ability1_cooldown = 0
    ability2_cooldown = 0
    ability3_cooldown = 0
    """ cooldowns """

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
        if not self.spaz:
            return
        if not self.spaz.is_alive():
            return
        if position is None:
            position = self.spaz.node.position
        if self.sfx.get(sfx, None):
            self.sfx.get(sfx).play(volume, position=position)
    
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
        if self.can_do_ability1():
            if not isinstance(bs.getactivity(), Lobby):
                self._last_used_1 = bs.time()
            self.ability1()
    def do_ability2(self):
        if self.can_do_ability2():
            if not isinstance(bs.getactivity(), Lobby):
                self._last_used_2 = bs.time()
            self.ability2()
    def do_ability3(self):
        if self.can_do_ability3():
            if not isinstance(bs.getactivity(), Lobby):
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

    def spaz_lost_all_hp(self):
        # By default we die here.
        self.spaz.handlemessage(
            bs.DieMessage(how=bs.DeathType.IMPACT)
        )
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

    def handle_recieved_damage(self):
        """ can we recieve damage? Return True if yes, return False if No"""
        return True

        

    


    

    





class AsymFactory:
    """
    basically what im gonna do is just put everythingin here
    """
    

    _STORENAME = bs.storagename()

    @classmethod
    def get(cls):
        """Create and/or return the single shared instance of this class."""
        activity = bs.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = AsymFactory()
            activity.customdata[cls._STORENAME] = factory
        assert isinstance(factory, AsymFactory)
        return factory

   
    def __init__(self) -> None:

        self.player_death_sound = bs.getsound('playerDeath')
        # Killer material.
        self.killer_material = bs.Material()

        self.killer_material.add_actions(
            conditions=(
                'they_have_material',
                self.killer_material
                # They have our material, we shoulnt collide with them.
            ),
            actions=('modify_part_collision', 'collide', False),
       )

        # Survivor Material
        self.survivor_material = bs.Material()

        self.survivor_material.add_actions(
            conditions=(
                'they_have_material',
                self.survivor_material
                # They have our material, we shoulnt collide with them.
            ),
            actions=('modify_part_collision', 'collide', False),
       )
        
        # Killer doors.
        self.killer_door_material = bs.Material()
        # By default act like collision
        self.killer_door_material.add_actions(
            ('modify_part_collision', 'collide', True)
        )
        # If the coming object has a killer material, let them through
        self.killer_door_material.add_actions(
            conditions=(
                'they_have_material',
                self.killer_material
            ),
            actions=('modify_part_collision', 'collide', False),
       )
        
        self.killer_trap_object_material = bs.Material()
        # material that detects and activates stuf

        # By default, we only collide with floors.
        self.killer_trap_object_material.add_actions(
             ('modify_part_collision', 'collide', False)
        )
        self.killer_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().footing_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
            ),
        )
        self.killer_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                self.survivor_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', SurvivorDetectedMessage())
            ),
        )


        self.survivor_trap_object_material = bs.Material()
        # material that detects and activates stuf

        # By default, we only collide with floors.
        self.survivor_trap_object_material.add_actions(
             ('modify_part_collision', 'collide', False)
        )
        self.survivor_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().footing_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
            ),
        )
        self.survivor_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                self.killer_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', KillerDetectedMessage())
            ),
        )
        


class LostSession(bs.Session):
    """ the thing that handles everything ig"""

    use_team_colors = False
    use_team = False
    def __init__(self):
        depsets: list[bs.DependencySet] = []
        self.last_results = None
        super().__init__(depsets, team_names=None, team_colors=None, min_players=1, max_players=9, submit_score=False)

        self._timer_duration = 35.0
        self._max_timer_cap = 300.0 
        self._time_remaining = 0.0

        self._timer_node: bs.Node | None = None
        self._countdown_timer: bs.Timer | None = None

        # Start up the lobby activity.
        self.setactivity(bs.newactivity(Lobby))

        
    
    def add_time(self, seconds: float, flash_color: tuple[float, float, float] = (0, 1, 0)) -> None:
        if self._countdown_timer is None:
            return   # doesnt exist

        self._time_remaining = min(
            self._max_timer_cap, max(0.0, self._time_remaining + seconds)
        )

        # Update
        if self._timer_node:
            self._timer_node.text = f'{self.format_time(max(0, int(self._time_remaining)))}'

            self._timer_node.color = flash_color
            self._timer_node.scale = 1.8

            bs.timer(
                0.3,
                bs.WeakCall(
                    self._reset_timer_node_style
                ),
            )

    def _reset_timer_node_style(self) -> None:
        if self._timer_node:
            self._timer_node.color = (1, 1, 1)
            self._timer_node.scale = 1.5


    def start_timer(self, duration: float) -> None:
        if self._timer_node:
            self.stop_timer()
        self._time_remaining = duration

        self._timer_node = bs.newnode(
            'text',
            attrs={
                'v_attach': 'top',
                'h_attach': 'center',
                'h_align': 'center',
                'color': (1, 1, 1),
                'scale': 1.5,
                'position': (0, -60),
                'text': f'{self.format_time(int(self._time_remaining))}',
            },
        )

        self._countdown_timer = bs.Timer(
            1.0,
            bs.WeakCall(self._tick_timer),
            repeat=True,
        )

    def stop_timer(self) -> None:
        self._countdown_timer = None
        if self._timer_node:
            self._timer_node.delete()
            self._timer_node = None

    def _tick_timer(self) -> None:
        self._time_remaining -= 1.0

        if self._timer_node:
            self._timer_node.text = f'{self.format_time(max(0, int(self._time_remaining)))}'

        if self._time_remaining <= 0:
            self.stop_timer()
            self.timer_complete()

    def timer_complete(self) -> None:
        # tell the activity the timer has ended.
        self.getactivity().on_timer_complete()
    
    def format_time(self, sec):
        total_seconds = max(0, int(sec))
        minutes = total_seconds // 60
        remaining_seconds = total_seconds % 60

        return f"{minutes}:{remaining_seconds:02d}"
        
        
    
    def on_activity_end(self, activity, results):
        self.stop_timer()

        if results and not isinstance(activity, TransitionActivity):
            # Okay, gather results and transition ourselves.
            self.last_results = results
            self.setactivity(bs.newactivity(TransitionActivity))
        else:
            # Um.. Not a transition activity so try and do stuff based results
            if not self.last_results:
                raise Exception('no LostSession.last_results to go by')
        
            if self.last_results == 'roundstart':
                self.setactivity(bs.newactivity(ChooserActivity))
            elif isinstance(self.last_results, dict) and 'chosen_killer' in self.last_results:
                self.setactivity(bs.newactivity(Match, settings={'match_data': self.last_results}))
            elif isinstance(self.last_results, dict):
                self.setactivity(bs.newactivity(Lobby))

def assignspazinput(spaz: Spaz, player: bs.Player):
    player.resetinput()
    player.assigninput(
        bs.InputType.LEFT_RIGHT, spaz.on_move_left_right
    )
    player.assigninput(
        bs.InputType.UP_DOWN, spaz.on_move_up_down
    )
    player.assigninput(bs.InputType.RUN, spaz.on_run)
    player.assigninput(
        bs.InputType.BOMB_PRESS, spaz.on_bomb_press
    )
    player.assigninput(
        bs.InputType.BOMB_RELEASE, spaz.on_bomb_release
    )
    player.assigninput(
        bs.InputType.PICK_UP_PRESS, spaz.on_pickup_press
    )
    player.assigninput(
        bs.InputType.PICK_UP_RELEASE, spaz.on_pickup_release
    )
    player.assigninput(
        bs.InputType.PUNCH_PRESS, spaz.on_punch_press
    )
    player.assigninput(
        bs.InputType.PUNCH_RELEASE, spaz.on_punch_release
    )
    player.assigninput(
        bs.InputType.JUMP_PRESS, spaz.on_jump_press
    )
    player.assigninput(
        bs.InputType.JUMP_RELEASE, spaz.on_jump_release
    )


class Lobby(bs.Activity[bs.Player, bs.Team]):
    """ where the lobby takes place. """
    allow_pausing = True
    def __init__(self, settings):
        self.session: LostSession
        super().__init__(settings)
        
    
    def on_transition_in(self):
        super().on_transition_in()
        map = maps.ThePad
        map.preload()
        self.map = map()
    
    def on_begin(self):
        super().on_begin()
        # Start us a timer.
        bs.setmusic(bs.MusicType.LOBBY)
        self.session.start_timer(15)

        
        


    def on_player_join(self, player):
        self.spawn_player(player)
    
    def on_player_leave(self, player):
        player.actor.handlemessage(bs.DieMessage(how=bs.DeathType.LEFT_GAME))
        

    def spawn_player(self, player: bs.Player):
        # get a spawn position
        spawn = self.map.get_ffa_start_position([])
       
        spaz = Spaz(
            character=player.character,
            color=player.color,
            highlight=player.color,
            source_player=player,
            start_invincible=False,
        )
        spaz.handlemessage(bs.StandMessage(spawn))
        spaz.node.name = player.getname()
        spaz.node.name_color = player.color
        assignspazinput(spaz, player)
        player.actor = spaz

        
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.PlayerDiedMessage):
            self.spawn_player(msg.getplayer(bs.Player))
        else:
            return super().handlemessage(msg)

    # Every activity should have this.
    def on_timer_complete(self):
        if  len(self.players) <= 1:
            self.session.start_timer(35)
        else:
            self.end('roundstart')

class ChooserActivity(bs.Activity[bs.Player, bs.Team]):
    allow_pausing = True

    def __init__(self, settings):
        self.session: LostSession
        super().__init__(settings)
        self.killer_player: bs.Player | None = None
        self.selected_killer_id: str | None = None

    def on_transition_in(self):
        super().on_transition_in()
        from bascenev1lib.actor.background import Background
        Background().autoretain()

    def on_begin(self):
        super().on_begin()
        bs.setmusic(bs.MusicType.MENU)
        
        self.killer_player = random.choice(self.players)
        
        bs.broadcastmessage(
            f"{self.killer_player.getname()} is picking a Killer!",
            color=(1, 0.2, 0.2)
        )

        killer_keys = killers
        self.selected_killer_id = killer_keys[0] if killer_keys else 'Spaz'

        self.session.start_timer(15)

        if self.killer_player:
            self.killer_player.resetinput()
            self.killer_player.assigninput(bs.InputType.PUNCH_PRESS, self._cycle_killer_choice)

    def _cycle_killer_choice(self):
        killer_keys = killers
        if not killer_keys:
            return

        curr_index = killer_keys.index(self.selected_killer_id) if self.selected_killer_id in killer_keys else 0
        next_index = (curr_index + 1) % len(killer_keys)
        self.selected_killer_id = killer_keys[next_index]


        bs.broadcastmessage(
            f"Selected: {self.selected_killer_id}",
            color=(1, 0.8, 0.2)
        )

    def on_timer_complete(self):
        self.finish_selection()

    def finish_selection(self):
        results = {
            'killer_player': self.killer_player.sessionplayer,
            'chosen_killer': self.selected_killer_id,
        }
        self.end(results)

class Match(bs.Activity[bs.Player, bs.Team]):
    allow_pausing = False
    allow_mid_activity_joins = False

    def __init__(self, settings):
        self.session: LostSession
        super().__init__(settings)
        self.survivors: list[bs.Player] = set()
        self.killers: list[bs.Player] = set()
        self.ended = False
        self.lms = False
        self.killer_chase_theme_audio = None
        self.max_terror_radius = 40.0
        self.min_terror_radius = 2.5
        self._entries = {}
        self.match_data = settings.get('match_data', {})
        # Seriously eric.. no other way to make this better?
        self.killer_target = self.match_data.get('killer_player')

        
    def on_expire(self):
        super().on_expire()
        self.survivors = set()
        self.killers = set()
        self._ui_update_timer = None
        
        
    
    def on_transition_in(self):
        super().on_transition_in()
        mapss = [
            maps.StepRightUp
        ]
        map = random.choice(mapss)
        map.preload()
        self.map = map()
    
    def on_begin(self):
        super().on_begin()
        bs.setmusic(None)
        self.killer_player = next(
            (p for p in self.players if p.sessionplayer == self.killer_target), 
            None
        )

        self.killer_character = self.match_data.get('chosen_killer', 'Spaz')


        # No killer... End.
        if self.killer_player is None:
            self.end_survivors_won()
            return

        # Start us a timer.
        self.session.start_timer(210)
       
        for player in self.players:
            if player != self.killer_player:
                self.spawn_player(player, is_killer=False)
        self.spawn_player(self.killer_player, is_killer=True)

        self.chase_music = bs.newnode(
                 type='sound',
                 attrs={
                     'sound': self.killer_chase_theme_audio,
                     'positional': False,
                     'music': True,
                     'volume': 0.0,
                 },
            )
        bs.timer(0.1, self._music_tick, repeat=True)


        # just incase theres 1 guy
        bs.timer(0.5, self.check_lms)
       
    def set_player_dead(self, player: bs.Player) -> None:
        pass
    
    def _music_tick(self):
        if self.lms or not self.chase_music or not self.chase_music.exists():
            return

        min_distance = float('inf')
        in_active_chase = False

        # killer nod
        killer_nodes = []
        for killer in self.killers:
            if killer.actor and killer.actor.node and killer.actor.node.exists():
                killer_nodes.append(killer.actor)

        # check distances on survivors
        for survivor in self.survivors:
            if not survivor.actor or not survivor.actor.node or not survivor.actor.node.exists():
                continue

            survivor_pos = survivor.actor.node.position

            for k_spaz in killer_nodes:
                killer_pos = k_spaz.node.position

                if getattr(k_spaz, 'in_chase', False) or getattr(survivor.actor, 'in_chase', False):
                    in_active_chase = True

                dist = math.sqrt(
                    (survivor_pos[0] - killer_pos[0]) ** 2 +
                    (survivor_pos[1] - killer_pos[1]) ** 2 +
                    (survivor_pos[2] - killer_pos[2]) ** 2
                )
                if dist < min_distance:
                    min_distance = dist

        # Volume 
        if in_active_chase:
            target_volume = 1.0
        elif min_distance < self.max_terror_radius:
            clamped_dist = max(self.min_terror_radius, min_distance)
            target_volume = 1.0 - (
                (clamped_dist - self.min_terror_radius) / 
                (self.max_terror_radius - self.min_terror_radius)
            ) * 7
        else:
            target_volume = 0.0

        current_vol = self.chase_music.volume
        self.chase_music.volume = current_vol + (target_volume - current_vol) * 0.2


    def end_survivors_won(self):
        if self.ended:
            return
        self.end(
            {
                'whowon': 'survivors',
                'winners': [
                    [
                        player.getname(full=True, icon=True) for player in
                        self.survivors
                    ]
                ]
            }
        )
    def end_killer_won(self):
        if self.ended:
            return
        self.end(
            {
                'whowon': 'killer',
                'winners': [
                    [
                        player.getname(full=True, icon=True) for player in
                        self.killers
                    ]
                ]
            }
        )


        

        

    def spawn_player(self, player: bs.Player, is_killer=False):
        # get a spawn position
        if is_killer:
            self.killers.add(player)
            spawn = self.map.get_ffa_start_position(list(self.survivors))
            # For now hard code it into spaz, sigh..
            character = self.killer_character
            color = bs.app.classic.spaz_appearances[character].default_color
            highlight = bs.app.classic.spaz_appearances[character].default_highlight
            self.killer_chase_theme_audio = bs.getsound(bs.app.classic.spaz_appearances[character].moveset.chase_theme_dir)
        else:
            self.survivors.add(player)
            spawn = self.map.get_ffa_start_position([])
            character = player.character # Their survivor..
            color=player.color
            highlight=player.color
        
       
        spaz = Spaz(
            character=character,
            color=color,
            highlight=highlight,
            source_player=player,
            start_invincible=False,
            is_killer=is_killer
        )
        spaz.handlemessage(bs.StandMessage(spawn))
        spaz.node.name = player.getname()
        spaz.node.name_color = color
        spaz.node.is_area_of_interest = False
        assignspazinput(spaz, player)
        player.actor = spaz
    
    def check_lms(self):
        if len(self.survivors) == 1:
            self.start_lms()

    def on_player_leave(self, player):
        # same shenanegins as diemessag
        if player in self.survivors:
                self.survivors.remove(player)
                # Survivor, increase timer.
                self.session.add_time(35, flash_color=(1, 0, 0))
                self.set_player_dead(player)
                self.check_lms()
        if player in self.killers:
            self.killers.remove(player)
            
        # No survivors, killers win.
        if len(self.survivors) == 0:
            self.end_killer_won()
        # No killers, survivors win.
        if len(self.killers) == 0:
            self.end_survivors_won()
    def start_lms(self):
        if self.lms:
            return
        
        if self.chase_music:
            self.chase_music.delete()
            self.chase_music = None
        # Special guys
        if (
            list(self.survivors)[0].actor.character == 'Zoe' and
            list(self.killers)[0].actor.character == 'Spaz'
        ):
            self.session.start_timer(96)
            bs.setmusic(bs.MusicType.LMS4)  
        if (
            list(self.survivors)[0].actor.character == 'Mel' and
            list(self.killers)[0].actor.character == 'Snake Shadow'
        ):
            self.session.start_timer(86)
            bs.setmusic(bs.MusicType.LMS5)    
        else:

            self.session.start_timer(69)
            bs.setmusic(bs.MusicType.LMS1)
        self.lms = True
        for player in self.survivors:
            player.actor.node.is_area_of_interest = True
        for player in self.killers:
            player.actor.node.is_area_of_interest = True
        # Set the BG...
        self.map.background.color_texture = bs.gettexture('spectureBG')
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.PlayerDiedMessage):
            player = msg.getplayer(bs.Player)
            
            if player in self.survivors:
                AsymFactory.get().player_death_sound.play()
                self.survivors.remove(player)
                # Survivor, increase timer.
                self.session.add_time(35, flash_color=(1, 0, 0))
                self.set_player_dead(player)
                self.check_lms()
            if player in self.killers:
                self.killers.remove(player)
            
            # No survivors, killers win.
            if len(self.survivors) == 0:
                self.end_killer_won()
            # No killers, survivors win.
            if len(self.killers) == 0:
                self.end_survivors_won()
        else:
            return super().handlemessage(msg)

    # Every activity should have this.
    def on_timer_complete(self):
        self.end_survivors_won()
    
    def end(self, results = None, delay = 0, force = False):
        bs.setmusic(None)
        return super().end(results, delay, force)