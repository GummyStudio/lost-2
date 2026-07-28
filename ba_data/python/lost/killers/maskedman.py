from typing import override, Any
from lost.lost import (
    CharacterMoveset, 
    DamageMessage, 
    AsymFactory, 
    StunMessage, 
    SurvivorDetectedMessage
)
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.popuptext import PopupText
import bascenev1 as bs
import babase
import random

class Beam(bs.Actor):
    def __init__(
        self,
        position: tuple[float],
        owner: bs.Actor,
    ):
        super().__init__()
        self.mesh = bs.getmesh('bomb')
        self.tex = bs.gettexture('tokens4')
        self.scale = 0.9
        self.bscale = 1.2
        self.owner = owner
        self.hurtpoints = random.randint(100, 350)
        shared = SharedObjects.get()
        asymf = AsymFactory.get()
        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'sphere',
                'body_scale': self.bscale,
                'position': position,
                'mesh': self.mesh,
                'mesh_scale': 0,
                'light_mesh': self.mesh,
                'shadow_size': self.bscale,
                'color_texture': self.tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'gravity_scale': 0,
                'materials': (asymf.killer_trap_object_material, shared.object_material),
            },
        )
        self.dying = False
        bs.animate(self.node, 'mesh_scale', {0: 0, 0.2: self.scale})
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        if self.expired:
            return None
            
        if isinstance(msg, bs.DieMessage):
            self.dying = True
            if msg.immediate:
                self.node.delete()
            else:
                bs.animate(self.node, 'mesh_scale', {0: self.scale, 0.1: 0})
                bs.timer(0.1, self.node.delete)
                
        elif isinstance(msg, SurvivorDetectedMessage):
            collision = bs.getcollision()
            toucher = collision.opposingnode
            if not toucher:
                return None
            ishittable = toucher.getnodetype() in ['spaz']
            if self.dying:
                return
            if not ishittable:
                return None
            actor = toucher.getdelegate(bs.Actor)
            other_beam = toucher.getdelegate(Beam)
            if (
                not actor
                or not actor.is_alive()
                or actor is self.owner
                or other_beam
                or self.dying
            ):
                return None
            bs.emitfx(
                position=self.node.position,
                chunk_type='spark',
                velocity=self.node.velocity,
                count=65,
                scale=2.0,
                spread=0.8,
            )
            dmg = 20
            # ew.
            sfx = self.owner.moveset.sfx.get('beam_hit') 
            actor.handlemessage(
                DamageMessage(
                    damage=dmg,
                    spaz=self.owner,
                    type='maskedman_beam',
                )
            )
            sfx.play(position=self.node.position)
            self.handlemessage(bs.DieMessage())
            
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage(immediate=True))
        else:
            return super().handlemessage(msg)
        return None

class MaskedManKiller(CharacterMoveset):
    """who is this kid!"""
    is_killer = True
    chase_theme_dir = 'coolone'
    hitpoints = 2000

    move_speed = 0.8
    run_speed = 1.0

    ability1_cooldown = 4
    ability2_cooldown = 12
    ability3_cooldown = 5

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = babase.charstr(babase.SpecialChar.TOP_BUTTON)
    ability3_icon = babase.charstr(babase.SpecialChar.DPAD_CENTER_BUTTON)
    
    def __init__(self, spaz):
        super().__init__(spaz)
        self.is_dashing = False
        self.trap = None
        self.bashes = 0
        self.bash_sound = None
        self.bash_sound_len = 2
        self.bash_sound_index = 0
        self.current_bash_sound_list = None
        self.bash_reset_timer = None
        self.bashes_text = None
        self._mathnode = None

        self.sfx = {
            'punch': bs.getsound('punchSwish'),
            'punch_hit': bs.getsound('maskedman/bashed'),
            'killed_player': bs.getsound('maskedman/enemy_swept_away'),
            'beam_hit': bs.getsound('maskedman/heavy_damage'),
            # FUCK.
            'inst1': list(bs.getsound(f'maskedman/inst1-0{i + 1}') for i in range(self.bash_sound_len + 1)),
            'inst2': list(bs.getsound(f'maskedman/inst2-0{i + 1}') for i in range(self.bash_sound_len + 1)),
            'inst3': list(bs.getsound(f'maskedman/inst3-0{i + 1}') for i in range(self.bash_sound_len + 1)),
            'cheer': bs.getsound('maskedman/cheer'),
            'prepare': bs.getsound('maskedman/enemy_turn'),
            'beam_shoot': bs.getsound('explosion01'),
        }

    def ability3(self) -> None:
        self.play('punch')
        self.spaz.impulse(x=7, y=2)
    
    def ability2(self) -> None:
        def shoot():
            if not self.spaz.node:
                return
            self.spaz.node.punch_pressed = True
            try: 
                bs.timer(0, bs.Call(setattr, self.spaz.node, 'punch_pressed', False))
            except: 
                pass
            x = self.spaz.node.move_left_right
            z = -self.spaz.node.move_up_down
            pos = self.spaz.node.position
            pos = (
                pos[0] + x,
                pos[1],
                pos[2] + z,
            )
            beam = Beam(
                position=pos,
                owner=self.spaz,
            ).autoretain()
            beam.node.velocity = (x*20, 0, z*20)
            mag = -400
            ppos = self.spaz.node.position
            punchdir = self.spaz.node.velocity
            self.spaz.node.handlemessage(
                'kick_back',
                ppos[0],
                ppos[1],
                ppos[2],
                punchdir[0],
                punchdir[1],
                punchdir[2],
                mag,
            )
            self.play('beam_shoot')
        self.play('prepare')
        time = 1.4
        self.spaz.node.handlemessage('celebrate_l', time*1000)
        bs.timer(1.4, shoot)

    def ability1(self) -> None:
        self._punched_nodes = set()
        self.play('punch')
        
        self.spaz.node.punch_pressed = True
        try: 
            bs.timer(0, bs.Call(setattr, self.spaz.node, 'punch_pressed', False))
        except: 
            pass
    
    def getspeed(self, 
            should_abs: bool = True, 
            decimals: int = 2, 
            ignore_y: bool = True
    ):
        vx, vy, vz = self.spaz.node.velocity
        components = (vx, vz) if ignore_y else (vx, vy, vz)
        # absolute-ize the result if we should
        if should_abs:
            value = abs(max(components, key=abs))
        else:
            value = max(components)
        # yep, theres your speed!
        return round(value, decimals)
    
    def play(self, sound: str):
        if not self.spaz.node:
            return
        self.play_sound(sound, position=self.spaz.node.position)
    
    def random_play(self, sound: str):
        this_list = self.sfx.get(sound)
        if not this_list:
            return
        choice = random.choice(this_list)
        choice.play(position=self.spaz.node.position)
    
    def update_text(self):
        text = self.bashes_text
        mathnode = self._mathnode
        if not mathnode:
            mathnode = self._mathnode = bs.newnode(
                'math',
                owner=self.spaz.node,
                attrs={'input1': (0, 1.7, 0), 'operation': 'add'},
            )
            self.spaz.node.connectattr('torso_position', mathnode, 'input2')
        if not text:
            text = self.bashes_text = bs.newnode(
                'text',
                owner=self.spaz.node,
                attrs={
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'scale': 0.011,
                    'color': (0.9, 0.9, 1),
                    'opacity': 0,
                    'h_align': 'center',
                },
            )
            mathnode.connectattr('output', text, 'position')
        text.text = f'*{self.bashes}*'
        mnode = self._mathnode
        text = self.bashes_text
        new_opa = 0 if not self.bashes else 1
        bs.animate(
            text,
            'opacity',
            {
                0: text.opacity,
                0.07: new_opa,
            }
        )
        # jump upwards and scale up
        bs.animate(
            text,
            'scale',
            {
                0: 0.011,
                0.05: 0.021,
                0.15: 0.011,
            }
        )
        bs.animate_array(
            mathnode, 
            'input1', 
            3,
            {
                0: (0, 1.7, 0),
                0.05: (0, 2, 0),
                0.1: (0, 2.1, 0),
                0.2: (0, 1.7, 0),
            }
        )

    def reset_bashes(self):
        PopupText(
            f'{self.bashes} HITS',
            position=self.spaz.node.position,
            color=(0.8, 0.9, 1),
            scale=1.35,
        ).autoretain()
        self.bash_sound_index = 0
        self.bashes = 0
        self.current_bash_sound_list = None
        self.update_text()
    
    def handle_bashes(self):
        self.bash_sound_index += 1
        self.bashes += 1
        if self.bash_sound_index > self.bash_sound_len:
            self.bash_sound_index = 0
        self.update_text()
        if self.bashes >= 16:
            self.reset_bashes()
            self._last_used_1 = (
                self._last_used_1 - 
                (self.ability1_cooldown - 6)
            )
            self.play('cheer')
        sfx_list = self.current_bash_sound_list
        if not sfx_list:
            sfx_list = self.current_bash_sound_list = random.choice([
                self.sfx['inst1'],
                self.sfx['inst2'],
                self.sfx['inst3'],
            ])
        index = self.bash_sound_index
        sound = sfx_list[index]
        self.bash_sound = bs.NodeActor(
            bs.newnode(
                'sound',
                attrs={
                    'sound': sound,
                    'position': self.spaz.node.position,
                    'positional': True,
                    'loop': False,
                    'volume': 0.9,
                }
            )
        )
        self.bash_reset_timer = bs.Timer(1.2, self.reset_bashes)
    
    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode

        if node.getnodetype() != 'spaz':
            return
        
        dele = node.getdelegate(bs.Actor)

        if self.node_not_punched_nodes(node) and len(self._punched_nodes) == 0:
            dmg = 2
            # rigged but whatever
            dmg *= (self.getspeed(ignore_y=False) + 1)
            self._last_used_1 = (
                self._last_used_1 - 
                (self.ability1_cooldown - 0.3)
            )
            self.handle_bashes()
            node.handlemessage(
                DamageMessage(
                    damage=dmg,
                    spaz=self.spaz,
                    type='spaz_punch',
                    hurt_sound=None,
                )
            )
            if dele.hitpoints <= 0:
                x = self.spaz.node.move_left_right
                z = -self.spaz.node.move_up_down
                i = 0
                for _ in range(7):
                    bs.timer(i, lambda: node.handlemessage(
                            StunMessage(
                                duration=0,
                                knockback_settings={
                                    'x': 7,
                                    'y': 5,
                                    'direction': (x, 0, z),
                                }
                            )
                        )
                    )
                    i += 0.06
                self.play('killed_player')
            self.play('punch_hit')
            self._punched_nodes.add(node)

        return False
    
    