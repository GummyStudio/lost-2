from __future__ import annotations

import copy
import random

import babase
import bascenev1 as bs
from bascenev1lib.actor.popuptext import PopupText

from lost.character_moveset import CharacterMoveset
from lost.factory import AsymFactory, DamageMessage, StunMessage

# Below this critical voicelines are used.
CRITICAL_HP = 300
# Idle lines count as critical below this
IDLE_CRITICAL_HP = 500
# Input below this counts as standing still.
IDLE_DEADZONE = 0.2

# Set to True to make every status effect 
# on the hit table below always be applied irregardless of chance.
DEBUG_ALWAYS_APPLY_EFFECTS = False

VOICELINES = {
    'fall_damage': [
        'Oowww...',
        'Fuck...',
        'Who even put that there!?',
    ],
    'fall_damage_strong': [
        'AAAGGHHH!!',
        'OOOWWWW-HO-HO!!!',
        'MOTHHERFF...',
    ],
    'jabbed': [
        'AH! Damn it!',
        'Can SOMEONE help me out already!?',
        'This damn THING is CHASING ME!',
    ],
    'jabbed_critical': [
        'OOOHHH!!',
        "HEY!! I CAN'T DO THIS ALONE!!!",
        'CAANN SOMEONE HEEELLLPPPP!??!?',
        "I'M ABOUT TO DIIEEE!!",
        "IT'S MAULING ME TO FUCKIN' DEATH!!",
    ],
    'claw': [
        'Well, that was easy.',
    ],
    'claw_critical': [
        'GET... THE FUCK.. AWAY.',
        'OH I GOTTA GET THE HELL OUTTA HERE!',
    ],
    'hit_any': [
        'OOWW... What even hit me??!',
        'OW- Damn it!',
        'GHH- KNOCK IT OUT!!',
    ],
    'hit_any_critical': [
        'OOOHHHHHH!!',
        'GGGAAAAHHHHH!!!',
        'FUUUCKK!!',
    ],
    'enraged': [
        "I'll fucking KILL YOU.",
        "Don't get me MAADD!!!\nI'M BOUT TO GET MAADDD!!!",
        'WHY YOU LITTLE-',
    ],
    'idle': [
        'Should probably be doing something...\ninstead of standing here.',
        '...where is everybody?',
        'Well, I suppose this is nice.',
    ],
    'idle_critical': [
        "This is the end, isn't it...?",
        'Wh- what am I DOING!?',
        "I've got to get out of here...",
        'This is madness...',
    ],
    'bleed_out': [
        "Damn it.. if this doesn't stop\nsoon I'll be dead by then...",
        "I'm screwed, aren't I...",
    ],
}

# Effects live here, keyed by codename, and are triggered by specific damage
# types (see HIT_STATUS_EFFECTS) so other movesets don't need to be touched.
# Supported keys:
# timeout: seconds until the effect wears off
# speed_debuff: multiplier on walk/run speed
# prevent_abilities: list of ability numbers that are blocked
# bleed_out: (interval, hp) lost per tick (negative = regen)
# ability_cooldown_debuffs: {ability number: seconds added to cooldown}
# claw_stun_debuff: multiplier on claw stun time
# claw_damage_debuff: multiplier on claw damage

STATUS_EFFECTS = {
    'dizzy': {
        'timeout': 10,
        'speed_debuff': 0.95,
    },
    'burning': {
        'timeout': 11,
        'bleed_out': (0.3, 1),
    },
    'disoriented': {
        'timeout': 13,
        'speed_debuff': 0.9,
    },
    'injured_limb': {
        'timeout': 16,
        'prevent_abilities': [1],
        'bleed_out': (0.9, 1),
    },
    'regen': {
        'timeout': 10,
        'bleed_out': (0.2, -1),
    },
    'enraged': {
        'timeout': 16,
        'speed_debuff': 1.1,
        'claw_stun_debuff': 1.5,
        'claw_damage_debuff': 6,
        'ability_cooldown_debuffs': {1: -6},
        'bleed_out': (0.1, 0.5),
    },
}


def _always(hp: float) -> bool:
    return True


def _below(limit: float):
    return lambda hp: hp < limit


# damage type -> [(chance, status effect, condition(hitpoints))]
HIT_STATUS_EFFECTS = {
    # Explosive-ish, so kinda related to fire.
    'maskedman_beam': [(0.3, 'burning', _always)],
    'ninja_mine': [(0.1, 'burning', _always)],
    'ninja_fire_punch': [(0.8, 'burning', _always)],
    # Punchy stuff.
    'ninja_punch': [(0.01, 'dizzy', _below(600))],
    'spaz_punch': [(0.01, 'dizzy', _below(600))],
    'ali_punch': [(0.01, 'dizzy', _below(600))],
    'bones_punch': [(0.1, 'disoriented', _below(300))],
    'pixel_minion_punch': [
        (0.05, 'dizzy', _below(300)),
        (0.1, 'regen', _always),
        (0.4, 'enraged', _always),
    ],
    'ali_rush': [
        (0.2, 'dizzy', _always),
        (0.4, 'disoriented', _always),
        (0.05, 'burning', _always),
        # Limb hits can't be detected, but this kinda makes sense.
        (0.2, 'injured_limb', _always),
    ],
}


class ExpieSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 150

    description = (
        'this game is unupdated as fuck so i got bored and made this '
        'gummy if you remove this i swear to god '
        'ill kill you il fucking kill you. '
        "There's no limit to the larp!"
        "\n{'type': 'edit_text', 'color': (0, 0.8, 1)}"
        'Lore'
        "{'type': 'edit_text', 'color': 'default'}"
        'there was a stupid idiota who really likes a certain '
        'furry character a lot so he decides to add it to '
        'basically every single game ever'
        "{'type': 'separator'}"
        'the end Go home! Goodbye!'
    )
    ability1_description = 'Claw at a killer to shortly stun them.'
    ability2_description = 'todo - maybe dumb dash move'
    ability3_description = 'todo - idk yet'

    move_speed = 0.85
    run_speed = 0.9
    ability1_cooldown = 7
    ability2_cooldown = 0
    ability3_cooldown = 0

    ability1_icon = babase.charstr(babase.SpecialChar.SKULL)
    ability2_icon = 'X'
    ability3_icon = 'X'

    # -----------------------------------------------------------------------
    # Setup
    # -----------------------------------------------------------------------

    def __init__(self, spaz):
        super().__init__(spaz)
        self.factory = AsymFactory.get()

        self.sfx = {
            'enraged': bs.getsound('expie/enrage'),
            'enrage_end': bs.getsound('expie/enrage_end'),
            'start_bleeding': bs.getsound('expie/mortal_damage'),
            'bleed_spike': bs.getsound('expie/hurt'),
            'status_effect': bs.getsound('expie/feeling_strange'),
            'status_effect_relieved': bs.getsound('expie/heal'),
            'die': bs.getsound('expie/die'),
            'text_blip': bs.getsound('expie/blip'),
            'error': bs.getsound('expie/error'),
            'punch_swish': bs.getsound('punchSwish'),
            'clawed': bs.getsound('Hitggg'),
        }

        # Per-instance copy so effects can be tweaked without side effects.
        self._status_effects = copy.deepcopy(STATUS_EFFECTS)
        self._active_effects: list[str] = []
        self._expiry_timers: dict[str, bs.Timer] = {}
        self._bleed_timers: dict[str, bs.Timer] = {}
        self._prevented_abilities: set[int] = set()

        self._claw_dmg = 40
        self._claw_stun_time = 0.4
        self._punched_nodes: set = set()

        self._idle_seconds = 0
        self._idle_threshold = random.randint(9, 15)
        self._typewriter_timer: bs.Timer | None = None
        self._typewriter_desired_text = ''
        self._typewriter_chunk = 0

        self._enraged_sfx = bs.newnode(
            'sound',
            owner=self.spaz.node,
            attrs={
                'sound': bs.getsound('expie/enraged_loop'),
                'positional': True,
                'music': False,
                'volume': 0,
            },
        )
        self.spaz.node.connectattr('position', self._enraged_sfx, 'position')

        self._voiceline_text = self._make_text(
            color=(1, 0.5, 0.2),
            scale=1.1 / 100,
            h_align='center',
            v_align='bottom',
        )
        self._statuses_text = self._make_text(
            color=(1, 0, 0),
            scale=0.9 / 100,
            h_align='left',
            v_align='top',
            opacity=1,
        )
        self._follow_spaz(self._voiceline_text, (0, 1.7, 0))
        self._follow_spaz(self._statuses_text, (0.4, 1.3, 0))

        self._idle_tick_timer = bs.Timer(
            1, bs.WeakCall(self.idle_tick), repeat=True
        )

    def _make_text(self, **attrs) -> bs.Node:
        return bs.newnode(
            'text',
            owner=self.spaz.node,
            attrs={
                'flatness': 1,
                'shadow': 0.8,
                'in_world': True,
                **attrs,
            },
        )

    def _follow_spaz(self, node: bs.Node, offset: tuple) -> None:
        """Pin `node` to the spaz's position plus an offset."""
        math = bs.newnode(
            'math',
            owner=self.spaz.node,
            attrs={'input1': offset, 'operation': 'add'},
        )
        self.spaz.node.connectattr('position', math, 'input2')
        math.connectattr('output', node, 'position')

    def _stream_sound(self, sound: str, volume: float = 1) -> None:
        if not self.spaz.node:
            return
        self.play_sound(
            sound, volume=volume, position=self.spaz.node.position
        )

    def _emit_blood(self) -> None:
        bs.emitfx(
            position=self.spaz.node.position,
            chunk_type='sweat',
            velocity=tuple(random.uniform(-1.5, 1.5) for _ in range(3)),
            count=random.randint(15, 20),
            scale=1.8,
            spread=0.4,
        )

    def _gib(self) -> None:
        self.spaz.shatter(True)
        for _ in range(5):
            self._emit_blood()
        # Why
        bs.getsound('expie/gib').play(position=self.spaz.node.position)
        
    def idle_tick(self) -> None:
        if not self.spaz.node:
            return
        still = (
            abs(self.spaz.input_x) < IDLE_DEADZONE
            and abs(self.spaz.input_y) < IDLE_DEADZONE
        )
        if not still:
            self._idle_seconds = 0
            return

        self._idle_seconds += 1
        if self._idle_seconds > self._idle_threshold:
            self._idle_seconds = 0
            self._idle_threshold = random.randint(9, 15)
            self._health_voiceline('idle', IDLE_CRITICAL_HP)
            
    def _health_voiceline(self, base: str, threshold: float = CRITICAL_HP):
        critical = self.spaz.hitpoints < threshold
        self.play_voiceline(f'{base}_critical' if critical else base)

    def play_voiceline(self, codename: str) -> None:
        if not self.spaz.is_alive():
            return
        self._typewriter_desired_text = random.choice(VOICELINES[codename])
        self._typewriter_chunk = 0
        self._voiceline_text.text = ''
        bs.animate(self._voiceline_text, 'opacity', {0: 0, 0.05: 1})
        self._typewriter_timer = bs.Timer(
            0.01, bs.WeakCall(self._advance_typewriter), repeat=True
        )

    def _advance_typewriter(self) -> None:
        if not self.spaz.is_alive():
            self._typewriter_timer = None
            self._voiceline_text.opacity = 0
            return

        self._typewriter_chunk += 1
        self._voiceline_text.text = self._typewriter_desired_text[
            : self._typewriter_chunk
        ]
        self._stream_sound('text_blip')

        if self._typewriter_chunk >= len(self._typewriter_desired_text):
            self._typewriter_timer = None
            bs.animate(
                self._voiceline_text, 'opacity', {0: 1, 1: 1, 1.5: 0}
            )

    def _enrage(self) -> None:
        bs.animate_array(
            self.spaz.node,
            'color',
            3,
            {0: (1, 0, 0), 0.05: (0.8, 0.3, 0.3), 0.1: (1, 0, 0)},
            loop=True,
        )
        self._stream_sound('enraged')
        self._enraged_sfx.volume = 0.5
        self.play_voiceline('enraged')

    def _calm_down(self) -> None:
        player = self.spaz.source_player
        bs.animate_array(
            self.spaz.node,
            'color',
            3,
            {
                0: self.spaz.node.color,
                0.1: (0.5, 0.6, 0.9),
                0.4: getattr(player, 'color', (1, 1, 1)),
            },
        )
        self._enraged_sfx.volume = 0
        self._stream_sound('enrage_end')

    def _resolve_effect(self, effect: str | dict) -> tuple[str, dict | None]:
        """Returns (codename, definition). Dicts are accepted so other
        movesets can pass their own one-off effects."""
        if isinstance(effect, dict):
            return str(id(effect)), effect
        return effect, self._status_effects.get(effect)

    def _fail_unknown_effect(self, codename: str) -> None:
        # Strike this Expie so no further side effects can occur,
        # then raise.
        self._gib()
        raise RuntimeError(
            f"Status effect {codename} undefined/not found in Expie's "
            'moveset; Eradicating...'
        )

    def _update_status_text(self) -> None:
        self._statuses_text.text = '\n'.join(self._active_effects)

    def _apply_modifiers(self, effect: dict, applying: bool) -> None:
        """Applies (or exactly reverses) every stat change in `effect`."""
        sign = 1 if applying else -1

        def scale(value: float, factor: float) -> float:
            return value * factor if applying else value / factor

        if factor := effect.get('speed_debuff'):
            self.spaz.max_walk_speed = scale(self.spaz.max_walk_speed, factor)
            self.spaz.max_run_speed = scale(self.spaz.max_run_speed, factor)

        for num in effect.get('prevent_abilities', ()):
            if applying:
                self.prevent_ability(num)
            else:
                self.allow_ability(num)

        if factor := effect.get('claw_stun_debuff'):
            self._claw_stun_time = scale(self._claw_stun_time, factor)
        if factor := effect.get('claw_damage_debuff'):
            self._claw_dmg = scale(self._claw_dmg, factor)

        for num, delta in effect.get('ability_cooldown_debuffs', {}).items():
            attr = f'ability{num}_cooldown'
            setattr(self, attr, getattr(self, attr) + sign * delta)

    def apply_status_effect(
        self, effect: str | dict, timeout_inc: float = 0
    ) -> None:
        """Gives Expie a status effect.

        `timeout_inc` is how much more/less time it takes to wear off.
        """
        if not self.spaz.node:
            return
        codename, data = self._resolve_effect(effect)
        if data is None:
            self._fail_unknown_effect(codename)
        if codename in self._active_effects:
            return

        self._apply_modifiers(data, applying=True)

        if bleed := data.get('bleed_out'):
            interval, amount = bleed
            self._bleed_timers[codename] = bs.Timer(
                interval, bs.WeakCall(self._bleed_out, amount), repeat=True
            )

        self._active_effects.append(codename)
        timeout = data.get('timeout', 10) + timeout_inc
        self._expiry_timers[codename] = bs.Timer(
            timeout, bs.WeakCall(self.relieve_status_effect, effect)
        )

        if codename == 'enraged':
            self._enrage()
        self._update_status_text()
        self._stream_sound('status_effect')

    def relieve_status_effect(self, effect: str | dict) -> None:
        """Relieves Expie from one of their status effects."""
        if not self.spaz.node:
            return
        codename, data = self._resolve_effect(effect)
        if data is None:
            self._fail_unknown_effect(codename)
        if codename not in self._active_effects:
            return

        self._apply_modifiers(data, applying=False)
        self._bleed_timers.pop(codename, None)
        self._expiry_timers.pop(codename, None)
        self._active_effects.remove(codename)

        if codename == 'enraged':
            self._calm_down()
        self._update_status_text()
        self._stream_sound('status_effect_relieved')

    def _bleed_out(self, amount: float) -> None:
        """Drains hitpoints; a negative amount heals (regen)."""
        if not self.spaz.is_alive():
            return

        if amount < 0:  # Regen: heal, but never past max.
            self.spaz.hitpoints = min(self.hitpoints, self.spaz.hitpoints - amount)
            return

        if random.random() < 0.1:
            self._emit_blood()
        self._stream_sound('bleed_spike')
        # FIXME: a cooldown would be nice so this can't fire twice in a row.
        if random.random() < 0.01:
            self.play_voiceline('bleed_out')

        self.spaz.hitpoints -= amount
        if self.spaz.hitpoints <= 0:
            self.spaz.handlemessage(
                DamageMessage(damage=amount, type='bleed_out', hurt_sound=None)
            )

    def prevent_ability(self, num: int) -> None:
        self._prevented_abilities.add(int(num))

    def allow_ability(self, num: int) -> None:
        self._prevented_abilities.discard(int(num))

    def _ability_allowed(self, num: int) -> bool:
        allowed = num not in self._prevented_abilities
        if not allowed:
            self._stream_sound('error')
        return allowed

    def ability1_extra_conditions(self) -> bool:
        allowed = self._ability_allowed(1)
        if not allowed and 'injured_limb' in self._active_effects:
            PopupText(
                "Can't claw; Injured limb...",
                position=self.spaz.node.position,
                color=(0.8, 0.9, 1),
                scale=1.0,
            ).autoretain()
        return allowed

    def ability2_extra_conditions(self) -> bool:
        return self._ability_allowed(2)

    def ability3_extra_conditions(self) -> bool:
        return self._ability_allowed(3)

    def ability1(self) -> None:
        self._punched_nodes = set()
        self.spaz.node.punch_pressed = True
        self.spaz.node.punch_pressed = False
        self._stream_sound('punch_swish')

    def ability2(self) -> None:
        self._stream_sound('error')

    def ability3(self) -> None:
        self._stream_sound('error')

    def handle_spaz_punched_something(self, collision: bs.Collision) -> bool:
        node = collision.opposingnode
        if node.getnodetype() != 'spaz':
            return False
        if not self.node_not_punched_nodes(node):
            return False

        self._punched_nodes.add(node)
        node.handlemessage(
            DamageMessage(
                damage=self._claw_dmg,
                spaz=self.spaz,
                type='expie_claw',
                hurt_sound=None,
            )
        )
        node.handlemessage(
            StunMessage(
                duration=self._claw_stun_time,
                knockback_settings={
                    'x': 18,
                    'y': 9,
                    'direction': node.velocity,
                },
            )
        )
        self.play_sound('clawed', position=node.position)
        bs.emitfx(
            position=self.spaz.node.position,
            chunk_type='spark',
            velocity=self.spaz.node.velocity,
            count=random.randint(30, 55),
            scale=0.8,
            spread=0.3,
        )
        if random.random() < 0.2:
            self._health_voiceline('claw')
        return False
        
    def handle_impact_damage(self, mag: float) -> bool:
        self.play_voiceline('fall_damage_strong' if mag >= 5 else 'fall_damage')
        # A hard enough fall leaves us disoriented.
        if mag >= 3.5:
            self.apply_status_effect('disoriented', 2 / mag)
        return True

    def handle_recieved_damage(self, damage: float, type: str) -> bool:
        if random.random() < 0.4:
            self._health_voiceline('jabbed' if 'punch' in type else 'hit_any')

        hp = self.spaz.hitpoints
        for chance, codename, condition in HIT_STATUS_EFFECTS.get(type, ()):
            if not condition(hp):
                continue
            if DEBUG_ALWAYS_APPLY_EFFECTS or random.random() < chance:
                self.apply_status_effect(codename)
        return True

    def spaz_lost_all_hp(self, type: str) -> None:
        super().spaz_lost_all_hp(type)
        # Stop any lingering bleed/expiry ticks.
        self._bleed_timers.clear()
        self._expiry_timers.clear()
        self._stream_sound('die')
        # No matter what; we shatter.
        # FIXME: Might look too dramatic for small-damage kills like bleed out.
        self._gib()
