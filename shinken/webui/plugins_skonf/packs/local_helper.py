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
    nb = tree['nb']
    s = '%s (%d) <ul id="cat-%s">' % (name, nb, _id)
    
    print "My sons", tree['sons']
    for (_, node) in tree['sons'].iteritems():
        print "Sub is", node
        s += '<li>'
        s += print_cat_tree(node)
        s += '</li>'

    s += '</ul>'
    return s




def sort_cat_weigth(s1, s2):
    _, _, nb1 = s1
    _, _, nb2 = s2

    if nb1 < nb2:
        return -1
    if nb2 < nb1:
        return 1
    return 0

def sort_cat_name(s1, s2):
    _, name1, _, _ = s1
    _, name2, _, _ = s2
    if name1 < name2:
        return -1
    if name2 < name1:
        return 1
    return 0
    

def get_weight_tags(tags):
    print "FLAT Tags", tags

    new_tree = {}
    for (_id, name, nb) in ft:
        print "Oh a new node", name
        if not name in new_tree:
            print "Create new tree node", name
            new_tree[name] = (_id, name, 0)
        # We add our weigth to the current weigth of this name
        new_size = new_tree[name][2] + nb
        print "Set the size", new_size, "for", name, "was", new_tree[name][2] 
        new_tree[name] = (new_tree[name][0], new_tree[name][1], new_size)
        
    ft = new_tree.values()

    ft.sort(sort_cat_weigth)
    l = len(ft)
    i = 0
    new_tree = []
    for (_id, name, nb) in ft:
        i +=1
        s = 1 + float(i)/l
        new_tree.append( (_id, name, nb, s) )
    
    # Finally sort by name
    new_tree.sort(sort_cat_name)
    
    print "New tree", new_tree
    return new_tree
        


def get_flat_cat(tree):
    r = []
    _id = tree['name'].replace('/', '__')
    name = tree['name'].split('/')[-1].strip()
    nb = tree['nb']
    # Skip the root
    if name:
        r.append((_id, name, nb))
    for (_, node) in tree['sons'].iteritems():
        s = get_flat_cat(node)
        for i in s:
            r.append(i)
    return r
