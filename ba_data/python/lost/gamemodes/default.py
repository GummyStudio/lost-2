"""Module containing a class for the default match type."""
import bascenev1 as bs
import random
from lost.factory import AsymFactory
from lost.survivoricon import SurvivorIcon
from lost.functions import assignspazinput, PlayerInfoPlus
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.zoomtext import ZoomText

_WIN_CONFIG = {
    'survivors': {
        'text': 'SURVIVORS WIN!',
        'color': (0.2, 0.5, 1),
        'sound_attr': 'survivors_won_sound',
    },
    'killers': {
        'text': 'KILLERS WIN!',
        'color': (1, 0.1, 0),
        'sound_attr': 'killers_won_sound',
    },
}

class DefaultMatch(bs.Activity[bs.Player, bs.Team]):
    allow_pausing = True
    allow_mid_activity_joins = False
    chooser_activity_override = None
    name = 'a Match'

    def __init__(self, settings):
        self.session: LostSession
        super().__init__(settings)
        self._source_player_roles: dict[str, list[bs.Player]] = {}
        self._source_player_roles['killers'] = []
        self._source_player_roles['survivors'] = []
        self.survivors: list[bs.Player] = set()
        self.killers: list[bs.Player] = set()
        self.ended = False
        self.lms = False
        self.max_terror_radius = 40.0
        self.min_terror_radius = 2.5
        self._entries = {}
        self._survivor_icons = []
        self.match_data = settings.get('match_data', {})
        # Seriously eric.. no other way to make this better?
        self.session_killers = self.match_data.get('killer_players')
        self.session_killer_characters = self.match_data.get('chosen_killers')
        self.aura_done = False # for taobao vs kronk lms
        # Get a random map from our class type
        self._map = self.session.chosen_map
        self._map.preload()
        self.chase_music = None
        self.lowHP_music = None
        
    def on_expire(self):
        super().on_expire()
        self.survivors = set()
        self.killers = set()
        self._ui_update_timer = None
    
    def _spawn_survivor_icons(self):
        # we want center of screen,
        # so let's do that
        scale = 0.8
        icon_size = (64 * scale, 64 * scale)
        spacing = icon_size[0] + 25
        total_width = (len(self.survivors)) * spacing
        x = -total_width * 0.5
        y = 50
        for survivor in self.survivors:
            icon = SurvivorIcon(
                position=(x, y),
                scale=scale,
                source_player=survivor,
            )
            self._survivor_icons.append(icon)
            x += spacing
        
    def _update_icons(self):
        for icon in self._survivor_icons:
            icon.update()
    
    def on_transition_in(self):
        super().on_transition_in()
        self.map = self._map()
    
    def check_end(self):
        # No survivors, killers win.
        if len(self.survivors) == 0:
            self.end_game('killers')
        # No killers, survivors win.
        if len(self.killers) == 0:
            self.end_game('survivors')
    
    def on_begin(self):
        super().on_begin()
        bs.setmusic(None)
        killer_players = list(
            p.activityplayer for p
            in self.session_killers
            if p.exists()
        )
        # For now, we just want the first character
        chars_vals = self.session_killer_characters.values()
        chars_list = list(chars_vals)
        self.killer_character = chars_list[0]
        for player in self.players:
            is_killer = player in killer_players
            role = 'killers' if is_killer else 'survivors'
            role_list = self._source_player_roles.get(role)
            role_list.append(player)
            self.spawn_player(player, is_killer=is_killer)
        self._spawn_survivor_icons()
        self._ui_update_timer = bs.Timer(
            0.1, 
            bs.WeakCall(self._update_icons), 
            repeat=True
        )
        character = self.killer_character
        app = bs.app.classic.spaz_appearances[character]
        low_hp_music_RRAWW = app.moveset.low_theme_dir
        low_hp_sound = bs.getsound(app.moveset.low_theme_dir)
        chase_sound = bs.getsound(app.moveset.chase_theme_dir)
        self.chase_music = bs.newnode(
            'sound',
            attrs={
                'sound': chase_sound,
                'positional': False,
                'music': True,
                'volume': 0.0,
            },
        )
        # FIXME: None exists you absolute fucking dumbass
        if low_hp_music_RRAWW != 'blank':
            self.lowHP_music = bs.newnode(
                'sound',
                attrs={
                    'sound': low_hp_sound,
                    'positional': False,
                    'music': True,
                    'volume': 0.0,
                },
            )
        bs.timer(0.1, self._music_tick, repeat=True)

        # Start us a timer.
        # Here we want based on the amount of survivors;
        # This should give us a pretty fair amount of time
        # to the killer so they could get a chance at killing everyone.
        total_survivors = len(self.survivors)
        default_time = 30
        self.session.start_timer(60+(default_time * total_survivors))

        # just incase theres 1 guy
        bs.timer(0.5, self.check_lms)
       
    def set_player_dead(self, player: bs.Player) -> None:
        pass
    
    def _music_tick(self):
        if (
            self.lms 
            or not self.chase_music 
            or not self.chase_music.exists()
        ):
            return

        # gummy what the fuck
        min_distance = float('inf')
        in_active_chase = False
        spaz_injured = False
        chasing_survivor = None

        # killer nod
        killer_nodes = []
        for killer in self.killers:
            if killer.actor and killer.actor.node and killer.actor.node.exists():
                killer_nodes.append(killer.actor)

        # check distances on survivors
        for survivor in self.survivors:
            # Don't count if they are dead
            if (
                not survivor.actor 
                or not survivor.actor.is_alive()
                or not survivor.actor.node
            ):
                continue

            survivor_pos = survivor.actor.node.position
            for k_spaz in killer_nodes:
                killer_pos = k_spaz.node.position
                # This just looks nicer
                # I dunno man
                if (
                    getattr(k_spaz, 'in_chase', False) 
                    or getattr(survivor.actor, 'in_chase', False)
                ):
                    in_active_chase = True

                # bs.Vec3 here is cleaner
                diff = bs.Vec3(survivor_pos) - bs.Vec3(killer_pos)
                dist = diff.length()
                if dist < min_distance:
                    min_distance = dist
                    chasing_survivor = survivor
        if chasing_survivor:
            spaz_injured = chasing_survivor.actor.hitpoints <= 250

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
        # FIXME: like really no this just looks ugly
        current_lowHP_vol = getattr(self.lowHP_music, 'volume', 0)
        # Play different chase music if
        # we have it (and if the spaz is low hp)
        if chasing_survivor:
            if spaz_injured and self.lowHP_music:
                self.chase_music.volume = 0
                self.lowHP_music.volume = current_lowHP_vol + (target_volume - current_lowHP_vol) * 0.2
            else:
                if self.lowHP_music:
                    self.lowHP_music.volume = 0
                self.chase_music.volume = current_vol + (target_volume - current_vol) * 0.2

    def show_win_text(self, text: str, color: tuple[float] = (1, 1, 1)):
        trail = bs.Vec3(color) - bs.Vec3(0.2)
        ZoomText(
            text,
            maxwidth=800,
            lifespan=2.5,
            jitter=2.0,
            position=(0, 200),
            flash=False,
            color=color,
            trailcolor=trail,
        ).autoretain()
        
    def end_game(self, whowon: str) -> None:
        if self.ended:
            return
        self.ended = True
        cfg = _WIN_CONFIG[whowon]
        
        winning_players = self._source_player_roles.get(whowon, [])
        winners: list[PlayerInfoPlus] = []
        losers: list[PlayerInfoPlus] = []

        

        for player in self.players:
            info = PlayerInfoPlus(
                name=player.getname(full=True, icon=True),
                color=player.color,
                highlight=player.highlight,
                character=player.character,
            )

            if player in winning_players:
                winners.append(info)

                # Winner, give invincibility if alive.
                if player.actor and player.actor.is_alive():
                    player.actor.set_invincible(10)
            else:
                losers.append(info)
        results = {
            'whowon': whowon,
            'winners': winners,
            'losers': losers,
        }
        self.session.stop_timer()
        bs.setmusic(None)
        self.show_win_text(cfg['text'], color=cfg['color'])
        getattr(AsymFactory.get(), cfg['sound_attr']).play()
        bs.timer(2.7, bs.WeakCall(self.end, results=results))

    def spawn_player(self, player: bs.Player, is_killer=False):
        # get a spawn position
        if is_killer:
            self.killers.add(player)
            spawn = self.map.get_ffa_start_position(list(self.survivors))
            # For now hard code it into spaz, sigh..
            character = self.session_killer_characters[player.sessionplayer]
            app = bs.app.classic.spaz_appearances[character]
            color = app.default_color
            highlight = app.default_highlight

        else:
            self.survivors.add(player)
            spawn = self.map.get_ffa_start_position([])
            character = player.character # Their survivor..
            color=player.color
            highlight=player.highlight
        
       
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
        # Remove player from roles if they're
        # there just so they die normally.
        for role in self._source_player_roles:
            role_list = self._source_player_roles.get(role)
            if player in role_list:
                role_list.remove(player)
        self.check_end()

    def start_lms(self):
        try:
            if self.lms:
                return
            self.check_end()
            
            if self.chase_music:
                self.chase_music.delete()
                self.chase_music = None
            if self.lowHP_music:
                self.lowHP_music.delete()
                self.lowHP_music = None
            # Special killer to survivor LMS
            # Format here is (Killer, Survivor)
            special_lms = {
                ('Spaz', 'Zoe'): {
                    'texture': 'spaz-vs-zoe',
                    'time': 96,
                    'music': bs.MusicType.LMS4,
                },
                ('Snake Shadow', 'Mel'): {
                    'texture': 'ninja-vs-mel',
                    'time': 86,
                    'music': bs.MusicType.LMS5,
                },
                ('Spaz', 'Salvatore'): {
                    'texture': 'spaz-vs-sal',
                    'time': 90,
                    'music': bs.MusicType.LMS6,
                },
                ('Easter Bunny', 'Penny'): {
                    'texture': 'bunny-vs-penny',
                    'time': 89,
                    'music': bs.MusicType.LMS7,
                },
                ('Bones', 'Bernard'): {
                    'texture': 'bones-vs-bernard',
                    'time': 88,
                    'music': bs.MusicType.LMS8,
                },
                ('Taobao Mascot', 'Kronk'): {
                    'texture': 'spaz',
                    'time': 97,
                    'music': bs.MusicType.LMS9,
                },
                
            }
            # Should update this to support multi-killers.
            killers = list(self.killers)
            killer_char = killers[0].actor.character
            # This too.
            survivors = list(self.survivors)
            survivor_char = survivors[0].actor.character
            special_lms_dict = special_lms.get(
                (killer_char, survivor_char),
                None,
            )
            if special_lms_dict:
                if killer_char == "Taobao Mascot" and survivor_char == "Kronk":
                    self.session.overtime = True
                time = special_lms_dict.get('time')
                music = special_lms_dict.get('music')
                texture = special_lms_dict.get('texture')
                self.session.start_timer(time)
                bs.setmusic(music)
                self.show_lms_texture(texture)
            else:
                self.session.start_timer(69)
                bs.setmusic(bs.MusicType.LMS1)
                # FIXME: this is OBJECTIVELY better,
                # but we should still move to spazapps
                textures = {
                    'Snake Shadow': 'snakeshadow',
                    'Easter Bunny': 'bunny',
                    'Grumbledorf': 'wizard',
                    'Bones': 'bones',
                    'Taobao Mascot': 'ali',
                    'Spaz': 'spaz',
                    'Pixel': 'pixel',
                }
                
                # Get the killer's LMS texture, but in any case
                # just fallback to spaz.
                texture = textures.get(killer_char, 'Spaz')
                self.show_lms_texture(texture)

            self.lms = True
            self.allow_pausing = False
            for player in self.survivors:
                player.actor.node.is_area_of_interest = True
            for player in self.killers:
                player.actor.node.is_area_of_interest = True
            # Set the BG...
            self.map.background.color_texture = bs.gettexture('spectureBG')
            self.globalsnode.tint = (1, 0.8, 0.8)
        except:
            pass
            # idk gang the killer or survivor probably left before it started
    
        
    def show_lms_texture(
        self,
        texture_name: str, 
        position = (0, 0)
    ):
        x, y = position
        # Variables
        scale = 1.7
        scale_ex = scale + 0.6
        size = (256 * scale, 256 * scale)
        size_ex = (256 * scale_ex, 256 * scale_ex)
        display_duration = 2.5
        # Make a nice lil node
        node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(f'LMS/{texture_name}'),
                'position': position,
            },
        )
        def do_shake():
            AsymFactory.get().lms_image_shake_sound.play(
                volume=1.5
            )
            cmb = bs.newnode(
                'combine', 
                owner=node, 
                attrs={'size': 2}
            )
            cmb.connectattr('output', node, 'position')
            keys = {}
            time_v = 0.0

            # Gen some random keys for that stop-motion-y look
            jitter_scale = 14
            key_amount = 20
            key_time = 0.03
            for _i in range(key_amount):
                keys[time_v] = (
                    x + (random.random() - 0.5) * 0.7 * jitter_scale
                )
                time_v += random.random() * key_time
            bs.animate(cmb, 'input0', keys, loop=False)
            keys = {}
            time_v = 0.0
            for _i in range(10):
                keys[time_v] = (
                    y + (random.random() - 0.5) * 0.7 * jitter_scale
                )
                time_v += random.random() * key_time
            bs.animate(cmb, 'input1', keys, loop=False)
        bs.animate_array(
            node,
            'scale', 2,
            {
                0: (0, 0),
                0.1: size_ex,
                0.2: size,
                display_duration - 0.3: size,
                display_duration: (0, 0),
            }
        )
        bs.timer(0.1, do_shake)
        bs.timer(display_duration, node.delete)
    
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
            
            self.check_end()
        else:
            return super().handlemessage(msg)

    # Every activity should have this.
    def on_timer_complete(self):
        # stolen co d heh ehe he
        killers = list(self.killers)
        killer_char = killers[0].actor.character
        survivors = list(self.survivors)
        survivor_char = survivors[0].actor.character
        if (
            killer_char == "Taobao Mascot" 
            and survivor_char == "Kronk" 
            and not self.aura_done
        ): # holy mother of conditions
            self.session.add_time(17.0, (1, 0, 0)) # add aura to the lms.
            bs.broadcastmessage(
                "YOU'RE NOT GETTING AWAY THAT EASILY.", 
                color=(1, 0.6, 0.6)
            )
            self.aura_done = True
            return
        # time ended successfully!
        # survivors win then
        self.end_game('survivors')
    
    def end(self, results = None, delay = 0, force = False):
        bs.setmusic(None)
        return super().end(results, delay, force)