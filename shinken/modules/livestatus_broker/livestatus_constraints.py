#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


class LiveStatusConstraints:
    """ Represent the constraints applied on a livestatus request """
    def __init__(self, filter_func, out_map, filter_map, output_map, without_filter):
        self.filter_func = filter_func
        self.out_map = out_map
        self.filter_map = filter_map
        self.output_map = output_map
        self.without_filter = without_filter
