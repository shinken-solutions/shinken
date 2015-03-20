#!/usr/bin/python
import os
from shinken.bin import VERSION
os.environ['PBR_VERSION'] = VERSION

import setuptools


setuptools.setup(
    setup_requires=['pbr'],
    version=VERSION,
    pbr=True,
)
