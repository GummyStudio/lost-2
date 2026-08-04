"""Provides help related ui."""
from __future__ import annotations
from typing import override
import random
import bauiv1 as bui


class HelpWindow(bui.MainWindow):
    """A window providing help on how to play."""

    def __init__(
        self,
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        width = 700
        height = 500
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=None,
                scale=1.1,
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(10, height - 50),
            size=(40, 40),
            scale=1.25,
            label='X',
            extra_touch_border_scale=2.0,
            autoselect=True,
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        h = width * 0.5 + 10
        v = height - 20
        text = (
            "Lost is a game where you and your friends\n"
            "get put together against a single person attempting\n"
            "to kill you, where THEY have the upper advantage.\n"
            "Both teamwork and your abillities is of the essence\n"
            "to survive, so that's where this somewhat handy guide\n"
            "can help you out with."
        )
        bui.textwidget(
            parent=self._root_widget,
            text=text,
            size=(0, 0),
            h_align='center',
            position=(h, v),
            maxwidth=width - 90
        )
        lines = text.splitlines()
        img_scale = 0.6
        img_size = (512 * img_scale, 256 * img_scale)
        v -= 35 * len(lines)
        v -= img_size[1] - 20
        bui.imagewidget(
            parent=self._root_widget,
            texture=bui.gettexture('helpwindow_art'),
            position=(h - img_size[0] * 0.5, v),
            size=img_size,
        )
        v -= img_size[1] * 0.5 - 20
        
        # Regular buttons.
        reg_button_size = (width - 60, 60)
        reg_button_scale = 0.9
        text_color = (1, 1, 1)
        default_hoffs = -65
        this_buttons = [
            {
                'label': 'Characters',
                'callback': self._open_chars,
            },
        ]
        for btn in this_buttons:
            if not btn.get('callback'):
                raise RuntimeError('Made a menu button without callback')
            bui.buttonwidget(
                parent=self._root_widget,
                position=(h - reg_button_size[0] * 0.5 * reg_button_scale, v),
                size=reg_button_size,
                scale=reg_button_scale,
                label=btn.get('label'),
                on_activate_call=btn.get('callback'),
                textcolor=text_color,
            )
            v -= reg_button_size[1]
    
    def _open_chars(self):
        # pylint: disable=cyclic-import
        from bauiv1lib.characters import CharactersWindow

        # no-op if we're not currently in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            CharactersWindow(transition='in_right')
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
