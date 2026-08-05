"""Base module for the Lobby."""
import bascenev1 as bs
import random
from lost.functions import assignspazinput
from bascenev1lib import maps
from bascenev1lib.actor.spaz import Spaz

class Lobby(bs.Activity[bs.Player, bs.Team]):
    """ where the lobby takes place. """
    allow_pausing = True
    def __init__(self, settings):
        super().__init__(settings)
        self.killers = []
        self.killer_player = settings.get('next_killer')
        if not self.killer_player:
            if self.players:
                self.killer_player = random.choice(self.players)
        self.random_chosen_map = self.chosen_map = settings.get('chosen_map')
        self._map = maps.ThePad
        self._map.preload()
    
    def can_timer_tick(self):
        return (bool(self.players), 'waiting for players...')
    
    def on_transition_in(self):
        super().on_transition_in()
        self.map = self._map()
    
    def on_begin(self):
        super().on_begin()
        # Start us a timer.
        bs.setmusic(bs.MusicType.LOBBY)
        self.session.start_timer(15)

    def on_player_join(self, player):
        # If we have no killer,
        # choose this one as our own
        if not self.killer_player:
            self.killer_player = player
        self.spawn_player(player)
    
    def on_player_leave(self, player):
        # If this player was the killer player,
        # then choose a new one
        if player is self.killer_player:
            # Get if other players exist
            others = list(p for p in self.players if p != player)
            if others:
                new = self.killer_player = random.choice(others)
                # Refresh the new killer to give em their new character
                new.actor.handlemessage(bs.DieMessage(True))
                self.spawn_player(new)
            # If not, killer is none
            else:
                self.killer_player = None
        player.actor.handlemessage(bs.DieMessage(how=bs.DeathType.LEFT_GAME))
        

    def spawn_player(self, player: bs.Player):
        # get a spawn position
        spawn = self.map.get_ffa_start_position([])
        character = player.character
        is_killer = False
        if player is self.killer_player:
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
            self.end(
                {
                    'lobby_end': True,
                    'killer_player': self.killer_player.sessionplayer
                }
            )