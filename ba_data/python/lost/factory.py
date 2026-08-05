"""Base module for messages and the factory."""
from __future__ import annotations
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spaz import Spaz
from dataclasses import dataclass
import bascenev1 as bs

class DamageMessage:
    """ a message  that says how much damage someone should take"""

    def __init__(self, 
        damage: float = 0, 
        spaz: Spaz = None,
        type: str = 'normal',
        hurt_sound: str | None = None,
        visual_damage: float | None = None
    ):
        self.damage = damage
        self.spaz = spaz # the person who hit us
        self.hittype = type
        if hurt_sound:
            self.hurt_sound = getattr(AsymFactory.get(), hurt_sound, None)
        else:
            self.hurt_sound = None
        self.visual_damage = visual_damage
        
class StunMessage:
    """ a message that tells the person to be stunned for how long"""

    def __init__(
        self, 
        duration: float, 
        spaz: Spaz = None,
        type: str = 'normal',
        use_node_knockout_message: bool = False,
        knockback_settings: dict | None = None,
        hurt_sound: str | None = None
    ):
        self.duration = duration
        self.spaz = spaz # the person who hit us
        self.hittype = type
        self.node_knockout_message = use_node_knockout_message
        self.knockback_settings = knockback_settings
        if hurt_sound:
            self.hurt_sound = getattr(AsymFactory.get(), hurt_sound, None)
        else:
            self.hurt_sound = None
        # Example:
        {
            "direction": (0, 1, 0),
            "x": 800,
            "y": 30,
        }

class SurvivorDetectedMessage:
    """ send this to any object in need to detect a survivor. """

class KillerDetectedMessage:
    """ send this to any object in need to detect a killer. """

class SurvivorUnDetectedMessage:
    """ send this to any object in need to undetect a survivor. """

class KillerUnDetectedMessage:
    """ send this to any object in need to undetect a killer. """
    
@dataclass
class IngameButtonPressedMessage:
    """A message that tells a in-game 
    button it's been pressed or unpressed."""
    state: bool

class AsymFactory:
    """Base class utility for materials
    and sound effects."""
    _STORENAME = bs.storagename()

    @classmethod
    def get(cls):
        """Create and/or return the single shared instance of this class."""
        activity = bs.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = AsymFactory()
            activity.customdata[cls._STORENAME] = factory
        assert isinstance(factory, AsymFactory)
        return factory

   
    def __init__(self) -> None:
        self.player_death_sound = bs.getsound('playerDeath')
        self.lms_image_shake_sound = bs.getsound('scoreHit01')
        # Killer material.
        self.killer_material = bs.Material()
        self.survivors_won_sound = bs.getsound('boxingBell')
        self.killers_won_sound = bs.getsound('boxingBell')

        self.killer_material.add_actions(
            conditions=(
                'they_have_material',
                self.killer_material
                # They have our material, we shoulnt collide with them.
            ),
            actions=('modify_part_collision', 'collide', False),
       )

        # Survivor Material
        self.survivor_material = bs.Material()

        self.survivor_material.add_actions(
            conditions=(
                'they_have_material',
                self.survivor_material
                # They have our material, we shoulnt collide with them.
            ),
            actions=(
                ('modify_part_collision', 'collide', False),
            )
        )
        
        # Killer doors.
        self.killer_door_material = bs.Material()
        # By default act like collision
        self.killer_door_material.add_actions(
            ('modify_part_collision', 'collide', True)
        )
        # If the coming object has a killer material, let them through
        self.killer_door_material.add_actions(
            conditions=(
                'they_have_material',
                self.killer_material
            ),
            actions=('modify_part_collision', 'collide', False),
        )
        
        self.killer_trap_object_material = bs.Material()
        # material that detects and activates stuf

        # By default, we only collide with floors.
        self.killer_trap_object_material.add_actions(
             ('modify_part_collision', 'collide', False)
        )
        self.killer_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().footing_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
            ),
        )
        self.killer_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                self.survivor_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', SurvivorDetectedMessage()),
                ('message', 'our_node', 'at_disconnect', SurvivorUnDetectedMessage())
            ),
        )


        self.survivor_trap_object_material = bs.Material()
        # material that detects and activates stuf

        # By default, we only collide with floors.
        self.survivor_trap_object_material.add_actions(
             ('modify_part_collision', 'collide', False)
        )
        self.survivor_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().footing_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
            ),
        )
        self.survivor_trap_object_material.add_actions(
            conditions=(
                'they_have_material',
                self.killer_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', KillerDetectedMessage()),
                ('message', 'our_node', 'at_disconnect', KillerUnDetectedMessage())
            ),
        )
        
        this_mat = self.no_wall_collide = bs.Material()
        #: Material that doesn't collide with walls (or footing).

        # Duh
        this_mat.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().footing_material
            ),
            actions=(
                ('modify_part_collision', 'collide', False),
            ),
        )

        this_mat = self.only_wall_collide = bs.Material()
        #: Material that only collide with walls (or footing).
        this_mat.add_actions(('modify_part_collision', 'collide', False))

        # Duh
        this_mat.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().footing_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
            ),
        )

        self.no_collision = bs.Material()
        # collide with nothin
        self.no_collision.add_actions(('modify_part_collision', 'collide', False))

        self.destroy_on_wall_collide = bs.Material()
        # destroy when colliding with a wall
        self.destroy_on_wall_collide.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().footing_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('message', 'our_node', 'at_connect', bs.DieMessage()),
            ),
        )
        this_mat = self.button_material = bs.Material()
        # collide with nothin
        this_mat.add_actions(('modify_part_collision', 'collide', False))
        # destroy when colliding with a wall
        this_mat.add_actions(
            conditions=(
                'they_have_material',
                SharedObjects.get().player_material
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('message', 'our_node', 'at_connect', IngameButtonPressedMessage(True)),
                ('message', 'our_node', 'at_disconnect', IngameButtonPressedMessage(False)),
            ),
        )