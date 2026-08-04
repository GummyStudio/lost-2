"""Characters related description UIs."""
from __future__ import annotations
from typing import override
from enum import Enum
import random
import bauiv1 as bui
import babase as ba
import _babase as _ba
import bascenev1 as bs
from bauiv1lib.tabs import TabRow
import re
import ast
import textwrap

def parse_chunks(text):
    chunks = []
    last = 0

    for match in re.finditer(r"\{.*?\}", text):
        start, end = match.span()

        # Text before the tag
        if start > last:
            chunks.append(text[last:start])

        # The tag itself
        chunks.append(ast.literal_eval(match.group()))

        last = end

    # Remaining text
    if last < len(text):
        chunks.append(text[last:])

    return chunks

class CharactersWindow(bui.MainWindow):
    """A window providing help on how to play."""
    class TabID(Enum):
        """Our available tab types."""

        KILLERS = 'killers'
        SURVIVORS = 'survivors'

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        width = 500
        height = 700
        camera_pos = [
            0.5,
            5.7, 
            7.8,
        ]
        camera_target = [
            0.5, 
            4.5, 
            -5,
        ]
        activity = bs.get_foreground_host_activity()
        calls = [
            lambda: _ba.set_camera_manual(True),
            lambda: _ba.set_camera_position(*camera_pos),
            lambda: _ba.set_camera_target(*camera_target),
            lambda: activity._word_actors.clear()
        ]
        for call in calls:
            with activity.context:
                call()
        self._widgets_to_clear = []
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=None,
                stack_offset=(300, -35),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(10, height - 50),
            size=(40, 40),
            scale=1.25,
            button_type='backSmall',
            label=bui.charstr(bui.SpecialChar.BACK),
            extra_touch_border_scale=2.0,
            autoselect=True,
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(width - 30, height - 50),
            size=(40, 40),
            scale=1.25,
            button_type='square',
            label=bui.charstr(bui.SpecialChar.PLAY_BUTTON),
            extra_touch_border_scale=2.0,
            on_activate_call=self.start_playtest,
        )
        tabrow_width = width * 0.9
        tabdefs = [
            (
                self.TabID.SURVIVORS,
                "Survivors",
            ),
            (
                self.TabID.KILLERS,
                "Killers",
            ),
        ]
        h = width * 0.5
        default_tab_color = (0.34, 0.29, 0.40)
        lit_tab_color = ba.Vec3(default_tab_color) + ba.Vec3(0.4)
        self._tab_row = TabRow(
            self._root_widget,
            tabdefs,
            pos=(h - tabrow_width * 0.5, height - 10),
            size=(tabrow_width, 50),
            on_select_call=self._set_tab,
            lit_color=lit_tab_color,
            unlit_color=default_tab_color,
        )
        index_buttons_h = width * 0.5
        index_buttons_spacing = width - 220
        index_buttons_v = height * 0.5
        index_buttons_size = (60, 60)
        index_buttons_scale = 1.2
        index_buttons_color = (0.39, 0.34, 0.46)
        index_buttons_textcolor = (1, 1, 1)
        self._left_index_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                (
                    index_buttons_h 
                    - index_buttons_spacing
                    - index_buttons_size[1]
                    * 0.5
                    * index_buttons_scale
                ), 
                index_buttons_v
            ),
            size=index_buttons_size,
            scale=index_buttons_scale,
            label=bui.charstr(bui.SpecialChar.LEFT_ARROW),
            on_activate_call=self._prev,
            color=index_buttons_color,
            textcolor=index_buttons_textcolor,
            button_type='square',
        )
        self._right_index_btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                (
                    index_buttons_h 
                    + index_buttons_spacing
                    - index_buttons_size[1]
                    * 0.5
                    * index_buttons_scale
                ), 
                index_buttons_v
            ),
            size=index_buttons_size,
            scale=index_buttons_scale,
            label=bui.charstr(bui.SpecialChar.RIGHT_ARROW),
            on_activate_call=self._next,
            color=index_buttons_color,
            textcolor=index_buttons_textcolor,
            button_type='square',
        )
        v = height - 10
        self._char_name_text = bui.textwidget(
            parent=self._root_widget,
            text='',
            h_align='center',
            position=(h, v),
            size=(0, 0),
            scale=1.1,
            maxwidth=width - 50,
        )
        v -= 40
        
        scroll_width = width - 50
        # c_height = 35 * len(lines)
        c_height = 700
        scroll_height = 350
        scroll_bottom = v
        scroll_h = h - scroll_width * 0.5
        c_width = scroll_width - 5
        scroll_v = scroll_bottom - scroll_height
        self._desc_scrollwidget = scrw = bui.scrollwidget(
            parent=self._root_widget,
            position=(scroll_h, scroll_v),
            size=(scroll_width, scroll_height),
        )
        self._desc_subcontainer = cnt = bui.containerwidget(
            parent=scrw,
            position=(
                scroll_width * 0.5,
                scroll_height * 0.5,
            ),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True,
        )
        self._character_index = 0
        self._desc_scroll_height = scroll_height
        self._desc_scroll_width = scroll_width
        # set the first tab so we get
        # the ui goin
        self._set_tab(tabdefs[0][0])
    
    def _update_ui(self):
        for widget in self._widgets_to_clear:
            widget.delete()
        self._widgets_to_clear.clear()
        character = self._characters_list[
            self._character_index
        ]
        character = bs.app.classic.spaz_appearances[character]
        activity = bs.get_foreground_host_activity()
        with activity.context:
            activity.spawn_character_preview(character.name)
        bui.textwidget(
            edit=self._char_name_text,
            text=character.name,
        )
        moveset = character.moveset
        raw_text = moveset.description
        for child in self._desc_subcontainer.get_children():
            child.delete()
        if isinstance(raw_text, list):
            text_w_tags = raw_text
        else:
            text_w_tags = parse_chunks(raw_text)
        total_c_height = 5
        text_maxwidth = 37
        text_height = 31
        # Calculate total height.
        for chunk in text_w_tags:
            if isinstance(chunk, (str, bs.Lstr)):
                text = textwrap.fill(
                    chunk, 
                    width=text_maxwidth,
                    replace_whitespace=False
                )
                lines = text.splitlines()
                total_c_height += text_height * len(lines)
            elif isinstance(chunk, dict):
                if chunk.get('type') == 'image':
                    total_c_height += chunk.get('size')[1] + 5
        total_c_height += 5
        bui.containerwidget(
            edit=self._desc_subcontainer,
            size=(
                self._desc_scroll_width - 5, 
                total_c_height
            )
        )
        v = total_c_height - 10
        def_text_color = text_color = (0.9, 0.9, 0.9)
        # Generate some UI widget types
        # based on the description.
        for chunk in text_w_tags:
            if isinstance(chunk, (str, bs.Lstr)):
                text = textwrap.fill(
                    chunk, 
                    width=text_maxwidth,
                    replace_whitespace=False
                )
                lines = text.splitlines()
                bui.textwidget(
                    parent=self._desc_subcontainer,
                    text=text,
                    size=(0, 0),
                    position=(15, v),
                    color=text_color,
                )
                v -= text_height * len(lines)
            
            elif isinstance(chunk, dict):
                # If chunk is a 'edit text' type chunk,
                # get it's necessary attrs and set those
                if chunk.get('type') == 'edit_text':
                    if chunk.get('color'):
                        chunk_color = chunk.get('color')
                        if chunk_color == 'default':
                            chunk_color = def_text_color
                        text_color = chunk_color
                # If chunk is image, then make
                # a image widget
                if chunk.get('type') == 'image':
                    size = chunk.get('size')
                    bui.imagewidget(
                        parent=self._desc_subcontainer,
                        position=(self._desc_scroll_width * 0.5 - size[0] * 0.5, v - size[1]),
                        texture=bui.gettexture(chunk.get('texture')),
                        size=size,
                    )
                    v -= size[1] + 5
                # If chunk is separator, pass
                # (used to separate text colors and such)
                if chunk.get('type') == 'separator':
                    pass
        v = self._desc_scroll_height - 60
        # FIXME: should gen this better
        max_abilities_num = 3
        icons = [
            getattr(
                character.moveset, 
                f'ability{i + 1}_icon', 
                None
            )
            for i in range(max_abilities_num)
        ]
        abilities_nums = [
            icons.index(i) + 1
            for i in icons
            if i is not None
            and i != ''
        ]
        ability_scale = 1.05
        ability_x_offs = 30
        button_size = (32, 32)
        for i in abilities_nums:
            description = getattr(character.moveset, f'ability{i}_description', 'INVALID ABILITY')
            icon = getattr(character.moveset, f'ability{i}_icon', 'X')
            cooldown = getattr(character.moveset, f'ability{i}_cooldown', '')
            description = textwrap.fill(
                description, 
                width=text_maxwidth / ability_scale,
                replace_whitespace=False
            )
            icon_widget = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    ability_x_offs * ability_scale - 5, 
                    v - button_size[1] * ability_scale
                ),
                size=button_size,
                label=icon,
                scale=ability_scale,
                button_type='square',
                color=(0.37, 0.39, 0.49),
                textcolor=(1, 1, 1),
                on_activate_call=bs.WeakCall(self._do_ability, i),
            )
            cooldown_widget = bui.textwidget(
                parent=self._root_widget,
                position=(ability_x_offs + button_size[0] * 0.5, v + 10),
                size=(0, 0),
                text=f'{cooldown}s',
                color=(0.8, 0.8, 0.8),
                scale=ability_scale - 0.4,
                h_align='center',
            )
            description_widget = bui.textwidget(
                parent=self._root_widget,
                text=description,
                size=(0, 0),
                position=(ability_x_offs + 38 * ability_scale, v),
                scale=ability_scale,
            )
            self._widgets_to_clear.append(icon_widget)
            self._widgets_to_clear.append(description_widget)
            self._widgets_to_clear.append(cooldown_widget)
            lines = description.splitlines()
            v -= text_height * len(lines) * ability_scale + 15
        
    def _add_to_character_index(self, value: int):
        self._character_index = (
            self._character_index + value
        ) % len(self._characters_list)
        self._update_ui()
    
    def _prev(self):
        self._add_to_character_index(-1)
    def _next(self):
        self._add_to_character_index(1)
    
    def _do_ability(self, num: int):
        activity = bs.get_foreground_host_activity()
        with activity.context:
            activity._preview_spaz_do_ability(num)
    
    def _set_tab(self, tab_id: TabID):
        self._character_index = 0
        lists_dict = {
            self.TabID.KILLERS: bui.app.classic.killers,
            self.TabID.SURVIVORS: bui.app.classic.survivors,
        }
        self._characters_list = lists_dict.get(tab_id)
        self._tab_row.update_appearance(tab_id)
        self._update_ui()
    
    def start_playtest(self):
        ba.pushcall(lambda: _ba.set_camera_manual(False))
        activity = bs.get_foreground_host_activity()
        character = self._characters_list[
            self._character_index
        ]
        character = bs.app.classic.spaz_appearances[character]
        with activity.context:
            activity.spawn_character_preview(None)
            activity.start_playtest(character.name)
        bui.screenmessage('Join the game to continue...')
        self.close()
    
    @override
    def main_window_back(self):
        activity = bs.get_foreground_host_activity()
        with activity.context:
            activity.spawn_character_preview(None)
            activity._remake_title()
        ba.pushcall(lambda: _ba.set_camera_manual(False))
        super().main_window_back()
    
    def close(self):
        bui.containerwidget(
            edit=self._root_widget,
            transition='out_right',
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