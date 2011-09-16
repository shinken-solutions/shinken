
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
