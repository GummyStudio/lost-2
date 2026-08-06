import bascenev1 as bs
import random
from lost.gamemodes.default import DefaultMatch
from lost.lobby import Lobby
from lost.killer_selection import ChooserActivity
from bascenev1._activitytypes import TransitionActivity
from bascenev1lib import maps

class LostSession(bs.Session):
    """ the thing that handles everything ig"""

    use_team_colors = False
    use_team = False

    gamemode_maps = {
        DefaultMatch: [
            maps.StepRightUp,
            maps.MonkeyFace,
            maps.CragCastle,
            maps.BlockFortress,
        ]
    }
    def __init__(self):
        depsets: list[bs.DependencySet] = []
        self.last_results = None
        super().__init__(
            depsets, 
            team_names=None, 
            team_colors=None, 
            min_players=1, 
            max_players=9, 
            submit_score=False
        )

        self._timer_duration = 35.0
        self._max_timer_cap = 9999.0 
        self._time_remaining = 0.0
        self.next_gamemode = DefaultMatch

        self._timer_node: bs.Node | None = None
        self._countdown_timer: bs.Timer | None = None

        # Start up the lobby activity.
        self.chosen_map = random.choice(
            self.gamemode_maps[self.next_gamemode]
        )
        self.setactivity(
            bs.newactivity(
                Lobby,
                settings={
                    'chosen_map': self.chosen_map,
                    'last_results': self.last_results,
                }
            )
        )
        #for map in self.mapss:
        #    map.preload()
    
    def add_time(
        self, 
        seconds: float, 
        flash_color: tuple[float] = (1, 0, 0)
    ) -> None:
        if self._countdown_timer is None:
            return   # doesnt exist

        self._time_remaining = min(
            self._max_timer_cap, max(0.0, self._time_remaining + seconds)
        )

        # Update
        if self._timer_node:
            self._timer_node.text = f'{self.format_time(max(0, int(self._time_remaining)))}'
            # variables
            default_color = (1, 1, 1)
            default_scale = 1.3
            # this amount MUST be even (so ends in color1)
            steps = 15
            step_time = 0.07
            end_time = step_time * steps
            color1 = default_color
            color2 = flash_color
            anim = {
                i * step_time: (color1 if i % 2 == 0 else color2)
                for i in range(steps)
            }
            big_scale = default_scale + 0.6
            
            node = self._timer_node
            bs.animate_array(
                node, 'color', 3, anim,
            )
            bs.animate(
                node,
                'scale',
                {
                    0: node.scale,
                    0.1: big_scale, 
                    end_time - 0.1: big_scale, 
                    end_time: default_scale, 
                }
            )


    def start_timer(self, duration: float) -> None:
        if self._timer_node:
            self.stop_timer()
        self._time_remaining = duration
        self._timer_node = bs.newnode(
            'text',
            attrs={
                'v_attach': 'top',
                'h_align': 'center',
                'v_align': 'top',
                'opacity': 0.5,
                'scale': 1.3,
                'position': (0, -10),
            },
        )
        
        self._tick_timer()
        self._countdown_timer = bs.Timer(
            1.0,
            bs.WeakCall(self._tick_timer),
            repeat=True,
        )

    def stop_timer(self) -> None:
        self._countdown_timer = None
        if self._timer_node:
            self._timer_node.delete()
            self._timer_node = None
            
    def _tick_timer(self) -> None:
        can_tick, reason = self.getactivity().can_timer_tick()
        if not can_tick:
            self._timer_node.text = reason
            return
        self._time_remaining -= 1.0
        if self._timer_node:
            self._timer_node.text = f'{self.format_time(max(0, int(self._time_remaining)))}'
        if self._time_remaining <= 0:
            self.timer_complete()
            self.stop_timer()
            

    def timer_complete(self) -> None:
        # tell the activity the timer has ended.
        self.getactivity().on_timer_complete()
    
    def format_time(self, sec):
        hours = sec // 3600
        mins = (sec % 3600) // 60
        seconds = sec % 60
        if hours > 0:
            return f"{hours:02}:{mins:02}:{seconds:02}"
        else:
            return f"{mins:02}:{seconds:02}"
    
    def on_activity_end(self, activity, results):
        self.stop_timer()

        if results and not isinstance(activity, TransitionActivity):
            # Okay, gather results and transition ourselves.
            self.last_results = results
            self.setactivity(bs.newactivity(TransitionActivity))
        else:
            # Um.. Not a transition activity so try and do stuff based results
            if not self.last_results:
                raise Exception('no LostSession.last_results to go by')
            # Lobby ended, go to killer selection
            if self.last_results.get('lobby_end'):
                if self.last_results.get('next_gamemode'):
                    self.next_gamemode = self.last_results.get('next_gamemode')
                killer_selection = (
                    self.next_gamemode.chooser_activity_override 
                    or ChooserActivity
                )
                self.setactivity(
                    bs.newactivity(
                        killer_selection,
                        settings=self.last_results
                    )
                )
            # Match start
            elif (
                isinstance(self.last_results, dict) 
                and 'chosen_killers' in self.last_results
            ):
                self.setactivity(
                    bs.newactivity(
                        self.next_gamemode, 
                        settings={'match_data': self.last_results}
                    )
                )
                # If the next gamemode isn't a regular match,
                # reset it by ourselves
                if self.next_gamemode != DefaultMatch:
                    self.next_gamemode = DefaultMatch
            
            elif isinstance(self.last_results, dict):
                # Choose a map by ourselves when the lobby starts
                self.chosen_map = random.choice(
                    self.gamemode_maps[self.next_gamemode]
                )
                self.setactivity(
                    bs.newactivity(
                        Lobby, 
                        settings={
                            'chosen_map': self.chosen_map,
                            'last_results': self.last_results,
                        }
                    )
                )