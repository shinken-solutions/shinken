### Will be populated by the UI with it's own value
app = None

# Our page
def get_page():
    pbs = app.datamgr.get_all_problems()
    print "get all problems:", pbs
    for pb in pbs :
        print pb.get_name()
    return {'app' : app, 'pbs' : pbs}



pages = {get_page : { 'routes' : ['/problems'], 'view' : 'problems', 'static' : True}}

