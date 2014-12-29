
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

import helpers

expected_helpers_X = 'B'

