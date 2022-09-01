# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

import io
import six
import traceback
if six.PY2:
    import cPickle as pickle
else:
    import pickle
from shinken.safepickle import SafeUnpickler


class SerializeError(Exception):
    pass


def serialize(obj):
    """
    Serializes an object to be sent through an HTTP request, for instance

    :param mixed obj: The object to serialize
    :rtype: bytes
    :terun: The serialized object
    """
    try:
        return pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    except pickle.PickleError as e:
        logger.error("Failed to serialize object: %s", e)
        logger.error(traceback.format_exc())
        raise SerializeError(e)


def deserialize(payload):
    """
    Deserializes an object got from an HTTP request, for instance

    :param bytes obj: The payload to deserialize
    :rtype: bytes
    :terun: The serialized object
    """
    try:
        if hasattr(payload, 'read'):
            return SafeUnpickler(payload).load()
        else:
            return SafeUnpickler(io.BytesIO(payload)).load()
    except pickle.PickleError as e:
        logger.error("Failed to serialize payload: %s", e)
        logger.error(traceback.format_exc())
        raise SerializeError(e)
