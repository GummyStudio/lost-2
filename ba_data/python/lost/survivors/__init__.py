import os
import glob
import importlib
import inspect

# Find all module names in the current directory
module_files = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
modules = [
    os.path.basename(f)[:-3] for f in module_files 
    if os.path.isfile(f) and not f.endswith('__init__.py')
]

# Extract classes from each module
__all__ = []
for module_name in modules:
    # Dynamically import the module relative to this package
    module = importlib.import_module(f".{module_name}", package=__name__)
    
    # Find all classes defined inside that specific module
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Prevent importing classes imported from external libraries
        if obj.__module__ == module.__name__:
            globals()[name] = obj
            __all__.append(name)

# Clean up namespace
del os, glob, importlib, inspect, module_files, modules