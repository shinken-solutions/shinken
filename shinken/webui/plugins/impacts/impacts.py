

# Global value that will be changed by the main app
app = None


# Main impacts view
#@route('/impacts')
#@view('impacts')
def show_impacts():
    return get_data()


def compare_impacts(imp1, imp2):
    # Get max business impact
    if imp1.business_impact > imp2.business_impact:
        return 1
    if imp2.business_impact > imp1.business_impact:
        return -1
    # OK here, same business_impact
    # Now get worse state
    if imp1.state_id > imp2.state_id:
        return 1
    if imp2.state_id > imp1.state_id:
        return -1
    # don't care so
    return 0
    

def find_pb(problems, name):
    for (i, pb) in problems.items():
        if pb['name'] == name:
            return i
    return None


def get_data():
    # We need to output impacts:
    # 1 : Mails/Critical/criticity=5/since one hour/No mails can be send nor received   ---> 1, 2
    # 2 : ERP/Critical/criticiy=4/since one day/""       ---> 1
    # 3 : FileShare@server/warning/criticity=3/since one day/No more file access   ---> 1
    # 4 : Print@server/Warning/since one day/Printer service is stopped  ---> 1,2


    # problems:
    # 1 : router-us is Down since 93294 with output Return in Dummy 2
    # 2 : router-asia is Down since one hour with output connexion failed
    # 3 : db-server/Mssql is Warning since one hour with output connexion failed

    all_imp_impacts = app.datamgr.get_important_impacts()
    all_imp_impacts.sort(compare_impacts)
    impacts = {}

    imp_id = 0
    for imp in all_imp_impacts:
        print "FIND A BAD SERVICE IN IMPACTS", imp.get_dbg_name()
        imp_id += 1
        impacts[imp_id] = imp

    return {'impacts' : impacts}



pages = {show_impacts : { 'routes' : ['/impacts'], 'view' : 'impacts', 'static' : True}  }
