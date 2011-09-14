
### Will be populated by the UI with it's own value
app = None


# Main impacts view
#@route('/host')
def show_host(name):
    # First we look for the user sid
    # so we bail out if it's a false one
    sid = app.request.get_cookie("sid")
    user = app.get_user(sid)
    print "Impact give user", user

    if not app.is_valid(sid):
        return {'app' : app, 'elt' : None, 'valid_user' : False, 'user' : user}

    # Ok, we can lookup it
    h = app.datamgr.get_host(name)
    return {'app' : app, 'elt' : h, 'valid_user' : True, 'user' : user}


def show_service(hname, desc):

    # First we look for the user sid
    # so we bail out if it's a false one
    sid = app.request.get_cookie("sid")
    user = app.get_user(sid)
    print "Impact give user", user

    if not app.is_valid(sid):
        return {'app' : app, 'elt' : None, 'valid_user' : False, 'user' : user}

    # Ok, we can lookup it :)
    s = app.datamgr.get_service(hname, desc)
    return {'app' : app, 'elt' : s, 'valid_user' : True, 'user' : user}


pages = {show_host : { 'routes' : ['/host/:name'], 'view' : 'eltdetail', 'static' : True},
         show_service : { 'routes' : ['/service/:hname/:desc'], 'view' : 'eltdetail', 'static' : True},
         }

