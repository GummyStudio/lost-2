"""Base module for the Lobby."""
import bascenev1 as bs
import random
from lost.functions import assignspazinput
from bascenev1lib import maps
from bascenev1lib.actor.spaz import Spaz
from lost.gamemodes.default import DefaultMatch
from lost.ingame_button import IngameButton
from lost.factory import AsymFactory
# set to 4 for default,
# and to 9999 if you want no extra killers
# set to something like 2 if yous testin
PLAYER_TO_KILLER_LIMIT = 9999
_DEFAULT_RESULT_COLORS = {
    'survivors': (0.2, 0.4, 0.9),
    'killers': (0.9, 0.2, 0.1),
}
_DEFAULT_RESULT_COLOR = (1, 1, 1)

class MapPreview(bs.Actor):
    def __init__(
        self, 
        position: tuple[float],
        map: bs.Map,
        scale: int = 1.0,
    ):
        super().__init__()
        self._map = map
        asymf = AsymFactory.get()
        self.node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'body_scale': 0.3,
                'position': position,
                'gravity_scale': 0,
                'materials': [asymf.no_collision,],
                'shadow_size': 0,
            },
        )
        map_tex = map.get_preview_texture_name()
        texture = bs.gettexture(map_tex)
        mesh = bs.getmesh('level_select_ingame')
        self.mesh_node: bs.Node = bs.newnode(
            'prop',
            delegate=self,
            owner=self.node,
            attrs={
                'mesh': mesh,
                'color_texture': texture,
                'mesh_scale': scale,
                'gravity_scale': 0,
                'body': 'puck',
                'position': position,
                'shadow_size': 0,
                'materials': [asymf.no_collision,],
                'reflection_scale': [0.0,],
            },
        )
        text_pos = (
            position[0], 
            position[1] + 0.5,
            position[2]
        )
        self.name_text_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': map.name,
                'scale': 0.012,
                'in_world': True,
                'h_align': 'center',
                'position': text_pos,
            }
        )
        text_pos = (
            position[0], 
            position[1] + 0.8,
            position[2]
        )
        self.votes_text_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': '',
                'scale': 0.011,
                'in_world': True,
                'h_align': 'center',
                'v_align': 'bottom',
                'position': text_pos,
                'color': (0.8, 0.9, 1),
            }
        )
        self.node.connectattr('position', self.mesh_node, 'position')
    
    def _update_votes(self):
        activity = self.getactivity()
        text = activity.get_formatted_votes(self._map)
        self.votes_text_node.text = text
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else: 
            return super().handlemessage(msg)

class Lobby(bs.Activity[bs.Player, bs.Team]):
    """ where the lobby takes place. """
    allow_pausing = True
    def __init__(self, settings):
        super().__init__(settings)
        self.killers = []
        self.killer_players = settings.get('next_killers')
        self._round_results = settings.get('last_results')
        # By default next gamemode is just the default
        self.next_gamemode = DefaultMatch
        # If we have no killer players but some players,
        # let's pick out some random ones
        if not self.killer_players:
            self.killer_players = []
            if self.players:
                while len(self.killer_players) < desired:
                    candidates = [
                        p for p in self.players
                        if p not in self.killer_players
                    ]
                    # If no candidates are possible, 
                    # break out the loop
                    if not candidates:
                        break

                    new = random.choice(candidates)
                    self.killer_players.append(new)
        # By default we have both a 
        # randomly chosen map and a normal chosen map,
        # which allows the chosen map to be changed
        # but still allow the randomly chosen one in case of no voting.
        self.random_chosen_map = self.chosen_map = settings.get('chosen_map')
        self._map = maps.ThePad
        self._map.preload()
        # Map voting related stuff.
        # I felt annotation was necessary here. ;3
        self._map_vote_buttons: dict[bs.Map, IngameButton] = {}
        self._map_player_votes: dict[bs.Map, bs.Player] = {}
        self._map_previews: list[MapPreview] = []
        self._vote_sound = bs.getsound('roblox_beep')
    
    def get_formatted_votes(self, map: bs.Map):
        votes = self._map_player_votes.get(map)
        names = list(p.getname(full=True, icon=True) for p in votes)
        return '\n'.join(names)
    
    def set_best_map(self):
        if all(
            i == 0 for i in 
            self._map_player_votes.values()
        ):
            best_map = self.random_chosen_map
        else:
            best_map = max(
                self._map_player_votes, 
                key=lambda k: len(self._map_player_votes[k])
            )
        self.chosen_map = best_map
    
    def _update_votes(self):
        for map in self._map_player_votes:
            votes = self._map_player_votes.get(map)
            for player in votes:
                if not player.exists():
                    votes.remove(player)
        for actor in self._map_previews:
            actor._update_votes()
    
    def player_vote(
        self, 
        player: bs.Player, 
        map: bs.Map,
    ):
        actor = player.actor
        if not actor:
            return
        node = player.actor.node
        if not node:
            return
        self._vote_sound.play(
            position=node.position
        )
        votes = self._map_player_votes.get(map)
        if player not in votes:
            votes.append(player)
        elif player in votes:
            votes.remove(player)
        else:
            # I have no idea how you would
            # run into this in any way
            raise RuntimeError('How.')
        for other_map in self._map_player_votes.keys():
            if other_map != map:
                votes = self._map_player_votes.get(other_map)
                if player in votes:
                    votes.remove(player)
        self._update_votes()
        self.set_best_map()
        
        
    def do_nothing(self, player):
        """DO NOTHING!!!!"""
    
    def make_vote_buttons(self):
        # Clear any existing buttons.
        if self._map_vote_buttons:
            self._map_vote_buttons.clear()
        if self._map_previews:
            self._map_previews.clear()
        # Make some calcs to 
        # center the buttons nicely.
        x_offs = -1.3
        button_scale = 0.8
        button_amount = 3
        spacing = 2.1
        y = 3.3
        total_width = ((button_amount * spacing) * button_scale) + x_offs
        x = -total_width * 0.5
        z = -5
        # Get the maps that this gamemode can have.
        allowed_maps = self.session.gamemode_maps[self.next_gamemode]
        for _ in range(button_amount):
            # Get a map that doesn't have a button.
            other_maps = list(
                m for m in allowed_maps
                if m not in 
                list(self._map_vote_buttons.keys())
            )
            # No other maps? Continue.
            if other_maps:
                this_map = random.choice(other_maps)
            else:
                continue
            self._map_player_votes[this_map] = []
            btn = IngameButton(
                position=(x, y, z),
                scale=button_scale,
            )
            btn.on_press = bs.WeakCall(
                self.player_vote, 
                map=this_map
            )
            btn.on_release = bs.WeakCall(self.do_nothing)
            self._map_vote_buttons[this_map] = btn
            preview_pos = (
                x, y + 1.2, z
            )
            preview = MapPreview(
                position=preview_pos,
                map=this_map,
            )
            self._map_previews.append(preview)
            x += spacing

    
    def can_timer_tick(self):
        # Allow ticking if we have players
        return (len(self.players) > 1, 'waiting for players...')
    
    def on_transition_in(self):
        super().on_transition_in()
        self.map = self._map()
    
    def on_begin(self):
        super().on_begin()
        # Start us a timer.
        bs.setmusic(bs.MusicType.LOBBY)
        self.session.start_timer(15)
        self.make_vote_buttons()
        # If we have the last round's results,
        # let's display them
        if self._round_results:
            self._display_round_results(self._round_results)

    def _display_round_results(
        self,
        results: dict,
        *,
        x: float = 610,
        y: float = 310,
        x_attach: str = 'left',
        y_attach: str = 'top',
        scale: float = 0.8,
        flatness: float = 0.6,
        shadow: float = 0.3,
        y_spacing: float = 30,
        x_spacing: float = 150,
        colors: dict | None = None,
    ) -> None:
        losers = results.get('losers', ())
        winners = results.get('winners', ())
        whowon = results.get('whowon')

        colors = colors or _DEFAULT_RESULT_COLORS
        color = results.get('color') or colors.get(whowon, _DEFAULT_RESULT_COLOR)

        # Normalize spacing/position based on attach points instead of
        # hardcoding sign flips inline.
        x = -x if x_attach == 'left' else x if x_attach == 'right' else x * 0.5
        y = -y if y_attach == 'bottom' else y
        y_spacing = (y_spacing * scale) * (-1 if y_attach == 'bottom' else 1)
        x_spacing = (x_spacing * scale) * (-1 if x_attach == 'right' else 1)

        name_maxwidth = abs(x_spacing) - 30

        base_attrs = {
            'h_align': x_attach,
            'scale': scale,
            'shadow': shadow,
            'flatness': flatness,
        }

        def _add_text(text, pos, *, extra=None, use_color=False):
            attrs = dict(base_attrs, text=text, position=pos)
            if use_color:
                attrs['color'] = color
            if extra:
                attrs.update(extra)
            return bs.newnode('text', attrs=attrs)

        def _add_column(header, infos, x_pos, y_start):
            y_pos = y_start
            _add_text(header, (x_pos, y_pos))
            y_pos -= y_spacing
            for info in infos:
                _add_text(
                    info.name,
                    (x_pos, y_pos),
                    extra={
                        'maxwidth': name_maxwidth,
                        'color': info.color, 
                    },
                )
                y_pos -= y_spacing
            return y_pos

        _add_text(
            f'{whowon.upper()} won the last round!' if whowon else 'Round complete!',
            (x, y),
            use_color=True,
        )
        y -= y_spacing

        _add_column('- WINNERS -', winners, x, y)
        _add_column('- LOSERS -', losers, x + x_spacing, y)
    
    def _desired_killers(self) -> int:
        """Return how many killers there should be."""
        player_count = len(self.players)

        if player_count == 0:
            return 0
        return (player_count + PLAYER_TO_KILLER_LIMIT - 1) // PLAYER_TO_KILLER_LIMIT
        
    def on_player_join(self, player):
        desired = self._desired_killers()
        # If this player joins while we don't
        # have enough killers, let's add em in
        if len(self.killer_players) < desired:
            self.killer_players.append(player)
        self.spawn_player(player)
    
    def on_player_leave(self, player):
        player.actor.handlemessage(
            bs.DieMessage(how=bs.DeathType.LEFT_GAME)
        )

        if player in self.killer_players:
            self.killer_players.remove(player)

        desired = self._desired_killers()

        while len(self.killer_players) < desired:
            candidates = [
                p for p in self.players
                if p not in self.killer_players
            ]
            # If no candidates are possible, 
            # break out the loop
            if not candidates:
                break

            new = random.choice(candidates)
            self.killer_players.append(new)

            # Refresh them as a killer
            new.actor.handlemessage(bs.DieMessage(True))
            self.spawn_player(new)
        

    def spawn_player(self, player: bs.Player):
        # get a spawn position
        spawn = self.map.get_ffa_start_position([])
        character = player.character
        is_killer = False
        if player in self.killer_players:
            character = 'Spaz'
            is_killer = True
       
        spaz = Spaz(
            character=character,
            color=player.color,
            highlight=player.highlight,
            source_player=player,
            start_invincible=False,
            is_killer=is_killer,
        )
        spaz.handlemessage(bs.StandMessage(spawn))
        spaz.node.name = player.getname()
        spaz.node.name_color = player.color
        player.actor = spaz
        assignspazinput(spaz, player)
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.PlayerDiedMessage):
            self.spawn_player(msg.getplayer(bs.Player))
        else:
            return super().handlemessage(msg)

    def on_timer_complete(self):
        if len(self.players) <= 1:
            # Push call to delay it a bit
            # (allows timer to restart normally)
            bs.pushcall(bs.Call(self.session.start_timer, 35))
        else:
            self.session.chosen_map = self.chosen_map
            killers = list(p.sessionplayer for p in self.killer_players)
            self.end(
                {
                    'lobby_end': True,
                    'killer_players': killers,
                    'next_gamemode': self.next_gamemode,
                }
            )