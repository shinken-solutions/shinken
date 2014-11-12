
from __future__ import absolute_import

import sys

if sys.version_info[:2] <= (2, 6):
    from ._importlib import *
else:
    from importlib import *
