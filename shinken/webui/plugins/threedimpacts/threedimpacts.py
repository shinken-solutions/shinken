### Will be populated by the UI with it's own value
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



def show_3dimpacts():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'app' : app, 'impacts' : [], 'valid_user' : False}

    all_imp_impacts = app.datamgr.get_important_elements()
    all_imp_impacts.sort(hst_srv_sort)


    return {'app' : app, 'impacts' : all_imp_impacts, 'valid_user' : True}



pages = {show_3dimpacts : { 'routes' : ['/3dimpacts'], 'view' : 'threedimpacts', 'static' : True}}
