"""Class for a ingame button that gets
activated by player spazzes."""
import bascenev1 as bs
import weakref
from lost.factory import AsymFactory, IngameButtonPressedMessage
from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.gameutils import SharedObjects

class IngameButton(bs.Actor):
    def __init__(
        self, 
        position: tuple[float],
        scale: int = 1.0,
    ):
        super().__init__()
        self._scale = scale = 0.9
        self._big_scale = scale * 1.2
        self._small_scale = scale * 0.8
        self._last_players = []
        asymf = AsymFactory.get()
        shared = SharedObjects.get()
        self.allow_presses = True
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'puck',
                'mesh': bs.getmesh('puck'),
                'color_texture': bs.gettexture('bg'),
                'mesh_scale': scale,
                'materials': (asymf.no_collision,),
                'position': position,
            }
        )
        self.region = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': position,
                'scale': (1.05 * scale, 0.17 * scale, 1.0 * scale),
                'type': 'box',
                'materials': (
                    asymf.button_material, 
                    shared.footing_material,
                ),
            },
        )
        test = False
        if test:
            region = self.region
            bs.newnode(
                'locator', 
                attrs={
                    'position': region.position,
                    'size': region.scale,
                    'shape': 'box',
                }
            )
        self.combine = bs.newnode(
            'combine', 
            owner=self.node, 
            attrs={
                'size': 3,
                'input0': position[0],
                'input1': position[1],
                'input2': position[2],
            }
        )
        self.combine.connectattr('output', self.node, 'position')
    
    def reset_allow_press(self, player: weakref.ref):
        self._last_players.remove(player)
    
    def on_press(self, player: bs.Player):
        raise RuntimeError("Ingame button's press method wasn't overriden")
    
    def on_release(self, player: bs.Player):
        raise RuntimeError("Ingame button's release method wasn't overriden")
    
    def animate_press(self, player: bs.Player):
        bs.animate(
            self.node,
            'mesh_scale',
            {
                0: self.node.mesh_scale,
                0.05: self._small_scale,
            }
        )
        self.on_press(player)
    
    def animate_release(self, player: bs.Player):
        bs.animate(
            self.node,
            'mesh_scale',
            {
                0: self.node.mesh_scale,
                0.05: self._scale,
            }
        )
        self.on_release(player)
        
    
    def handlemessage(self, msg):
        if isinstance(msg, IngameButtonPressedMessage):
            try:
                node = bs.getcollision().opposingnode
            except:
                node = None
            actor = node.getdelegate(Spaz)
            if not node or not actor:
                return
            player = actor.source_player
            if not player:
                return
            wref = weakref.ref(player)
            if not msg.state:
                self.animate_release(player)
            if wref in self._last_players:
                return
            self._last_players.append(wref)
            if msg.state:
                self.animate_press(player)
            bs.timer(0.3, bs.WeakCall(self.reset_allow_press, wref))
            
            
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            return super().handlemessage(msg)
        return None