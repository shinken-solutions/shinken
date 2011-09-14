

# Global value that will be changed by the main app
app = None



# Sort hosts and services by impact, states and co
def hst_srv_sort(s1, s2):
    if s1.business_impact > s2.business_impact:
        return -1
    if s2.business_impact > s1.business_impact:
        return 1
    # ok, here, same business_impact
    # Compare warn and crit state
    if s1.state_id > s2.state_id:
        return -1
    if s2.state_id > s1.state_id:
        return 1
    # Ok, so by name...
    return s1.get_full_name() > s2.get_full_name()



def show_impacts():
    # First we look for the user sid
    # so we bail out if it's a false one
    sid = app.request.get_cookie("sid")
    user = app.get_user(sid)
    print "Impact give user", user

    if not app.is_valid(sid):
        return {'app' : app, 'impacts' : {}, 'valid_user' : False, 'user' : user}

    
    all_imp_impacts = app.datamgr.get_important_elements()
    all_imp_impacts.sort(hst_srv_sort)

    impacts = {}

    imp_id = 0
    for imp in all_imp_impacts:
        print "FIND A BAD SERVICE IN IMPACTS", imp.get_dbg_name()
        imp_id += 1
        impacts[imp_id] = imp

    return {'app' : app, 'impacts' : impacts, 'valid_user' : True, 'user' : user}



pages = {show_impacts : { 'routes' : ['/impacts'], 'view' : 'impacts', 'static' : True}  }
