
from __future__ import absolute_import

import sys

if sys.version_info[:2] <= (2, 6):
    try: # still try to import it from system:
        from importlib import *
    except ImportError:
        from ._importlib import *
else:
    from importlib import *
