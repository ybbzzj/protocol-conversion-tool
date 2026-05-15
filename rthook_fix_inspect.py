"""
Runtime hook to fix inspect.getsource() for PyInstaller bundled apps
This allows libraries like 'datasets' to work after packaging
"""
import sys
import inspect

# Store original getsource
_original_getsource = inspect.getsource
_original_getsourcelines = inspect.getsourcelines
_original_findsource = inspect.findsource

def _get_py_filename(object):
    """Get the source file of a module, handling frozen apps"""
    if hasattr(object, '__module__'):
        module_name = object.__module__
        try:
            module = sys.modules.get(module_name)
            if module and hasattr(module, '__file__'):
                return module.__file__
        except (KeyError, AttributeError):
            pass
    
    # Fallback to original method
    return _original_findsource(object)[0].co_filename if hasattr(_original_findsource(object)[0], 'co_filename') else None

def patched_findsource(object):
    """Patched findsource that works with PyInstaller"""
    try:
        return _original_findsource(object)
    except OSError:
        # If original fails, try to get from module
        if hasattr(object, '__module__'):
            module_name = object.__module__
            module = sys.modules.get(module_name)
            if module and hasattr(module, '__file__'):
                # For frozen modules, return a dummy code object
                if getattr(sys, 'frozen', False):
                    # Create a fake code object
                    import types
                    code = types.CodeType(
                        0, 0, 0, 0, b'', (), (), (), '', '', 0, b''
                    )
                    return [code], -1
        raise

def patched_getsource(object):
    """Patched getsource that returns empty string for frozen modules"""
    try:
        return _original_getsource(object)
    except (OSError, TypeError):
        # For frozen modules, return empty string instead of failing
        if getattr(sys, 'frozen', False):
            return ''
        raise

def patched_getsourcelines(object):
    """Patched getsourcelines that works with frozen modules"""
    try:
        return _original_getsourcelines(object)
    except (OSError, TypeError):
        # For frozen modules, return empty lines
        if getattr(sys, 'frozen', False):
            return [], -1
        raise

# Apply patches
inspect.findsource = patched_findsource
inspect.getsource = patched_getsource
inspect.getsourcelines = patched_getsourcelines

print("[Inspect Patch] Applied patches to inspect module for frozen mode")
