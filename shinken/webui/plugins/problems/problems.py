### Will be populated by the UI with it's own value
app = None

# Our page
def get_page():
    
    # First we look for the user sid
    # so we bail out if it's a false one
    sid = app.request.get_cookie("sid")
    
    user = app.get_user(sid)
    print "Impact give user", user

    if not app.is_valid(sid):
        return {'app' : app, 'pbs' : [], 'valid_user' : False, 'user' : None}
    

    pbs = app.datamgr.get_all_problems()
    print "get all problems:", pbs
    for pb in pbs :
        print pb.get_name()
    return {'app' : app, 'pbs' : pbs, 'valid_user' : True, 'user' : user}



pages = {get_page : { 'routes' : ['/problems'], 'view' : 'problems', 'static' : True}}

