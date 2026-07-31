from lost.lost import CharacterMoveset, AsymFactory
import bascenev1 as bs
import babase, random, math
from bascenev1lib.actor.popuptext import PopupText

class SalvatoreSurvivor(CharacterMoveset):
    is_killer = False
    hitpoints = 100

    move_speed = 0.85
    run_speed =  0.9
    ability1_cooldown = 0.0
    ability2_cooldown = 35
    ability3_cooldown = 40

    ability1_icon = ''
    ability2_icon = babase.charstr(babase.SpecialChar.FAST_FORWARD_BUTTON)
    ability3_icon = babase.charstr(babase.SpecialChar.MUSHROOM)

    def __init__(self, spaz):
        super().__init__(spaz)
        self.sfx = {
            'drink': bs.getsound('Bloxycola'),
            'womp': bs.getsound('BoowompSlateskin'),
            'slateskin': bs.getsound('Slateskin_Use_Sound_Effect')
        }
        self.slateskin_tex = bs.gettexture('shrapnel1Color')
        self.original_tex = self.spaz.node.color_texture
        self.original_colortex = self.spaz.node.color_mask_texture
        self.factory = AsymFactory.get()
        self.using_item = False
        self.in_slateskin = False
    
    def ability1_extra_conditions(self):
        return not self.using_item
    def ability2_extra_conditions(self):
        return not self.using_item
    def ability3_extra_conditions(self):
        return not self.using_item
    
    def speed(self):
        self.spaz.max_run_speed /= 0.05
        self.using_item = False
        if self.in_slateskin:
            self.play_sound('womp')
            return
        
        
        self.spaz.max_run_speed *= 1.44
        def stop():
            self.spaz.max_run_speed /= 1.44
        bs.timer(10, stop)
    
    def slateskin(self):
        self.using_item = False
        self.spaz.max_run_speed /= 0.05
        # already in slate skin, no need.
        if self.in_slateskin:
            return
        
        self.in_slateskin = True
        
        
        self.spaz.max_walk_speed *= 0.15
        self.play_sound('slateskin')
        
        self.spaz.node.color_texture = self.slateskin_tex
        self.spaz.node.color_mask_texture = bs.gettexture('bonesColorMask')
        self.spaz.damage_mult *= 0.15

        def stop():
            self.in_slateskin = False
            self.spaz.speed_boost(0.5)
            self.spaz.damage_mult /= 0.15
            self.spaz.max_walk_speed /= 0.15
            self.spaz.node.color_texture = self.original_tex
            self.spaz.node.color_mask_texture = self.original_tex
        bs.timer(10, stop)
    

    def ability1(self):
        pass
    def ability2(self):
        duration = 2
        self.spaz.max_run_speed *= 0.05
        self.using_item = True
        self.play_sound('drink')
        self.spaz.node.handlemessage('celebrate_l', duration*(1000))
        bs.timer(duration, self.speed)
    def ability3(self):
        duration = 0.8
        self.spaz.max_run_speed *= 0.05
        self.using_item = True
        self.spaz.node.handlemessage('celebrate_r', duration*(1000))
        bs.timer(duration, self.slateskin)

        
 
   
        