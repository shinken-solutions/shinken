
### Will be populated by the UI with it's own value
app = None


def show_host(name):
    return get_data(name)


def depgraph_host(name):
    return get_data(name)

def get_data(name):
    h = app.datamgr.get_host(name)
    return {'app' : app, 'elt' : h}

def depgraph_srv(hname, desc):
    s = app.datamgr.get_service(hname, desc)
    return {'app' : app, 'elt' : s}

pages = {depgraph_host : { 'routes' : ['/depgraph/:name'], 'view' : 'depgraph', 'static' : True},
         depgraph_srv : { 'routes' : ['/depgraph/:hname/:desc'], 'view' : 'depgraph', 'static' : True},
         }
