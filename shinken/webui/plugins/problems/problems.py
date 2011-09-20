### Will be populated by the UI with it's own value
app = None

import re

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

    search = app.request.GET.get('search', '')

    pbs = app.datamgr.get_all_problems()

    # Ok, if need, appli the search filter
    if search:
        print "SEARCHING FOR", search
        print "Before filtering", len(pbs)
        # We compile the patern
        pat = re.compile(search, re.IGNORECASE)
        new_pbs = []
        for p in pbs:
            if pat.search(p.get_full_name()):
                new_pbs.append(p)
                continue
            to_add = False
            for imp in p.impacts:
                if pat.search(imp.get_full_name()):
                    to_add = True
            for src in p.source_problems:
                if pat.search(src.get_full_name()):
                    to_add = True
            if to_add:
                new_pbs.append(p)

        pbs = new_pbs
        print "After filtering", len(pbs)

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
    return {'app' : app, 'pbs' : pbs, 'valid_user' : True, 'user' : user, 'navi' : navi, 'search' : search}



pages = {get_page : { 'routes' : ['/problems'], 'view' : 'problems', 'static' : True}}

