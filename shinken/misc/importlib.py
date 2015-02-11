
from __future__ import absolute_import

import sys

# importlib was introduced in 2.7. It is also available as a backport
if sys.version_info[:2] < (2, 7):
    try:  # try to import the system-wide backported module
        from importlib import *
    except ImportError:  # load our bundled backported module
        from ._importlib import *
else:
    from importlib import *
