"""Class for a survivor's icon."""
import bascenev1 as bs
from lost.functions import lerp
HP_COLORS = [
    (0,   (0.3, 0.1, 0.1)),
    (500, (0.9, 0, 0.1)),
    (1000, (0, 1, 0.1)),
]

def _get_hp_color(hp: float):
    points = HP_COLORS

    # Below first threshold
    if hp <= points[0][0]:
        return points[0][1]

    # Between thresholds
    for i in range(len(points) - 1):
        p1, c1 = points[i]
        p2, c2 = points[i + 1]

        if p1 <= hp <= p2:
            t = (hp - p1) / (p2 - p1)  # 0 → 1
            return lerp(c1, c2, t)

    # Above last threshold
    return points[-1][1]

class SurvivorIcon(bs.Actor):
    """An icon for a survivor that will update by itself
    when told to by something (like the match)."""
    def __init__(
        self, 
        position: tuple[float],
        source_player: bs.Player,
        scale: int = 1,
    ):
        super().__init__()
        self._source_player = source_player
        self._spaz = source_player.actor
        self._already_logged_death = False
        size = (64 * scale, 64 * scale)
        self.node = bs.newnode(
            'image',
            attrs={
                'scale': size,
                'position': position,
                'attach': 'bottomCenter',
                'mask_texture': bs.gettexture('characterIconMask'),
            }
        )
        node = self.node
        player = self._source_player
        apps = bs.app.classic.spaz_appearances
        character = apps[player.character]
        gt = bs.gettexture
        node.tint_texture = gt(character.icon_mask_texture)
        node.texture = gt(character.icon_texture)
        node.tint_color = player.color
        node.tint2_color = player.highlight
        y_spacing = -30
        self.name_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': player.getname(),
                'scale': scale,
                'position': (
                    position[0], 
                    position[1] + ((size[1] * scale) + y_spacing)
                ),
                'v_attach': 'bottom',
                'h_align': 'center',
                'v_align': 'bottom',
                'maxwidth': size[0] + 30,
                'color': bs.safecolor(player.color),
            }
        )
        self.hp_node = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'scale': scale,
                'position': (
                    position[0], 
                    position[1] - ((size[1] * scale) + y_spacing)
                ),
                'v_attach': 'bottom',
                'h_align': 'center',
                'v_align': 'top',
                'maxwidth': size[0] + 30,
            }
        )
        self.node.connectattr('opacity', self.name_node, 'opacity')
        self.node.connectattr('opacity', self.hp_node, 'opacity')
        self.update()
    
    def update(self):
        if not self._spaz:
            return
        if not self._spaz.is_alive():
            self.node.color = (0.4, 0.4, 0.4)
        self.hp_node.text = '+' + str(
            int(self._spaz.hitpoints / 10)
        )
        self.hp_node.color = _get_hp_color(self._spaz.hitpoints)
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            self._source_player = None
            self._spaz = None
            if self.node:
                self.node.delete()
        else:
            return super().handlemessage(msg)
        return None