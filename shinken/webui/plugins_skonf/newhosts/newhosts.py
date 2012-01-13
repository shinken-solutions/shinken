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


from shinken.webui.bottle import redirect
from shinken.util import to_bool



### Will be populated by the UI with it's own value
app = None

# Our page. If the useer call /dummy/TOTO arg1 will be TOTO.
# if it's /dummy/, it will be 'nothing'
def get_newhosts():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    # we return values for the template (view). But beware, theses values are the
    # only one the tempalte will have, so we must give it an app link and the
    # user we are loggued with (it's a contact object in fact)
    return {'app' : app, 'user' : user}



def get_launch():
    print "Got forms in /newhosts/launch page"
    names = app.request.forms.get('names', '')
    use_nmap = to_bool(app.request.forms.get('use_nmap', '0'))
    use_vmware = to_bool(app.request.forms.get('use_vmware', '0'))
    
    print "Got in request form"
    print names
    print 'nmap?', use_nmap
    print 'vmware?', use_vmware

    return {'app' : app}



def get_scans():
    print "Got scans"
    return {'app' : app}

def get_results():
    print "Looking for hosts in pending aprouval"
    cur = app.db.discovered_hosts.find({})
    pending_hosts = [h for h in cur]
    return {'app' : app, 'pending_hosts' : pending_hosts}


# This is the dict teh webui will try to "load".
#  *here we register one page with both adresses /dummy/:arg1 and /dummy/, both addresses
#   will call the function get_page.
#  * we say taht for this page, we are using the template file dummy (so view/dummy.tpl)
#  * we said this page got some static stuffs. So the webui will match /static/dummy/ to
#    the dummy/htdocs/ directory. Bewere : it will take the plugin name to match.
#  * optional : you can add 'method' : 'POST' so this adress will be only available for
#    POST calls. By default it's GET. Look at the lookup module for sample about this.
pages = {get_newhosts : { 'routes' : ['/newhosts'], 'view' : 'newhosts', 'static' : True},
         get_launch : { 'routes' : ['/newhosts/launch'], 'view' : 'newhosts_launch', 'static' : True, 'method' : 'POST'},
         get_scans : { 'routes' : ['/newhosts/scans'], 'view' : 'newhosts_scans', 'static' : True},
         get_results : { 'routes' : ['/newhosts/results'], 'view' : 'newhosts_results', 'static' : True},
         }

