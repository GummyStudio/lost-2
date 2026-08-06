import traceback
import datetime
import sys

def startup():
    def auto_module_import():
        # import the modules...
        import babase as ba
        import bascenev1 as bs
        import bauiv1 as bui
        # and install them to the console
        globals = sys.modules['__main__'].__dict__
        globals['ba'] = ba
        globals['bs'] = bs
        globals['bui'] = bui
        globals['ga'] = bs.getactivity
        globals['gp'] = lambda: bs.getactivity().players
        globals['gs'] = bs.getsession
    # call it
    auto_module_import()
    def my_global_exception_hook(exc_type, exc_value, exc_traceback):
        import bauiv1 as bui
        global _last_error_time, _recent_error
        # convert a error to text
        error_text = ''.join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        
        _last_error_time = datetime.datetime.now()
        _recent_error = True
        print(error_text)
        bui.getsound('error').play(0.3)
        
    # Install the hook
    sys.excepthook = my_global_exception_hook