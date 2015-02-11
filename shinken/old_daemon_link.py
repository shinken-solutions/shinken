
import sys
import inspect
import warnings


def deprecation(msg, stacklevel=4):
    warnings.warn(msg, DeprecationWarning, stacklevel=stacklevel)


def make_deprecated_daemon_link(new_module):
    stack = inspect.stack()
    full_mod_name = stack[1][0].f_locals['__name__']
    mod_name = full_mod_name.split('.')[-1]
    deprecation(
        "{fullname} is deprecated module path ; "
        "{name} must now be imported from shinken.objects.{name}"
        " ; please update your code accordingly".format(name=mod_name, fullname=full_mod_name)
    )
    sys.modules[full_mod_name] = new_module
