#!/usr/bin/env python
#Copyright (C) 2009-2011 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Andreas Karfusehr, andreas@karfusehr.de
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

### Will be populated by the UI with it's own value
app = None


def depgraph_host(name):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'app' : app, 'elt' : None, 'valid_user' : False}

    h = app.datamgr.get_host(name)
    return {'app' : app, 'elt' : h, 'valid_user' : True}


def depgraph_srv(hname, desc):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'app' : app, 'elt' : None, 'valid_user' : False}

    s = app.datamgr.get_service(hname, desc)
    return {'app' : app, 'elt' : s, 'valid_user' : True}

pages = {depgraph_host : { 'routes' : ['/depgraph/:name'], 'view' : 'depgraph', 'static' : True},
         depgraph_srv : { 'routes' : ['/depgraph/:hname/:desc'], 'view' : 'depgraph', 'static' : True},
         }
