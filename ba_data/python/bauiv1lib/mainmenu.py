# Released under the MIT License. See LICENSE for details.
#
"""Implements the main menu window."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Callable


class MainMenuWindow(bui.MainWindow):
    """The main menu window."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        bui.set_analytics_screen('Main Menu')

        uiscale = bui.app.ui_v1.uiscale

        # Make a vanilla container; we'll modify it to our needs in
        # refresh.
        super().__init__(
            root_widget=bui.containerwidget(
                toolbar_visibility=('no_menu_minimal')
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        # Grab this stuff in case it changes.
        # self._is_demo = bui.app.env.demo
        # self._is_arcade = bui.app.env.arcade

        self._tdelay = 0.0
        self._t_delay_inc = 0.02
        self._t_delay_play = 1.7
        self._use_autoselect = True
        self._button_width = 200.0
        self._button_height = 45.0
        self._width = 100.0
        self._height = 100.0
        self._demo_menu_button: bui.Widget | None = None
        self._gather_button: bui.Widget | None = None
        self._play_button: bui.Widget | None = None
        self._watch_button: bui.Widget | None = None
        self._how_to_play_button: bui.Widget | None = None
        self._credits_button: bui.Widget | None = None

        self._refresh()

        self._restore_state()

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use; avoids hitches (called in bg thread)."""
        # pylint: disable=cyclic-import
        import bauiv1lib.getremote as _unused
        import bauiv1lib.confirm as _unused2
        import bauiv1lib.account.settings as _unused5
        import bauiv1lib.store.browser as _unused6
        import bauiv1lib.credits as _unused7
        import bauiv1lib.help as _unused8
        import bauiv1lib.settings.allsettings as _unused9
        import bauiv1lib.gather as _unused10
        import bauiv1lib.watch as _unused11

    def get_play_button(self) -> bui.Widget | None:
        """Return the play button."""
        return self._play_button

    def _refresh(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        classic = bui.app.classic
        assert classic is not None

        # Clear everything that was there.
        children = self._root_widget.get_children()
        for child in children:
            child.delete()

        self._tdelay = 0.0
        self._t_delay_inc = 0.0
        self._t_delay_play = 0.0
        self._button_width = 200.0
        self._button_height = 45.0

        self._r = 'mainMenu'

        app = bui.app
        assert app.classic is not None
        uiscale = app.ui_v1.uiscale

        if not classic.did_menu_intro:
            self._tdelay = 1.6
            self._t_delay_inc = 0.03
            classic.did_menu_intro = True

        td1 = 2
        td2 = 1
        td3 = 0
        td4 = -1
        td5 = -2

        self._width = 400.0
        self._height = 200.0

        play_button_width = self._button_width * 0.65
        play_button_height = self._button_height * 1.1
        play_button_scale = 1.7
        hspace = 20.0
        side_button_width = self._button_width * 0.4
        side_button_height = side_button_width
        side_button_scale = 0.95
        side_button_y_offs = 5.0
        hspace2 = 15.0
        side_button_2_width = self._button_width * 1.0
        side_button_2_height = side_button_2_width * 0.3
        side_button_2_y_offs = 10.0
        side_button_2_scale = 0.5

        root_widget_scale = 1.2
        button_y_offs = -100

        bui.containerwidget(
            edit=self._root_widget,
            size=(self._width, self._height),
            background=False,
            scale=root_widget_scale,
        )

        # Version/copyright info.
        thistdelay = self._tdelay + td3 * self._t_delay_inc

        # Gather button
        h = self._width * 0.5
        h = (
            self._width * 0.5
            - play_button_width * play_button_scale * 0.5
            - hspace
            - side_button_width * side_button_scale * 0.5
        )
        v = button_y_offs

        thistdelay = self._tdelay + td2 * self._t_delay_inc
        self._gather_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - side_button_width * side_button_scale * 0.5, v),
            size=(side_button_width, side_button_height),
            scale=side_button_scale,
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=thistdelay,
            on_activate_call=self._gather_press,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(h, v + side_button_height * side_button_scale * 0.25),
            size=(0, 0),
            scale=0.75,
            transition_delay=thistdelay,
            draw_controller=self._gather_button,
            color=(0.75, 1.0, 0.7),
            maxwidth=side_button_width * side_button_scale * 0.8,
            text=bui.Lstr(resource='gatherWindow.titleText'),
            h_align='center',
            v_align='center',
        )
        icon_size = side_button_width * side_button_scale * 0.63
        bui.imagewidget(
            parent=self._root_widget,
            size=(icon_size, icon_size),
            draw_controller=self._gather_button,
            transition_delay=thistdelay,
            position=(
                h - 0.5 * icon_size,
                v
                + 0.65 * side_button_height * side_button_scale
                - 0.5 * icon_size,
            ),
            texture=bui.gettexture('usersButton'),
        )
        thistdelay = self._tdelay + td1 * self._t_delay_inc

        h -= (
            side_button_width * side_button_scale * 0.5
            + hspace2
            + side_button_2_width * side_button_2_scale
        )
        v = button_y_offs + side_button_2_y_offs

        self._how_to_play_button = None
      

        # Play button.
        h = self._width * 0.5
        v = button_y_offs
        assert play_button_width is not None
        assert play_button_height is not None
        thistdelay = self._tdelay + td3 * self._t_delay_inc
        self._play_button = start_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - play_button_width * 0.5 * play_button_scale, v),
            size=(play_button_width, play_button_height),
            autoselect=self._use_autoselect,
            scale=play_button_scale,
            text_res_scale=2.0,
            label=bui.Lstr(resource='playText'),
            transition_delay=thistdelay,
            on_activate_call=self._play_press,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=start_button,
            selected_child=start_button,
        )

        # self._tdelay += self._t_delay_inc

        h = (
            self._width * 0.5
            + play_button_width * play_button_scale * 0.5
            + hspace
            + side_button_width * side_button_scale * 0.5
        )
        v = button_y_offs + side_button_y_offs
        thistdelay = self._tdelay + td4 * self._t_delay_inc
        self._watch_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - side_button_width * side_button_scale * 0.5, v),
            size=(side_button_width, side_button_height),
            scale=side_button_scale,
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=thistdelay,
            on_activate_call=self._watch_press,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(h, v + side_button_height * side_button_scale * 0.25),
            size=(0, 0),
            scale=0.75,
            transition_delay=thistdelay,
            color=(0.75, 1.0, 0.7),
            draw_controller=self._watch_button,
            maxwidth=side_button_width * side_button_scale * 0.8,
            text=bui.Lstr(resource='watchWindow.titleText'),
            h_align='center',
            v_align='center',
        )
        icon_size = side_button_width * side_button_scale * 0.63
        bui.imagewidget(
            parent=self._root_widget,
            size=(icon_size, icon_size),
            draw_controller=self._watch_button,
            transition_delay=thistdelay,
            position=(
                h - 0.5 * icon_size,
                v
                + 0.65 * side_button_height * side_button_scale
                - 0.5 * icon_size,
            ),
            texture=bui.gettexture('tv'),
        )

        # Credits button.
        thistdelay = self._tdelay + td5 * self._t_delay_inc

        v -= 50
        h = self._width * 0.5
        self._credits_button = None
        # I LOVE YOU FOUNTAIN SEALERS
        this_buttons = [
            {
                'label': bui.Lstr(resource=f'{self._r}.settingsText'),
                'callback': self._settings,
            },
            {
                'label': bui.Lstr(resource=f'{self._r}.howToPlayText'),
                'callback': self._howtoplay,
            },
            {
                'label': bui.Lstr(resource=f'{self._r}.quitText'),
                'callback': self._quit,
                'back_btn': True,
            },
        ]
        # Regular buttons.
        reg_button_size = (130, 40)
        reg_button_scale = 0.9
        spacing = reg_button_size[0] + 8
        text_color = (1, 1, 1)
        default_hoffs = -65
        hoffs = default_hoffs * len(this_buttons)
        for btn in this_buttons:
            if not btn.get('callback'):
                raise RuntimeError('Made a menu button without callback')
            text_color = btn.get('color')
            if text_color:
                text_color = (
                    text_color[0] + 0.4,
                    text_color[1] + 0.4,
                    text_color[2] + 0.4,
                )
            buttonw = bui.buttonwidget(
                parent=self._root_widget,
                position=(h + hoffs + (spacing * this_buttons.index(btn)), v),
                autoselect=self._use_autoselect,
                size=reg_button_size,
                scale=reg_button_scale,
                label=btn.get('label'),
                on_activate_call=btn.get('callback'),
                color=btn.get('color'),
                textcolor=text_color,
                transition_delay=thistdelay,
            )
            if btn.get('back_btn'):
                bui.containerwidget(
                    edit=self._root_widget,
                    cancel_button=buttonw,
                )

        v -= 5
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, v),
            size=(0, 0),
            scale=0.7,
            flatness=1.0,
            color=(1, 1, 1, 0.3),
            text=(
                f'{app.env.engine_version}'
                f' build {app.env.engine_build_number}.'
                f' Copyright 2025 Eric Froemling.'
            ),
            h_align='center',
            v_align='top',
            # transition_delay=self._t_delay_play,
            transition_delay=thistdelay,
        )
                
    def _quit(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import QuitWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        # Note: Normally we should go through bui.quit(confirm=True) but
        # invoking the window directly lets us scale it up from the
        # button.
        QuitWindow()

    def _credits(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.credits import CreditsWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            CreditsWindow(origin_widget=self._credits_button),
        )

    def _howtoplay(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.help import HelpWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            HelpWindow(origin_widget=self._how_to_play_button),
        )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._play_button:
                sel_name = 'Start'
            elif sel == self._gather_button:
                sel_name = 'Gather'
            elif sel == self._watch_button:
                sel_name = 'Watch'
            elif sel == self._how_to_play_button:
                sel_name = 'HowToPlay'
            elif sel == self._credits_button:
                sel_name = 'Credits'
            elif sel == self._demo_menu_button:
                sel_name = 'DemoMenu'
            else:
                sel_name = 'Start'
            bui.app.ui_v1.window_states[type(self)] = {'sel_name': sel_name}
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:

            sel: bui.Widget | None

            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                'sel_name'
            )
            assert isinstance(sel_name, (str, type(None)))
            if sel_name is None:
                sel_name = 'Start'
            if sel_name == 'HowToPlay':
                sel = self._how_to_play_button
            elif sel_name == 'Gather':
                sel = self._gather_button
            elif sel_name == 'Watch':
                sel = self._watch_button
            elif sel_name == 'Credits':
                sel = self._credits_button
            elif sel_name == 'Quit':
                sel = self._quit_button
            elif sel_name == 'DemoMenu':
                sel = self._demo_menu_button
            else:
                sel = self._play_button
            if sel is not None:
                bui.containerwidget(edit=self._root_widget, selected_child=sel)

        except Exception:
            logging.exception('Error restoring state for %s.', self)

    def _gather_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.gather import GatherWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            GatherWindow(origin_widget=self._gather_button)
        )

    def _watch_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.watch import WatchWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            WatchWindow(origin_widget=self._watch_button),
        )
    
    def _settings(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.allsettings import AllSettingsWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            AllSettingsWindow(origin_widget=self._gather_button)
        )

    def _play_press(self) -> None:
        # pylint: disable=cyclic-import
        from lost.session import LostSession

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return
        
        bs.new_host_session(LostSession)
        
