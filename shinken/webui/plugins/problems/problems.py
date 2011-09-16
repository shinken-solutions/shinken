### Will be populated by the UI with it's own value
app = None


# Our page
def get_page():
    
    # First we look for the user sid
    # so we bail out if it's a false one
#    sid = app.request.get_cookie("sid")
    

    user = app.get_user_auth()

    if not user:
        return {'app' : app, 'pbs' : [], 'valid_user' : False, 'user' : None, 'navi' : None}
 
    #We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '30'))
   

    pbs = app.datamgr.get_all_problems()

    total = len(pbs)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = 30
    navi = app.helper.get_navi(total, start, step=30)
    pbs = pbs[start:end]

#    print "get all problems:", pbs
#    for pb in pbs :
#        print pb.get_name()
    return {'app' : app, 'pbs' : pbs, 'valid_user' : True, 'user' : user, 'navi' : navi}



pages = {get_page : { 'routes' : ['/problems'], 'view' : 'problems', 'static' : True}}

