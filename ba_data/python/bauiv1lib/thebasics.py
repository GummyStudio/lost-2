"""Provides help related ui."""
from __future__ import annotations
from typing import override
import random
import bauiv1 as bui

class TheBasicsWindow(bui.MainWindow):
    """A window providing help on how to play."""

    def __init__(
        self,
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        width = 800
        height = 500
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=None,
                scale=1.2,
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        h = width * 0.5
        scroll_h = 30
        scroll_v = 30
        scroll_width = width - 50
        scroll_height = height - 80
        c_width = scroll_width - 5
        bui.textwidget(
            parent=self._root_widget,
            text="The Basics",
            size=(0, 0),
            h_align='center',
            position=(width * 0.5, height - 10),
            color=bui.app.ui_v1.title_color,
        )
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(10, height - 50),
            size=(40, 40),
            scale=1.25,
            label=bui.charstr(bui.SpecialChar.BACK),
            extra_touch_border_scale=2.0,
            autoselect=True,
            on_activate_call=self.main_window_back,
            button_type='backSmall',
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        self._scrollwidget = scrw = bui.scrollwidget(
            parent=self._root_widget,
            position=(scroll_h, scroll_v),
            size=(scroll_width, scroll_height),
        )
        all_texts = [
            (   
                ("As the survivor, you have to\n"
                "avoid the killer and try to\n"
                "help your teammates if possible."),
                "zoeIcon",
            ),
            (
                ("As the killer, kill EVERY survivor.\n"
                "Leave none of them alive. That's about it."),
                "neoSpazIcon",
            ),
        ]
        max_height = 128
        c_height = max_height * len(all_texts)
        c_height += 710
        self._subcontainer = bui.containerwidget(
            parent=scrw,
            position=(
                scroll_width * 0.5,
                scroll_height * 0.5,
            ),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True,
            selectable=False,
        )
        img_size = (max_height, max_height)
        h_offs = -160
        h = c_width * 0.5
        text_h = h + h_offs
        v = c_height - 80
        image_h = 0
        image_spacing = img_size[0]
        for text, texture in all_texts:
            image_h = text_h
            image_h = image_h - image_spacing - 20
            bui.textwidget(
                parent=self._subcontainer,
                text=text,
                size=(0, 0),
                h_align='left',
                v_align='center',
                position=(text_h, v),
                max_height=max_height,
                maxwidth=c_width * 0.9 - img_size[0],
                scale=1.05,
            )
            bui.imagewidget(
                parent=self._subcontainer,
                texture=bui.gettexture(texture),
                position=(image_h, v - img_size[1] * 0.5),
                size=img_size,
            )
            v -= max_height + 5
        v += 50
        text = (
            "As for the survivors, they are split into\n"
            "3 types of classes that each behave in their own way;"
        )
        lines = text.splitlines()
        bui.textwidget(
            parent=self._subcontainer,
            text=text,
            size=(0, 0),
            h_align='center',
            v_align='top',
            position=(h, v),
            maxwidth=c_width - 30,
        )
        v -= 36 * len(lines)
        classes = {
            "Sentinels": (
                "These survivors will stun the killer\n"
                "VERY easily, or at the very least put up\n"
                "a good fight against them."
            ),
            "Support": (
                "They will help their team by providing\n"
                "them by healing them or boosting a stat of theirs."
            ),
            "Survivalist": (
                "These are mostly solo-type guys\n"
                "who can't really help their team.\n"
                "They have abilities that are made\n"
                "for avoiding the killer."
            ),
        }
        for sclass in classes.keys():
            bui.textwidget(
                parent=self._subcontainer,
                text=sclass,
                size=(0, 0),
                h_align='center',
                v_align='top',
                position=(h, v),
                maxwidth=c_width - 30,
                color=(0.8, 0.9, 1),
            )
            v -= 30
            text = classes.get(sclass)
            bui.textwidget(
                parent=self._subcontainer,
                text=text,
                size=(0, 0),
                h_align='center',
                v_align='top',
                position=(h, v),
                maxwidth=c_width - 30,
                color=(0.9, 0.9, 1),
            )
            lines = text.splitlines()
            v -= 36 * len(lines)
            
        text = (
            "Every single one of these characters' abilities\n"
            "are triggered via the 3 face buttons.\n"
            "If you do need to learn about specific abilities,\n"
            "read about them or playtest them\n"
            "in the characters section.\n"
        )
        bui.textwidget(
            parent=self._subcontainer,
            text=text,
            size=(0, 0),
            h_align='center',
            v_align='top',
            position=(h, v),
            maxwidth=c_width - 30,
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
