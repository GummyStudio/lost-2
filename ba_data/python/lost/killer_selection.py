"""Class for a killer selection screen."""
import bascenev1 as bs
import random
from lost.functions import choppify

class ChooserCard(bs.Actor):
    def __init__(
        self, 
        position: tuple[float],
        size: tuple[float],
        character: str = 'Spaz',
    ):
        super().__init__()
        apps = bs.app.classic.spaz_appearances
        character = apps[character]
        texture = bs.gettexture(f'cards/{character.card_texture}')
        y_spacing = -210
        top = size[1] + y_spacing
        bottom = -size[1] - y_spacing
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': texture,
                'position': position,
                'scale': size,
            }
        )
        node = self.text_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': character.name,
                'scale': 1.3,
                'h_align': 'center',
            }
        )
        mnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (0, top, 0), 'operation': 'add'},
        )
        self.node.connectattr('position', mnode, 'input2')
        self.node.connectattr('opacity', node, 'opacity')
        self.node.connectattr('color', node, 'color')
        self.node.connectattr('front', node, 'front')
        mnode.connectattr('output', node, 'position')
        node = self.oneliner_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': character.oneliner,
                'scale': 1.1,
                'h_align': 'center',
            }
        )
        mnode = bs.newnode(
            'math',
            owner=self.node,
            attrs={'input1': (0, bottom, 0), 'operation': 'add'},
        )
        self.node.connectattr('position', mnode, 'input2')
        self.node.connectattr('opacity', node, 'opacity')
        self.node.connectattr('color', node, 'color')
        self.node.connectattr('front', node, 'front')
        mnode.connectattr('output', node, 'position')
        self.combine = None
    
    def exists(self):
        return bool(self.node)
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            return super().handlemessage(msg)
        return None

class ChooserActivity(bs.Activity[bs.Player, bs.Team]):
    allow_pausing = True

    def __init__(self, settings):
        self.session: LostSession
        super().__init__(settings)
        self.killer_player = settings['killer_player']
        self.selected_killer_id: str | None = None
        self._killer_index = 0

    def on_transition_in(self):
        super().on_transition_in()
        from bascenev1lib.actor.background import Background
        Background().autoretain()

    def on_begin(self):
        super().on_begin()
        bs.setmusic(bs.MusicType.KILLER_SELECT)

        killer_keys = bs.app.classic.killers
        self.selected_killer_id = killer_keys[0]
        self.cards = {}
        x = 0
        y = 240
        scale = 1.6
        self._icon_size = icon_size = (256 * scale, 256 * scale)
        self._spacing = spacing = icon_size[0] - 40
        self._move_sound = bs.getsound('deek')
        self._done_sound = bs.getsound('punch01')
        name = self.killer_player.getname(full=True)
        self._player_text = bs.newnode(
            'text',
            attrs={
                'scale': 1.2,
                'text': f'- {name}; PICK YOUR CARD -',
                'h_align': 'center',
                'position': (x, y),
            }
        )
        y -= icon_size[0] - 150
        self._center_pos = (x, y)
        arrow_x = x
        arrow_y = y
        for killer in killer_keys:
            self.cards[killer] = ChooserCard(
                position=(x, y),
                size=icon_size,
                character=killer
            )
            x += spacing
        self._killer_index = len(killer_keys) - 1 * 0.5
        self._killer_index = int(self._killer_index)
        self._update_per_choice()

        self.session.start_timer(15)

        if self.killer_player:
            self.killer_player.resetinput()
            self.killer_player.assigninput(bs.InputType.RIGHT_PRESS, self._next_killer)
            self.killer_player.assigninput(bs.InputType.LEFT_PRESS, self._prev_killer)
            self.killer_player.assigninput(bs.InputType.PUNCH_PRESS, self._done)
        
        # ARROWS
        arrow_spacing = 500
        arrow_scale = 3.0
        arrow_color = (1, 0.3, 0.3)
        arrow = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('arrow_down'),
                'scale': (64 * arrow_scale, 32 * arrow_scale),
                'rotate': 90,
                'color': arrow_color,
            }
        )
        keys = {
            0: (arrow_x + arrow_spacing + 40, arrow_y),
            0.5: (arrow_x + arrow_spacing + 28, arrow_y),
            1: (arrow_x + arrow_spacing + 40, arrow_y),
        }
        keys = choppify(keys, fps=10)
        bs.animate_array(
            arrow,
            'position', 2,
            keys,
            loop=True,
        )
        arrow = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('arrow_down'),
                'scale': (64 * arrow_scale, 32 * arrow_scale),
                'rotate': -90,
                'color': arrow_color,
            }
        )
        keys = {
            0: (arrow_x - arrow_spacing - 40, arrow_y),
            0.5: (arrow_x - arrow_spacing - 28, arrow_y),
            1: (arrow_x - arrow_spacing - 40, arrow_y),
        }
        keys = choppify(keys, fps=10)
        bs.animate_array(
            arrow,
            'position', 2,
            keys,
            loop=True,
        )
    
    def _done(self):
        self._done_sound.play()
        self.session.stop_timer()
        self.on_timer_complete()
    
    def _next_killer(self):
        self._killer_index = (
            self._killer_index + 1
        ) % len(bs.app.classic.killers)
        self._update_per_choice()
        self._move_sound.play()
    
    def _prev_killer(self):
        self._killer_index = (
            self._killer_index - 1
        ) % len(bs.app.classic.killers)
        self._update_per_choice()
        self._move_sound.play()

    def _update_per_choice(self):
        killers = bs.app.classic.killers
        self.selected_killer_id = killers[self._killer_index]
        card_list = list(self.cards.values())
        chosen_card = card_list[self._killer_index]
        base_x, y = self._center_pos
        use_front = False

        for i, card in enumerate(card_list):
            if card is not chosen_card:
                offset = i - self._killer_index
                card.node.position = (base_x + offset * self._spacing, y)
                x, y = card.node.position
                card.node.color = (0.5, 0.5, 0.5)
                card.node.front = False
                if card.combine:
                    card.combine.delete()
                node = card.node
                card.combine = cmb = bs.newnode(
                    'combine',
                    owner=node,
                    attrs={'size': 2}
                )
                keys = {}
                time_v = 0.0
                jitter_scale = 4
                for _i in range(10):
                    keys[time_v] = (
                        x + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.1
                bs.animate(cmb, 'input0', keys, loop=True)
                keys = {}
                time_v = 0.0
                for _i in range(10):
                    keys[time_v] = (
                        y + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.1
                bs.animate(cmb, 'input1', keys, loop=True)
                cmb.connectattr('output', node, 'position')
            else:
                x, y = self._center_pos
                card.node.color = (1, 1, 1)
                card.node.front = use_front
                node = card.node
                card.combine = cmb = bs.newnode(
                    'combine',
                    owner=node,
                    attrs={'size': 2}
                )
                keys = {}
                time_v = 0.0
                jitter_scale = 4
                for _i in range(10):
                    keys[time_v] = (
                        x + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.01
                bs.animate(cmb, 'input0', keys, loop=True)
                keys = {}
                time_v = 0.0
                for _i in range(10):
                    keys[time_v] = (
                        y + (random.random() - 0.5) * 0.7 * jitter_scale
                    )
                    time_v += random.random() * 0.01
                bs.animate(cmb, 'input1', keys, loop=True)
                cmb.connectattr('output', node, 'position')

    def on_timer_complete(self):
        self.finish_selection()

    def finish_selection(self):
        try:
            player = self.killer_player
        except:
            self.end(
                {
                    'whowon': 'survivors',
                    'winners': [],
                }
            )
            return
        results = {
            'killer_player': player,
            'chosen_killer': self.selected_killer_id,
        }
        self.end(results)