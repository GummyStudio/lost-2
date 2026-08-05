"""Class for a ingame button that gets
activated by player spazzes."""
import bascenev1 as bs
from lost.factory import AsymFactory, IngameButtonPressedMessage
from bascenev1lib.gameutils import SharedObjects

class IngameButton(bs.Actor):
    def __init__(
        self, 
        position: tuple[float],
        scale: int = 1.0,
    ):
        scale = 1.0
        asymf = AsymFactory.get()
        shared = SharedObjects.get()
        self.node = bs.newnode(
            'prop',
            attrs={
                'body': 'crate',
                'mesh': bs.getmesh('box'),
                'mesh_scale': scale - 0.2,
                'body_scale': scale,
                'materials': (asmyf.button_material, shared.footing_material),
            }
        )
    
    def on_press(self, player: bs.Player):
        raise RuntimeError("Ingame button's press method wasn't overriden")
    
    def on_release(self, player: bs.Player):
        raise RuntimeError("Ingame button's release method wasn't overriden")
    
    def handlemessage(self, msg):
        if isinstance(msg, IngameButtonPressedMessage):
            node = bs.getcollision().opposingnode
            actor = node.getdelegate(Spaz)
            if not node or not actor:
                return
            player = actor.source_player
            if msg.state:
                self.on_press(player)
            else:
                self.on_release(player)
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            return super().handlemessage(msg)
        return None