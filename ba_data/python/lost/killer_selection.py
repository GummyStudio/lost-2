"""Class for a killer selection screen."""
from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs

from lost.functions import choppify
from lost.survivoricon import SurvivorIcon

if TYPE_CHECKING:
    from lost.session import LostSession


class ChooserCard(bs.Actor):
    """A card that represents a character."""

    def __init__(
        self,
        position: tuple[float, float],
        size: tuple[float, float],
        character: str = 'Spaz',
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
        scale: int = 1.1,
    ):
        super().__init__()
        self.character = character
        appearance = bs.app.classic.spaz_appearances[character]
        texture = bs.gettexture(f'cards/{appearance.card_texture}')
        margin = 40 * scale
        half_height = size[1] * 0.5
        top = half_height + margin
        bottom = -(half_height + margin)

        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': texture,
                'position': position,
                'scale': size,
                'color': color,
            },
        )

        # character name above the card
        self.text_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': appearance.name,
                'scale': scale + 0.1,
                'h_align': 'center',
            },
        )
        mnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (0, top, 0), 'operation': 'add'},
        )
        self.node.connectattr('position', mnode, 'input2')
        self.node.connectattr('opacity', self.text_node, 'opacity')
        self.node.connectattr('color', self.text_node, 'color')
        self.node.connectattr('front', self.text_node, 'front')
        mnode.connectattr('output', self.text_node, 'position')

        # oneliner text below the card
        self.oneliner_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': appearance.oneliner,
                'scale': scale,
                'h_align': 'center',
            },
        )
        mnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (0, bottom, 0), 'operation': 'add'},
        )
        self.node.connectattr('position', mnode, 'input2')
        self.node.connectattr('opacity', self.oneliner_node, 'opacity')
        self.node.connectattr('color', self.oneliner_node, 'color')
        self.node.connectattr('front', self.oneliner_node, 'front')
        mnode.connectattr('output', self.oneliner_node, 'position')

    def set_character(self, character: str) -> None:
        """Swap this card to display a different character."""
        self.character = character
        self._update()

    def _update(self) -> None:
        appearance = bs.app.classic.spaz_appearances[self.character]
        texture = bs.gettexture(f'cards/{appearance.card_texture}')
        self.node.texture = texture
        self.text_node.text = appearance.name
        self.oneliner_node.text = appearance.oneliner

    def exists(self) -> bool:
        return bool(self.node)

    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            return super().handlemessage(msg)
        return None


class KillerSelection(bs.Actor):
    """Per-player killer selection actor
    with it's own input handling."""

    def __init__(
        self,
        source_player: bs.Player,
        position: tuple[float, float],
        scale: float,
    ):
        super().__init__()
        self._killer_index = len(bs.app.classic.killers) // 2
        self._move_sound = bs.getsound('deek')
        self._done_sound = bs.getsound('punch01')
        self._source_player = source_player
        self._ready = False
        self._cards: list[ChooserCard] = []

        card_spacing = 60 * scale
        card_amount = 3
        self._card_amount = card_amount
        total_width = (card_amount - 1) * card_spacing
        x = -total_width * 0.5
        x += position[0]
        y = position[1]
        name = source_player.getname()
        color = source_player.color
        name_y = 130 * scale
        self._name_text = bs.newnode(
            'text',
            attrs={
                'text': name,
                'scale': scale * 0.7,
                'h_align': 'center',
                'position': (position[0], y + name_y),
                'color': bs.safecolor(color),
            },
        )
        self._ready_text = bs.newnode(
            'text',
            attrs={
                'text': '- READY -',
                'scale': scale * 0.5,
                'h_align': 'center',
                'position': (position[0], y + name_y - 20),
                'color': (0.1, 0.9, 0.2),
                'opacity': 0,
            },
        )

        killer_keys = bs.app.classic.killers
        center_i = card_amount // 2
        for i in range(card_amount):
            card_size = (128 * scale, 128 * scale)
            color = (1.0, 1.0, 1.0)
            front = True
            card_text_scale = scale * 0.5 + 0.3
            if i != center_i:
                card_size = (card_size[0] * 0.8, card_size[1] * 0.8)
                color = (0.8, 0.8, 0.8)
                front = False
                card_text_scale = scale * 0.5

            offset = i - center_i
            key_index = (self._killer_index + offset) % len(killer_keys)

            card = ChooserCard(
                character=killer_keys[key_index],
                size=card_size,
                position=(x, y),
                color=color,
                scale=card_text_scale,
            )
            card.node.front = front
            self._cards.append(card)
            x += card_spacing

        # nice littel arrows
        arrow_spacing = card_spacing * scale
        arrow_scale = scale - 0.3
        arrow_color = (1, 0.3, 0.3)
        arrow_x, arrow_y = position

        right_arrow = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('arrow_down'),
                'scale': (64 * arrow_scale, 32 * arrow_scale),
                'rotate': 90,
                'color': arrow_color,
            },
        )
        keys = {
            0: (arrow_x + arrow_spacing + 10, arrow_y),
            0.5: (arrow_x + arrow_spacing, arrow_y),
            1: (arrow_x + arrow_spacing + 10, arrow_y),
        }
        keys = choppify(keys, fps=10)
        bs.animate_array(right_arrow, 'position', 2, keys, loop=True)

        left_arrow = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('arrow_down'),
                'scale': (64 * arrow_scale, 32 * arrow_scale),
                'rotate': -90,
                'color': arrow_color,
            },
        )
        keys = {
            0: (arrow_x - arrow_spacing - 10, arrow_y),
            0.5: (arrow_x - arrow_spacing, arrow_y),
            1: (arrow_x - arrow_spacing - 10, arrow_y),
        }
        keys = choppify(keys, fps=10)
        bs.animate_array(left_arrow, 'position', 2, keys, loop=True)

    def _update_cards(self) -> None:
        """Re-sync each card's displayed character with the current index."""
        killer_keys = bs.app.classic.killers
        center_i = self._card_amount // 2
        for i, card in enumerate(self._cards):
            offset = i - center_i
            key_index = (self._killer_index + offset) % len(killer_keys)
            card.set_character(killer_keys[key_index])

    def _done(self) -> None:
        self._done_sound.play()

    def ready(self) -> None:
        self._ready = not self._ready
        if self._ready:
            self._done()
        self._ready_text.opacity = 1 if self._ready else 0
        self.getactivity().on_player_ready(self._source_player, self._ready)

    def _next_killer(self) -> None:
        if self._ready:
            return
        killer_keys = bs.app.classic.killers
        self._killer_index = (self._killer_index + 1) % len(killer_keys)
        self._update_cards()
        killer = killer_keys[self._killer_index]
        self.getactivity()._on_killer_change(self._source_player, killer)
        self._move_sound.play()

    def _prev_killer(self) -> None:
        if self._ready:
            return
        killer_keys = bs.app.classic.killers
        self._killer_index = (self._killer_index - 1) % len(killer_keys)
        self._update_cards()
        killer = killer_keys[self._killer_index]
        self.getactivity()._on_killer_change(self._source_player, killer)
        self._move_sound.play()

    def connect_controls(self) -> None:
        player = self._source_player
        player.assigninput(bs.InputType.LEFT_PRESS, self._prev_killer)
        player.assigninput(bs.InputType.RIGHT_PRESS, self._next_killer)
        ready_btns = (
            bs.InputType.PUNCH_PRESS,
            bs.InputType.JUMP_PRESS,
            bs.InputType.BOMB_PRESS,
        )
        player.assigninput(ready_btns, self.ready)


class ChooserActivity(bs.Activity[bs.Player, bs.Team]):
    """Activity where each player 
    picks their killer character."""

    allow_pausing = True

    def __init__(self, settings):
        self.session: LostSession
        super().__init__(settings)
        self.killers = settings['killer_players']
        self.survivors = list(
            p for p in self.session.sessionplayers
            if p not in self.killers
        )
        self._player_characters: dict[bs.Player, str] = {}
        self._ready_players: dict[bs.Player, bool] = {}
        self._survivor_icons: list[Survivoricon] = []

    def on_player_ready(self, player: bs.Player, state: bool) -> None:
        self._ready_players[player] = state
        if all(self._ready_players.values()):
            self.session.stop_timer()
            self.on_timer_complete()

    def on_transition_in(self) -> None:
        super().on_transition_in()
        from bascenev1lib.actor.background import Background
        Background().autoretain()

    def on_begin(self) -> None:
        super().on_begin()
        bs.setmusic(bs.MusicType.KILLER_SELECT)

        killer_keys = bs.app.classic.killers
        self.selected_killer_id = killer_keys[0]
        self.cards: dict[bs.Player, KillerSelection] = {}
        # Remove a player if they don't exist
        for player in self.killers:
            if not player.exists():
                self.killers.remove(player)
            else:
                # Otherwise, add them to some dicts
                # per default
                self._ready_players[player] = False
                self._player_characters[player] = 'Spaz'

        x = 0
        y = 270
        scale = 6 / int((len(self.killers)))
        self._spacing = spacing = 256 + 30 * scale

        if len(self.killers) == 1:
            names = self.killers[0].getname(full=True)
            suffix = ''
        else:
            names = ', '.join(p.getname() for p in self.killers)
            suffix = 'S'

        # self._players_text = bs.newnode(
            # 'text',
            # attrs={
                # 'scale': 1.2,
                # 'text': names,
                # 'h_align': 'center',
                # 'position': (x, y),
            # },
        # )
        y -= 30
        self._pick_text = bs.newnode(
            'text',
            attrs={
                'scale': 1.2,
                'text': f'- PICK YOUR CARD{suffix} -',
                'h_align': 'center',
                'position': (x, y),
            },
        )
        y -= 280
        self.session.start_timer(15)

        total_width = len(self.killers) * spacing
        x = -total_width * 0.5 + spacing * 0.5
        for player in self.killers:
            controller = KillerSelection(
                source_player=player,
                position=(x, y),
                scale=scale * 0.4,
            ).autoretain()
            controller.connect_controls()
            self.cards[player] = controller
            x += spacing
        y -= 260
        self._survivors_text = bs.newnode(
            'text',
            attrs={
                'scale': 1.2,
                'text': f'- TO KILL THESE -',
                'h_align': 'center',
                'position': (0, y),
            },
        )
        y = 30
        scale = 0.8
        icon_size = (64 * scale, 64 * scale)
        spacing = icon_size[0] + 25
        total_width = (len(self.survivors)) * spacing
        x = -total_width * 0.5
        for survivor in self.survivors:
            icon = SurvivorIcon(
                position=(x, y),
                scale=scale,
                source_player=survivor.activityplayer,
            )
            self._survivor_icons.append(icon)
            x += spacing

    def _on_killer_change(self, player: bs.Player, killer: str) -> None:
        self._player_characters[player] = killer

    def on_timer_complete(self) -> None:
        self._survivor_icons.clear()
        self.finish_selection()

    def finish_selection(self) -> None:
        results = {
            'killer_players': self.killers,
            'chosen_killers': self._player_characters,
        }
        self.end(results)