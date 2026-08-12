import traceback
import datetime
import sys
import babase as ba
import bascenev1 as bs
import bauiv1 as bui
from .discordrp_handler import RichPresence

def startup():
    def auto_module_import():
        globals = sys.modules['__main__'].__dict__
        globals['ba'] = ba
        globals['bs'] = bs
        globals['bui'] = bui
        globals['ga'] = bs.getactivity
        globals['gp'] = lambda: bs.getactivity().players
        globals['gs'] = bs.getsession
    auto_module_import()
    def global_exception_hook(exc_type, exc_value, exc_traceback):
        global _last_error_time, _recent_error
        # convert a error to text
        error_text = ''.join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        
        _last_error_time = datetime.datetime.now()
        _recent_error = True
        print(error_text)
        bui.getsound('error').play(1)
        bui.screenmessage('error occured pls check console ill replace this later :3')
    sys.excepthook = global_exception_hook
    # ok get rpc started!!! yay
    ba.apptimer(3, RichPresence)