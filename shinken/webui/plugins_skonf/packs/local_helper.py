#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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


def print_cat_tree(tree):
    print "Tree?", tree
    _id = tree['name'].replace('/', '__')
    name = tree['name']
    if name.startswith('/'):
        name = name[1:]
    nb = tree['nb']
    s = '<a href="/getpacks/%s"> %s (%d)</a> <ul id="cat-%s" class="nav nav-list">' % (name, name, nb, _id)

    print "My sons", tree['sons']
    for (_, node) in tree['sons'].iteritems():
        print "Sub is", node
        s += '<li>'
        s += print_cat_tree(node)
        s += '</li>'

    s += '</ul>'
    return s
