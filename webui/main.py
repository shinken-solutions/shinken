# -*- coding: utf-8 -*-
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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


import sys
import os


my_dir = os.path.abspath(os.path.dirname(__file__))
# Got in my own dir, and add my path in sys.path
os.chdir(my_dir)
sys.path.append(my_dir)

from bottle import Bottle, run, static_file, view, route

# Debug
import bottle
bottle.debug(True)

# Main app object
#app = Bottle()



# Route static files css files
@route('/static/:path#.+#')
def server_static(path):
    #print "Getting static files from", os.path.join(my_dir, 'htdocs'), path
    return static_file(path, root=os.path.join(my_dir, 'htdocs'))




# hello/bla will use the hello_template.tpl template
@route('/hello/:name')
@view('hello_template')
def hello(name='World'):
    return dict(name=name)


# Output json
@route('/bla')
def bla():
    return {1:2}


# Main impacts view
#@app.route('/impacts')
#@view('impacts')
#def show_impacts():
#    return dict()

import impacts


print "Starting application"
run(host='0.0.0.0', port=8080)
