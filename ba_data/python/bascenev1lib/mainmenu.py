# Released under the MIT License. See LICENSE for details.
#
"""Session and Activity for displaying the main menu bg."""

from __future__ import annotations

import time
import random
import weakref
from typing import TYPE_CHECKING, override

from bacommon.locale import LocaleResolved
import bascenev1 as bs
import bauiv1 as bui
from bascenev1 import _map

from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.maps import ThePad
from lost.lost import AsymFactory, assignspazinput

if TYPE_CHECKING:
    from typing import Any

    import bacommon.bs


class MainMenuActivity(bs.Activity[bs.Player, bs.Team]):
    """Activity showing the rotating main menu bg stuff."""

    _stdassets = bs.Dependency(bs.AssetPackage, 'stdassets@1')

    _did_initial_transition = False

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._logo_node: bs.Node | None = None
        self._custom_logo_tex_name: str | None = None
        self._word_actors: list[bs.Actor] = []
        self.my_name: bs.NodeActor | None = None
        self._host_is_navigating_text: bs.NodeActor | None = None
        self.version: bs.NodeActor | None = None
        self.beta_info: bs.NodeActor | None = None
        self.beta_info_2: bs.NodeActor | None = None
        self.bottom: bs.NodeActor | None = None
        self.vr_bottom_fill: bs.NodeActor | None = None
        self.vr_top_fill: bs.NodeActor | None = None
        self.terrain: bs.NodeActor | None = None
        self.trees: bs.NodeActor | None = None
        self.bgterrain: bs.NodeActor | None = None
        self._ts = 0.86
        self._language: str | None = None
        self._update_timer: bs.Timer | None = None
        self._news: NewsDisplay | None = None
        self._attract_mode_timer: bs.Timer | None = None
        self._logo_rotate_timer: bs.Timer | None = None
        self._preview_spaz: Spaz | None = None
        self._map_type = _map.get_map_class('The Pad')
        self._map_type.preload()
        self._killer_dummy: Spaz | None = None
        self._survivor_dummy: Spaz | None = None
        self._killed_dummies = False
        self._chosen_player_char = 'Zoe'
    
    def on_player_join(self, player):
        self.spawn_player(player)
    
    def on_player_leave(self, player):
        player.actor.handlemessage(bs.DieMessage(how=bs.DeathType.LEFT_GAME))
    
    def spawn_player(self, player: bs.Player):
        # get a spawn position
        spawn = self.map.get_ffa_start_position([])
        char = self._chosen_player_char
        spaz = Spaz(
            character=char,
            color=player.color,
            highlight=player.highlight,
            source_player=player,
            start_invincible=False,
            is_killer=char in bs.app.classic.killers,
        )
        spaz.handlemessage(bs.StandMessage(spawn))
        spaz.node.name = player.getname()
        spaz.node.name_color = player.color
        player.actor = spaz
        assignspazinput(spaz, player)

    
    def _preview_spaz_random_action(self):
        if (
            not self._preview_spaz 
            or not self._preview_spaz.node
        ):
            return
        # Alright, let's get some actions here
        spaz = self._preview_spaz
        node = spaz.node
        # Include some actions that happen randomly for funsies.
        rare_actions = [
            # explode into a bunch of pieces
            [
                lambda: spaz.impulse(y=3.5),
                lambda: bs.timer(0.05, lambda: setattr(node, 'shattered', 2)),
                lambda: bs.getsound('lego_break').play(),
            ]
        ]
        actions = [
            # wave
            [
                lambda: node.handlemessage('celebrate_r', 700),
                lambda: node.handlemessage('jump_sound'),
            ],
            # jump
            lambda: spaz.on_jump_press(),
            # punch
            [
                lambda: setattr(node, 'punch_pressed', True),
                lambda: bs.timer(0, lambda: setattr(node, 'punch_pressed', False)),
            ],
            # hurt thingy
            [
                lambda: node.handlemessage('knockout', 100),
                lambda: node.handlemessage('hurt_sound'),
                lambda: spaz.impulse(x=-0.5, y=2,),
            ],
        ]
        if random.random() < 0.01:
            action = random.choice(rare_actions)
        else:
            action = random.choice(actions)
        if isinstance(action, list):
            for i in action:
                i()
        else:
            action()
    
    def _preview_spaz_do_ability(self, num: int):
        if (
            not self._preview_spaz 
            or not self._preview_spaz.node
        ):
            return
        spaz = self._preview_spaz
        func = getattr(spaz.moveset, f'do_ability{num}', None)
        if not func:
            return
        func()
    
    def spawn_character_preview(self, character: str | None):
        raw_char_str = character
        if character:
            character = bs.app.classic.spaz_appearances[character]
        # Kill the existing previous Spaz
        if self._preview_spaz:
            self._preview_spaz.handlemessage(bs.DieMessage(True))
        if not character:
            return
        # Get their color, but if it doesn't exist
        # then make up a random one
        color = character.default_color or (
            random.random(), 
            random.random(), 
            random.random()
        )
        highlight = character.default_highlight or (
            random.random(), 
            random.random(), 
            random.random()
        )
        # Spawn a nice little Spaz.
        self._preview_spaz = spaz = Spaz(
            character=raw_char_str,
            color=color,
            highlight=highlight,
            start_invincible=False,
            is_killer=character.name in bs.app.classic.killers,
        )
        # Tell it to stand somewhere we can see it.
        spawn_pos = (
            -0.7,
            4.5, 
            3.1,
        )
        spaz.handlemessage(bs.StandMessage(spawn_pos))
        # Schedule a timer for it to do some random action..
        # (class timer so no repeats happen)
        self._preview_spaz_random_action_timer = bs.Timer(0.9, 
            bs.WeakCall(self._preview_spaz_random_action)
        )
    
    def kill_playtest_dummies(self):
        if self._killer_dummy:
            self._killer_dummy.handlemessage(bs.DieMessage(True))
        if self._survivor_dummy:
            self._survivor_dummy.handlemessage(bs.DieMessage(True))
        self._killed_dummies = True
    
    def spawn_playtest_dummies(self):
        if self._killed_dummies:
            return
        spawn_pos = (0, 3.5, -4)
        spacing = 0.8
        apps = bs.app.classic.spaz_appearances
        killer_char = random.choice(bs.app.classic.killers)
        killer_char = apps[killer_char]
        survivor_char = random.choice(bs.app.classic.survivors)
        survivor_char = apps[survivor_char]
        if not self._killer_dummy:
            color = killer_char.default_color or (
                random.random(), 
                random.random(), 
                random.random()
            )
            highlight = killer_char.default_highlight or (
                random.random(), 
                random.random(), 
                random.random()
            )
            spaz = self._killer_dummy = Spaz(
                character=killer_char.name,
                color=color,
                highlight=highlight,
                start_invincible=False,
                is_killer=True,
            )
            spaz.handlemessage(
                bs.StandMessage(
                    (spawn_pos[0] + spacing, spawn_pos[1], spawn_pos[2])
                )
            )
            asymf = AsymFactory.get()
            spaz.node.name = killer_char.name
            spaz.node.name_color = color
            spaz.node.add_death_action(bs.WeakCall(self.spawn_playtest_dummies))
            spaz.node.is_area_of_interest = True
            
        if not self._survivor_dummy:
            color = survivor_char.default_color or (
                random.random(), 
                random.random(), 
                random.random()
            )
            highlight = survivor_char.default_highlight or (
                random.random(), 
                random.random(), 
                random.random()
            )
            spaz = self._survivor_dummy = Spaz(
                character=survivor_char.name,
                color=color,
                highlight=highlight,
                start_invincible=False,
                is_killer=False,
            )
            spaz.handlemessage(
                bs.StandMessage(
                    (spawn_pos[0] - spacing, spawn_pos[1], spawn_pos[2])
                )
            )
            asymf = AsymFactory.get()
            spaz.node.name = survivor_char.name
            spaz.node.name_color = color
            spaz.node.add_death_action(bs.WeakCall(self.spawn_playtest_dummies))
            spaz.node.is_area_of_interest = True
    
    def start_playtest(self, character: str):
        self._chosen_player_char = character
        self.spawn_playtest_dummies()
        self.globalsnode.camera_mode = 'follow'

    @property
    def map(self) -> _map.Map:
        """The map being used for this game.

        Raises a bascenev1.MapNotFoundError if the map does not currently
        exist.
        """
        if self._map is None:
            raise babase.MapNotFoundError
        return self._map

    @override
    def on_transition_in(self) -> None:
        # pylint: disable=too-many-locals
        super().on_transition_in()
        random.seed(123)
        app = bs.app
        env = app.env
        assert app.classic is not None

        plus = bs.app.plus
        assert plus is not None

        # Throw up some text that only clients can see so they know that
        # the host is navigating menus while they're just staring at an
        # empty-ish screen.
        tval = bs.Lstr(
            resource='hostIsNavigatingMenusText',
            subs=[('${HOST}', plus.get_v1_account_display_string())],
        )
        self._host_is_navigating_text = bs.NodeActor(
            bs.newnode(
                'text',
                attrs={
                    'text': tval,
                    'client_only': True,
                    'position': (0, -200),
                    'flatness': 1.0,
                    'h_align': 'center',
                },
            )
        )
        
        # Make our map.
        self._map = self._map_type()
        
        gnode = self.globalsnode
        gnode.camera_mode = 'rotate'

        tint = (1.0, 0.6, 0.6)
        gnode.tint = tint
        gnode.ambient_color = (1.06, 1.04, 1.03)
        gnode.vignette_outer = (0.45, 0.55, 0.54)
        gnode.vignette_inner = (0.99, 0.98, 0.98)
        self._remake_title()

        # Hopefully this won't hitch but lets space these out anyway.
        bs.add_clean_frame_callback(bs.WeakCall(self._start_preloads))

        random.seed()

        # Need to update this for toolbar mode; currenly doesn't fit.
        # if bool(False):
        #     if not (env.demo or env.arcade):
        #         self._news = NewsDisplay(self)

        self._attract_mode_timer = bs.Timer(
            3.12, self._update_attract_mode, repeat=True
        )

        app.classic.invoke_main_menu_ui()

    def _remake_title(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        app = bs.app
        assert app.classic is not None
        y = 20
        base_scale = 1.2
        self._word_actors = []
        base_delay = 0.8
        delay = base_delay
        delay_inc = 0.02
        # disable for the creepypasta ish logo
        # enable if you want. i dunno :3
        cool_logo = bs.app.config.get('LOSTCOOLERFUCKINMENU', False)
        # Come on faster after the first time.
        if self._did_initial_transition:
            base_delay = 0.0
            delay = base_delay
            delay_inc = 0.02
        if cool_logo:
            base_scale += 0.7
            base_x = -115
            x = base_x - 20
            spacing = 100
            y_extra = -30
            xv1 = x
            delay1 = delay
            for shadow in (True, False):
                x = xv1
                delay = delay1
                delay += delay_inc
                delay += delay_inc
                self._make_word(
                    'L',
                    x,
                    y + y_extra,
                    scale=base_scale,
                    delay=delay,
                    vr_depth_offset=14,
                    shadow=shadow,
                )
                x += spacing * 0.85
                delay += delay_inc
                x += spacing * 0.85
                delay += delay_inc
                self._make_word(
                    's',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    vr_depth_offset=7,
                    shadow=shadow,
                )
                x += spacing * 0.5
                delay += delay_inc
                self._make_word(
                    't',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    shadow=shadow,
                )
            self._make_logo(
                xv1 + (spacing * 0.95),
                y + y_extra + 170,
                delay=delay,
                scale=base_scale - 1.35,
            )
            two_x = 0
            two_y = y + y_extra - 10
            image2 = self._shaky_effect = bs.NodeActor(
                bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('scorchBig'),
                        'position': (two_x, two_y),
                        'opacity': 0,
                    }
                )
            )
            image = self._two_image = bs.NodeActor(
                bs.newnode(
                    'image',
                    attrs={
                        'texture': bs.gettexture('lost2'),
                    }
                )
            )
            self._word_actors.append(image)
            self._word_actors.append(image2)
            hit_time = 0.1
            bs.animate_array(
                image.node,
                'scale', 2,
                {
                    0: (1024 * base_scale, 1024 * base_scale),
                    hit_time: (64 * base_scale, 64 * base_scale),
                    hit_time + 0.2: (128 * base_scale, 128 * base_scale),
                },
                offset=delay,
            )
            bs.animate(
                image.node,
                'opacity',
                {
                    0: 0,
                    hit_time - 0.1: 0,
                    hit_time: 1,
                },
                offset=delay,
            )
            def make_shaky_effect():
                if self._did_initial_transition:
                    return
                cmb = bs.newnode('combine', owner=image2.node, attrs={'size': 2})
                cmb.connectattr('output', image2.node, 'scale')
                end_time = 0.3
                keys = {
                    0: 0,
                    end_time: 1024,
                }
                bs.animate(
                    image2.node,
                    'opacity',
                    {
                        0: 0,
                        0.01: 0.7,
                        end_time - 0.1: 0.7,
                        end_time: 0,
                    }
                )
                        
                bs.animate(cmb, 'input0', keys)
                bs.animate(cmb, 'input1', keys)
            
            cmb = bs.newnode('combine', owner=image.node, attrs={'size': 2})
            cmb.connectattr('output', image.node, 'position')
            keys = {}
            time_v = 0.0
            jitter_scale = 5 
            key_steps = 15
            speed = 0.07
            x = two_x
            y = two_y

            # Gen some random keys for that stop-motion-y look
            for _i in range(key_steps):
                keys[time_v] = (
                    x + (random.random() - 0.5) * 0.7 * jitter_scale
                )
                time_v += random.random() * speed
            bs.animate(cmb, 'input0', keys, loop=True)
            keys = {}
            time_v = 0.0
            for _i in range(key_steps):
                keys[time_v * self._ts] = (
                    y + (random.random() - 0.5) * 0.7 * jitter_scale
                )
                time_v += random.random() * speed
            bs.animate(cmb, 'input1', keys, loop=True)
            bs.timer(delay + hit_time, make_shaky_effect)
        else:
            base_x = -90
            x = base_x - 20
            spacing = 55 * base_scale
            y_extra = -20
            xv1 = x
            delay1 = delay
            for shadow in (True, False):
                x = xv1
                delay = delay1
                delay += delay_inc
                delay += delay_inc
                self._make_word(
                    'L',
                    x,
                    y + y_extra,
                    scale=base_scale,
                    delay=delay,
                    vr_depth_offset=14,
                    shadow=shadow,
                )
                x += spacing * 0.9
                delay += delay_inc
                self._make_word(
                    'o',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    shadow=shadow,
                )
                x += spacing * 0.9
                delay += delay_inc
                self._make_word(
                    's',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    vr_depth_offset=7,
                    shadow=shadow,
                )
                x += spacing * 0.9
                delay += delay_inc
                self._make_word(
                    't',
                    x,
                    y + y_extra,
                    delay=delay,
                    scale=base_scale,
                    shadow=shadow,
                )
                   

    def _make_word(
        self,
        word: str,
        x: float,
        y: float,
        *,
        scale: float = 1.0,
        delay: float = 0.0,
        vr_depth_offset: float = 0.0,
        shadow: bool = False,
    ) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        if shadow:
            word_obj = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'position': (x, y),
                        'big': True,
                        'color': (0.0, 0.0, 0.2, 0.08),
                        'tilt_translate': 0.09,
                        'opacity_scales_shadow': False,
                        'shadow': 0.2,
                        'vr_depth': -130,
                        'v_align': 'center',
                        'project_scale': 0.97 * scale,
                        'scale': 1.0,
                        'text': word,
                    },
                )
            )
            self._word_actors.append(word_obj)
        else:
            word_obj = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'position': (x, y),
                        'big': True,
                        'color': (1.2, 1.15, 1.15, 1.0),
                        'tilt_translate': 0.11,
                        'shadow': 0.2,
                        'vr_depth': -40 + vr_depth_offset,
                        'v_align': 'center',
                        'project_scale': scale,
                        'scale': 1.0,
                        'text': word,
                    },
                )
            )
            self._word_actors.append(word_obj)

        # Add a bit of stop-motion-y jitter to the logo (unless we're in
        # VR mode in which case its best to leave things still).
        if not bs.app.env.vr:
            cmb: bs.Node | None
            cmb2: bs.Node | None
            if not shadow:
                cmb = bs.newnode(
                    'combine', owner=word_obj.node, attrs={'size': 2}
                )
            else:
                cmb = None
            if shadow:
                cmb2 = bs.newnode(
                    'combine', owner=word_obj.node, attrs={'size': 2}
                )
            else:
                cmb2 = None
            if not shadow:
                assert cmb and word_obj.node
                cmb.connectattr('output', word_obj.node, 'position')
            if shadow:
                assert cmb2 and word_obj.node
                cmb2.connectattr('output', word_obj.node, 'position')
            keys = {}
            keys2 = {}
            time_v = 0.0
            for _i in range(10):
                val = x + (random.random() - 0.5) * 0.8
                val2 = x + (random.random() - 0.5) * 0.8
                keys[time_v * self._ts] = val
                keys2[time_v * self._ts] = val2 + 5
                time_v += random.random() * 0.1
            if cmb is not None:
                bs.animate(cmb, 'input0', keys, loop=True)
            if cmb2 is not None:
                bs.animate(cmb2, 'input0', keys2, loop=True)
            keys = {}
            keys2 = {}
            time_v = 0
            for _i in range(10):
                val = y + (random.random() - 0.5) * 0.8
                val2 = y + (random.random() - 0.5) * 0.8
                keys[time_v * self._ts] = val
                keys2[time_v * self._ts] = val2 - 9
                time_v += random.random() * 0.1
            if cmb is not None:
                bs.animate(cmb, 'input1', keys, loop=True)
            if cmb2 is not None:
                bs.animate(cmb2, 'input1', keys2, loop=True)

        if not shadow:
            assert word_obj.node
            bs.animate(
                word_obj.node,
                'project_scale',
                {delay: 0.0, delay + 0.1: scale * 1.1, delay + 0.2: scale},
            )
        else:
            assert word_obj.node
            bs.animate(
                word_obj.node,
                'project_scale',
                {delay: 0.0, delay + 0.1: scale * 1.1, delay + 0.2: scale},
            )

    def _get_custom_logo_tex_name(self) -> str | None:
        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_misc_read_val('easter', False):
            return 'logoEaster'
        return None

    # Pop the logo and menu in.
    def _make_logo(
        self,
        x: float,
        y: float,
        scale: float,
        delay: float,
        *,
        custom_texture: str | None = None,
        jitter_scale: float = 1.0,
        rotate: float = 0.0,
        vr_depth_offset: float = 0.0,
    ) -> None:
        # pylint: disable=too-many-locals
        if custom_texture is None:
            custom_texture = self._get_custom_logo_tex_name()
        self._custom_logo_tex_name = custom_texture
        ltex = bs.gettexture(
            custom_texture if custom_texture is not None else 'logo'
        )
        logo_attrs = {
            'position': (x, y),
            'texture': ltex,
            'vr_depth': -10 + vr_depth_offset,
            'rotate': rotate,
            'attach': 'center',
            'tilt_translate': 0.21,
            'absolute_scale': True,
        }
        logo = bs.NodeActor(bs.newnode('image', attrs=logo_attrs))
        self._logo_node = logo.node
        self._word_actors.append(logo)

        # Add a bit of stop-motion-y jitter to the logo (unless we're in
        # VR mode in which case its best to leave things still).
        assert logo.node

        def jitter() -> None:
            if not bs.app.env.vr:
                cmb = bs.newnode('combine', owner=logo.node, attrs={'size': 2})
                cmb.connectattr('output', logo.node, 'position')
                keys = {}
                time_v = 0.0

                # Gen some random keys for that stop-motion-y look
                for _i in range(10):
                    keys[time_v] = (
                        x + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.1
                bs.animate(cmb, 'input0', keys, loop=True)
                keys = {}
                time_v = 0.0
                for _i in range(10):
                    keys[time_v * self._ts] = (
                        y + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.1
                bs.animate(cmb, 'input1', keys, loop=True)

        # Do a fun spinny animation on the logo the first time in.
        if (
            custom_texture is None
            and bs.app.classic is not None
            and not self._did_initial_transition
        ):
            jitter()
            cmb = bs.newnode('combine', owner=logo.node, attrs={'size': 2})

            delay = 0.0
            keys = {
                delay: 5000.0 * scale,
                delay + 0.4: 530.0 * scale,
                delay + 0.45: 620.0 * scale,
                delay + 0.5: 590.0 * scale,
                delay + 0.55: 605.0 * scale,
                delay + 0.6: 600.0 * scale,
            }
            bs.animate(cmb, 'input0', keys)
            bs.animate(cmb, 'input1', keys)
            cmb.connectattr('output', logo.node, 'scale')

            keys = {
                delay: 100.0,
                delay + 0.4: 370.0,
                delay + 0.45: 357.0,
                delay + 0.5: 360.0,
            }
            bs.animate(logo.node, 'rotate', keys)
            type(self)._did_initial_transition = True
        else:
            # For all other cases do a simple scale up animation.
            jitter()
            cmb = bs.newnode('combine', owner=logo.node, attrs={'size': 2})

            keys = {
                delay: 0.0,
                delay + 0.1: 700.0 * scale,
                delay + 0.2: 600.0 * scale,
            }
            bs.animate(cmb, 'input0', keys)
            bs.animate(cmb, 'input1', keys)
            cmb.connectattr('output', logo.node, 'scale')

    def _start_preloads(self) -> None:
        # FIXME: The func that calls us back doesn't save/restore state
        #  or check for a dead activity so we have to do that ourself.
        if self.expired:
            return
        with self.context:
            _preload1()

        def _start_menu_music() -> None:
            assert bs.app.classic is not None
            bs.setmusic(bs.MusicType.MENU)

        bui.apptimer(0.5, _start_menu_music)

    def _update_attract_mode(self) -> None:
        if bui.app.classic is None:
            return

        if not bui.app.config.resolve('Show Demos When Idle'):
            return

        threshold = 20.0

        # If we're idle *and* have been in this activity for that long,
        # flip over to our cpu demo.
        if bui.get_input_idle_time() > threshold and bs.time() > threshold:
            bui.app.classic.run_stress_test(
                playlist_type='Random',
                playlist_name='__default__',
                player_count=8,
                round_duration=20,
                attract_mode=True,
            )


class NewsDisplay:
    """Wrangles news display."""

    def __init__(self, activity: bs.Activity):
        self._valid = True
        self._message_duration = 10.0
        self._message_spacing = 2.0
        self._text: bs.NodeActor | None = None
        self._activity = weakref.ref(activity)
        self._phrases: list[str] = []
        self._used_phrases: list[str] = []
        self._phrase_change_timer: bs.Timer | None = None

        # If we're signed in, fetch news immediately. Otherwise wait
        # until we are signed in.
        self._fetch_timer: bs.Timer | None = bs.Timer(
            1.0, bs.WeakCall(self._try_fetching_news), repeat=True
        )
        self._try_fetching_news()

    # We now want to wait until we're signed in before fetching news.
    def _try_fetching_news(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() == 'signed_in':
            self._fetch_news()
            self._fetch_timer = None

    def _fetch_news(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        assert bs.app.classic is not None
        bs.app.classic.main_menu_last_news_fetch_time = time.time()

        # UPDATE - We now just pull news from MRVs.
        news = plus.get_v1_account_misc_read_val('n', None)
        if news is not None:
            self._got_news(news)

    def _change_phrase(self) -> None:
        from bascenev1lib.actor.text import Text

        app = bs.app
        assert app.classic is not None

        # If our news is way out of date, lets re-request it; otherwise,
        # rotate our phrase.
        assert app.classic.main_menu_last_news_fetch_time is not None
        if time.time() - app.classic.main_menu_last_news_fetch_time > 600.0:
            self._fetch_news()
            self._text = None
        else:
            if self._text is not None:
                if not self._phrases:
                    for phr in self._used_phrases:
                        self._phrases.insert(0, phr)
                val = self._phrases.pop()
                if val == '__ACH__':
                    vrmode = app.env.vr
                    Text(
                        bs.Lstr(resource='nextAchievementsText'),
                        color=((1, 1, 1, 1) if vrmode else (0.95, 0.9, 1, 0.4)),
                        host_only=True,
                        maxwidth=200,
                        position=(-300, -35),
                        h_align=Text.HAlign.RIGHT,
                        transition=Text.Transition.FADE_IN,
                        scale=0.9 if vrmode else 0.7,
                        flatness=1.0 if vrmode else 0.6,
                        shadow=1.0 if vrmode else 0.5,
                        h_attach=Text.HAttach.CENTER,
                        v_attach=Text.VAttach.TOP,
                        transition_delay=1.0,
                        transition_out_delay=self._message_duration,
                    ).autoretain()
                    achs = [
                        a
                        for a in app.classic.ach.achievements
                        if not a.complete
                    ]
                    if achs:
                        ach = achs.pop(random.randrange(min(4, len(achs))))
                        ach.create_display(
                            -180,
                            -35,
                            1.0,
                            outdelay=self._message_duration,
                            style='news',
                        )
                    if achs:
                        ach = achs.pop(random.randrange(min(8, len(achs))))
                        ach.create_display(
                            180,
                            -35,
                            1.25,
                            outdelay=self._message_duration,
                            style='news',
                        )
                else:
                    spc = self._message_spacing
                    keys = {
                        spc: 0.0,
                        spc + 1.0: 1.0,
                        spc + self._message_duration - 1.0: 1.0,
                        spc + self._message_duration: 0.0,
                    }
                    assert self._text.node
                    bs.animate(self._text.node, 'opacity', keys)
                    # {k: v
                    #  for k, v in list(keys.items())})
                    self._text.node.text = val

    def _got_news(self, news: str) -> None:
        # Run this stuff in the context of our activity since we need to
        # make nodes and stuff.. should fix the serverget call so it.
        activity = self._activity()
        if activity is None or activity.expired:
            return
        with activity.context:
            self._phrases.clear()

            # Show upcoming achievements in non-vr versions (currently
            # too hard to read in vr).
            self._used_phrases = (['__ACH__'] if not bs.app.env.vr else []) + [
                s for s in news.split('<br>\n') if s != ''
            ]
            self._phrase_change_timer = bs.Timer(
                (self._message_duration + self._message_spacing),
                bs.WeakCall(self._change_phrase),
                repeat=True,
            )

            assert bs.app.classic is not None
            scl = (
                1.2
                if (bs.app.ui_v1.uiscale is bs.UIScale.SMALL or bs.app.env.vr)
                else 0.8
            )

            color2 = (1, 1, 1, 1) if bs.app.env.vr else (0.7, 0.65, 0.75, 1.0)
            shadow = 1.0 if bs.app.env.vr else 0.4
            self._text = bs.NodeActor(
                bs.newnode(
                    'text',
                    attrs={
                        'v_attach': 'top',
                        'h_attach': 'center',
                        'h_align': 'center',
                        'vr_depth': -20,
                        'shadow': shadow,
                        'flatness': 0.8,
                        'v_align': 'top',
                        'color': color2,
                        'scale': scl,
                        'maxwidth': 900.0 / scl,
                        'position': (0, -10),
                    },
                )
            )
            self._change_phrase()


def _preload1() -> None:
    """Pre-load some assets a second or two into the main menu.

    Helps avoid hitches later on.
    """
    for mname in [
        'plasticEyesTransparent',
        'playerLineup1Transparent',
        'playerLineup2Transparent',
        'playerLineup3Transparent',
        'playerLineup4Transparent',
        'angryComputerTransparent',
        'scrollWidgetShort',
        'windowBGBlotch',
    ]:
        bs.getmesh(mname)
    for tname in ['playerLineup', 'lock']:
        bs.gettexture(tname)
    for tex in [
        'iconRunaround',
        'iconOnslaught',
        'medalComplete',
        'medalBronze',
        'medalSilver',
        'medalGold',
        'characterIconMask',
    ]:
        bs.gettexture(tex)
    bs.gettexture('bg')
    from bascenev1lib.actor.powerupbox import PowerupBoxFactory

    PowerupBoxFactory.get()
    bui.apptimer(0.1, _preload2)


def _preload2() -> None:
    # FIXME: Could integrate these loads with the classes that use them
    #  so they don't have to redundantly call the load
    #  (even if the actual result is cached).
    for mname in ['powerup', 'powerupSimple']:
        bs.getmesh(mname)
    for tname in [
        'powerupBomb',
        'powerupSpeed',
        'powerupPunch',
        'powerupIceBombs',
        'powerupStickyBombs',
        'powerupShield',
        'powerupImpactBombs',
        'powerupHealth',
    ]:
        bs.gettexture(tname)
    for sname in [
        'powerup01',
        'boxDrop',
        'boxingBell',
        'scoreHit01',
        'scoreHit02',
        'dripity',
        'spawn',
        'gong',
    ]:
        bs.getsound(sname)
    from bascenev1lib.actor.bomb import BombFactory

    BombFactory.get()
    bui.apptimer(0.1, _preload3)


def _preload3() -> None:
    from bascenev1lib.actor.spazfactory import SpazFactory

    for mname in ['bomb', 'bombSticky', 'impactBomb']:
        bs.getmesh(mname)
    for tname in [
        'bombColor',
        'bombColorIce',
        'bombStickyColor',
        'impactBombColor',
        'impactBombColorLit',
    ]:
        bs.gettexture(tname)
    for sname in ['freeze', 'fuse01', 'activateBeep', 'warnBeep']:
        bs.getsound(sname)
    SpazFactory.get()
    bui.apptimer(0.2, _preload4)


def _preload4() -> None:
    for tname in ['bar', 'meter', 'null', 'flagColor', 'achievementOutline']:
        bs.gettexture(tname)
    for mname in ['frameInset', 'meterTransparent', 'achievementOutline']:
        bs.getmesh(mname)
    for sname in ['metalHit', 'metalSkid', 'refWhistle', 'achievement']:
        bs.getsound(sname)
    from bascenev1lib.actor.flag import FlagFactory

    FlagFactory.get()


class MainMenuSession(bs.Session):
    """Session that runs the main menu environment."""

    def __init__(self) -> None:
        # Gather dependencies we'll need (just our activity).
        self._activity_deps = bs.DependencySet(bs.Dependency(MainMenuActivity))

        super().__init__([self._activity_deps])
        self._locked = False
        self.setactivity(bs.newactivity(MainMenuActivity))

    @override
    def on_activity_end(self, activity: bs.Activity, results: Any) -> None:
        if self._locked:
            bui.unlock_all_input()

        # Any ending activity leads us into the main menu one.
        self.setactivity(bs.newactivity(MainMenuActivity))

    # @override
    # def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # # Reject all player requests.
        # return False
