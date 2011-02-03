#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#The resultmodulation class is used for in scheduler modulation of resulsts
#like the return code or the output.

import time

from item import Item, Items
from shinken.util import to_split
from shinken.property import UnusedProp, BoolProp, IntegerProp, FloatProp, CharProp, StringProp, ListProp

class Resultmodulation(Item):
    id = 1#0 is always special in database, so we do not take risk here
    my_type = 'resultmodulation'

    properties = {'resultmodulation_name': StringProp(),
                  'exit_codes_match': ListProp(
            default=''),
                  'exit_code_modulation': StringProp(
            default=None),
                  'modulation_period': StringProp(
            default=None),
                  }
    running_properties = {}
    macros = {}


    #For debugging purpose only (nice name)
    def get_name(self):
        return self.resultmodulation_name


    def clean(self):
        pass


    #Make the return code modulation if need
    def module_return(self, return_code):
        #Only if in modulation_period of modulation_period == None
        if self.modulation_period == None or self.modulation_period.is_time_valid(time.time()):
            #Try to change the exit code only if a new one is defined
            if self.exit_code_modulation != None:
                #First with the exit_code_match
                if return_code in self.exit_codes_match:
                    return_code = self.exit_code_modulation

        return return_code


    #We override the pythonize because we have special cases that we do not want
    #to be do at running
    def pythonize(self):
        #First apply Item pythonize
        super(self.__class__, self).pythonize()

        #Then very special cases
        # Intify the exit_codes_match, and make list
        self.exit_codes_match = [ int(ec) for ec in getattr(self, 'exit_codes_match', []) ]

        if hasattr(self, 'exit_code_modulation'):
            self.exit_code_modulation = int(self.exit_code_modulation)
        else:
            self.exit_code_modulation = None


class Resultmodulations(Items):
    name_property = "resultmodulation_name"
    inner_class = Resultmodulation


    def linkify(self, timeperiods):
        self.linkify_rm_by_tp(timeperiods)


    #We just search for each timeperiod the tp
    #and replace the name by the tp
    def linkify_rm_by_tp(self, timeperiods):
        for rm in self:
            mtp_name = rm.modulation_period

            #The new member list, in id
            mtp = timeperiods.find_by_name(mtp_name)

            rm.modulation_period = mtp
