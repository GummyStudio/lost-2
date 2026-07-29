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


class WizardKiller(CharacterMoveset):
    """who is this kid!"""
    is_killer = True
    chase_theme_dir = 'masteryartful'
    hitpoints = 250

    move_speed = 0.75
    run_speed = 1.0

    ability1_cooldown = 2
    ability2_cooldown = 15
    ability3_cooldown = 18

    ability1_icon = babase.charstr(babase.SpecialChar.LEFT_BUTTON)
    ability2_icon = babase.charstr(babase.SpecialChar.DELETE)
    ability3_icon = babase.charstr(babase.SpecialChar.UP_ARROW)
    
    def __init__(self, spaz):
        super().__init__(spaz)
       
        self.sfx = {
            'punch': bs.getsound('punchSwish'),
           
        }
