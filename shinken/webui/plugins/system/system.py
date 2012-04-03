#!/usr/bin/env python
# Copyright (C) 2009-2012 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Andreas Karfusehr, andreas@karfusehr.de
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

import time

### Will be populated by the UI with it's own value
app = None

def system_page():
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
    
    schedulers = app.datamgr.get_schedulers()
    brokers = app.datamgr.get_brokers()
    reactionners = app.datamgr.get_reactionners()
    receivers = app.datamgr.get_receivers()
    pollers = app.datamgr.get_pollers()

    return {'app' : app, 'user' : user, 'schedulers' : schedulers,
            'brokers' : brokers, 'reactionners' : reactionners,
            'receivers' : receivers, 'pollers' : pollers,
            }

def system_widget():
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
    
    schedulers = app.datamgr.get_schedulers()
    brokers = app.datamgr.get_brokers()
    reactionners = app.datamgr.get_reactionners()
    receivers = app.datamgr.get_receivers()
    pollers = app.datamgr.get_pollers()

    wid = app.request.GET.get('wid', 'widget_system_'+str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')
    print "SYSTEM COLLAPSED?", collapsed, type(collapsed)

    options = {'key' : {'value' : 1, 'type' : 'int'},
               'place' : {'value' : '', 'type' : 'select', 'values' : ['Paris', 'Bordeaux', 'Marseille']}
               }

    return {'app' : app, 'user' : user, 'schedulers' : schedulers,
            'brokers' : brokers, 'reactionners' : reactionners,
            'receivers' : receivers, 'pollers' : pollers, 'wid' : wid,
            'collapsed' : collapsed, 'options' : options
            }


def show_log():
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
    
    schedulers = app.datamgr.get_schedulers()
    brokers = app.datamgr.get_brokers()
    reactionners = app.datamgr.get_reactionners()
    receivers = app.datamgr.get_receivers()
    pollers = app.datamgr.get_pollers()

    return {'app' : app, 'user' : user, 'schedulers' : schedulers,
            'brokers' : brokers, 'reactionners' : reactionners,
            'receivers' : receivers, 'pollers' : pollers,
            }

pages = {system_page : { 'routes' : ['/system', '/system/'], 'view' : 'system', 'static' : True},
         system_widget : { 'routes' : ['/widget/system'], 'view' : 'system_widget', 'static' : True, 'widget' : ['dashboard']},
         show_log : { 'routes' : ['/system/log'], 'view' : 'log', 'static' : True},
         }
