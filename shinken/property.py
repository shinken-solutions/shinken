# -*- mode: python ; coding: utf-8 -*-

# Copyright (C) 2009-2011 :
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



from shinken.util import to_float, to_split, to_char, to_int

__all__ = ['UnusedProp', 'BoolProp', 'IntegerProp', 'FloatProp',
           'CharProp', 'StringProp', 'ListProp',
           'FULL_STATUS', 'CHECK_RESULT']

# Suggestion 
# Is this useful? see above
__author__ = "Hartmut Goebel <h.goebel@goebel-consult.de>"
__copyright__ = "Copyright 2010-2011 by Hartmut Goebel <h.goebel@goebel-consult.de>"
__licence__ = "GNU Affero General Public License version 3 (AGPL v3)"


FULL_STATUS = 'full_status'
CHECK_RESULT = 'check_result'


none_object = object()


class Property(object):
    """Baseclass of all properties.

    Same semantic for all subclasses (except UnusedProp): The property
    is required if, and only if, the default value is `None`.


    """
    
    
    
    def __init__(self, default=none_object, class_inherit=None,
                 unmanaged=False, help='', no_slots=False,
                 fill_brok=None, conf_send_preparation=None,
                 brok_transformation=None, retention=False,
                 retention_preparation=None, to_send=False,
                 override=False, managed=True):
                     
        """
        `default`: default value to be used if this property is not set.
                   If default is None, this property is required.

        `class_inherit`: List of 2-tuples, (Service, 'blabla') : must
                   set this property to the Service class with name
                   blabla. if (Service, None): must set this property
                   to the Service class with same name
        `unmanaged`: ....
        `help`: usage text
        `no_slots`: do not take this property for __slots__

        `fill_brok`: if set, send to broker. There are two categories:
                     FULL_STATUS for initial and update status,
                     CHECK_RESULT for check results
        `retention`: if set, we will save this property in the retention files
        `retention_preparation`: function, if set, will go this function before 
                     being save to the retention data

        Only for the inital call:

        conf_send_preparation: if set, will pass the property to this
                     function. It's used to 'flatten' some dangerous
                     properties like realms that are too 'linked' to
                     be send like that.

        brok_transformation: if set, will call the function with the
                     value of the property when flattening 
                     data is necessary (like realm_name instead of
                     the realm object).

        override : for scheduler, if the property must override the
                     value of the configuration we send it

        managed : property that is managed in Nagios but not in Shinken

        """
        
        self.default = default
        self.has_default = (default is not none_object)
        self.required = not self.has_default
        self.class_inherit = class_inherit or []
        self.help = help or ''
        self.unmanaged = unmanaged
        self.no_slots = no_slots
        self.fill_brok = fill_brok or []
        self.conf_send_preparation = conf_send_preparation
        self.brok_transformation = brok_transformation
        self.retention = retention
        self.retention_preparation = retention_preparation
        self.to_send = to_send
        self.override = override
        self.managed = managed
        self.unused = False


class UnusedProp(Property):
    """A unused Property. These are typically used by Nagios but
    no longer usefull/used by Shinken.

    This is just to warn the user that the option he uses is no more used
    in Shinken.
    
    """
    
    # Since this property is not used, there is no use for other
    # parameters than 'text'.
    # 'text' a some usage text if present, will print it to explain
    # why it's no more useful
    def __init__(self, text=None):

        if text is None:
            text = ("This parameter is no longer useful in the "
                    "Shinken architecture.")
        self.text = text
        self.has_default = False
        self.class_inherit = []
        self.unused = True
        self.managed = True


_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


class BoolProp(Property):
    """A Boolean Property.

    Boolean values are currently case insensitively defined as 0,
    false, no, off for False, and 1, true, yes, on for True).
    """
#    @staticmethod
    def pythonize(self, val):
        return _boolean_states[val.lower()]


class IntegerProp(Property):
    """Please Add a Docstring to describe the class here"""
#    @staticmethod
    def pythonize(self, val):
        return to_int(val)


class FloatProp(Property):
    """Please Add a Docstring to describe the class here"""
#    @staticmethod
    def pythonize(self, val):
        return to_float(val)


class CharProp(Property):
    """Please Add a Docstring to describe the class here"""
#    @staticmethod
    def pythonize(self, val):
        return to_char(val)


class StringProp(Property):
    """Please Add a Docstring to describe the class here"""
#    @staticmethod
    def pythonize(self, val):
        return val

class PathProp(StringProp):
    """ A string property representing a "running" (== VAR) file path """

class ConfigPathProp(StringProp):
    """ A string property representing a config file path """

class ListProp(Property):
    """Please Add a Docstring to describe the class here"""
#    @staticmethod
    def pythonize(self, val):
        return to_split(val)
