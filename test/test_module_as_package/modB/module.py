from __future__ import absolute_import, division, print_function, unicode_literals

from shinken.basemodule import BaseModule

properties = {
    'daemons': ['broker', 'scheduler'],
    'type': 'modB',
    'external': False,
    'phases': ['running'],
}

def get_instance(plugin):
    return ThisModule(plugin)

class ThisModule(BaseModule):
    pass

from .helpers import X as helpers_X
expected_helpers_X = 'B'
