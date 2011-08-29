

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
    # We need to output impacts:
    # 1 : Mails/Critical/criticity=5/since one hour/No mails can be send nor received   ---> 1, 2
    # 2 : ERP/Critical/criticiy=4/since one day/""       ---> 1
    # 3 : FileShare@server/warning/criticity=3/since one day/No more file access   ---> 1
    # 4 : Print@server/Warning/since one day/Printer service is stopped  ---> 1,2


    # problems:
    # 1 : router-us is Down since 93294 with output Return in Dummy 2
    # 2 : router-asia is Down since one hour with output connexion failed
    # 3 : db-server/Mssql is Warning since one hour with output connexion failed

    all_imp_impacts = app.datamgr.get_important_elements()
    all_imp_impacts.sort(hst_srv_sort)

    impacts = {}

    imp_id = 0
    for imp in all_imp_impacts:
        print "FIND A BAD SERVICE IN IMPACTS", imp.get_dbg_name()
        imp_id += 1
        impacts[imp_id] = imp

    return {'app' : app, 'impacts' : impacts}



pages = {show_impacts : { 'routes' : ['/impacts'], 'view' : 'impacts', 'static' : True}  }
