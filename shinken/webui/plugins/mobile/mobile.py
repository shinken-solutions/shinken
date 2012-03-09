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
from shinken.misc.sorter import worse_first

### Will be populated by the UI with it's own value
app = None

def main():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/mobile/")
        return


    all_imp_impacts = app.datamgr.get_important_elements()
    
    all_pbs = app.datamgr.get_all_problems()

    return {'app' : app, 'user' : user, 'impacts' : all_imp_impacts, 'problems' : all_pbs}


def impacts():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/mobile/")
        return


    all_imp_impacts = app.datamgr.get_important_elements()
    all_imp_impacts.sort(worse_first)
    
    
    return {'app' : app, 'user' : user, 'impacts' : all_imp_impacts}


def problems():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/mobile/")
        return

    all_pbs = app.datamgr.get_all_problems()

    return {'app' : app, 'user' : user, 'problems' : all_pbs}


pages = {main : { 'routes' : ['/mobile/main'], 'view' : 'mobile_main', 'static' : True},
         impacts : { 'routes' : ['/mobile/impacts'], 'view' : 'mobile_impacts', 'static' : True},
         problems : { 'routes' : ['/mobile/problems'], 'view' : 'mobile_problems', 'static' : True},
         }

