
### Will be populated by the UI with it's own value
app = None


# Main impacts view
#@route('/host')
def show_host(name):
    return get_data(name)


def get_data(name):
    h = app.datamgr.get_host(name)
    return {'app' : app, 'elt' : h}


def show_service(hname, desc):
    s = app.datamgr.get_service(hname, desc)
    return {'app' : app, 'elt' : s}


pages = {show_host : { 'routes' : ['/host/:name'], 'view' : 'eltdetail', 'static' : True}}

