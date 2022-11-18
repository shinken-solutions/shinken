#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print("Error: you need the json or simplejson module for this script")
        sys.exit(0)

print("Argv", sys.argv)

# Case 1 mean host0 is the father of host1
if sys.argv[1] == 'case1':
    d = [[["host", "test_host_0"], ["host", "test_host_1"]]]
if sys.argv[1] == 'case2':
    d = [[["host", "test_host_2"], ["host", "test_host_1"]]]

f = open(sys.argv[2], 'wb')
f.write(json.dumps(d))
f.close()
