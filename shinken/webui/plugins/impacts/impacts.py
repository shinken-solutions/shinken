

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
    impacts[1] = {'name' : 'Mails', 'status' : 'Critical', 'criticity' : 5, 'since' : 'one hour', 'output' : 'No mails can be send nor received', 'problems' : [1, 3]}
    impacts[2] = {'name' : 'ERP', 'status' : 'Critical', 'criticity' : 4, 'since' : 'one day', 'output' : '', 'problems' : [1]}
    impacts[3] = {'name' : 'FileShare@server', 'status' : 'Warning', 'criticity' : 4, 'since' : 'one hour', 'output' : 'No more file access', 'problems' : [1]}
    impacts[4] = {'name' : 'Print@server', 'status' : 'Warning', 'criticity' : 3, 'since' : 'one day', 'output' : 'Printer service is stopped', 'problems' : [1, 2]}
    
    problems = {}
    problems[1] = {'name' : 'router-us is Down since 93294 with output Return in Dummy 2'}
    problems[2] = {'name' : 'router-asia is Down since 93294 with output Return in Dummy 2'}
    problems[3] = {'name' : 'Mssql@db-server is Down since 93294 with output connexion failed'}

    imp_id = 4
    pb_id = 3
    for imp in all_imp_impacts:
        print "FIND A BAD SERVICE IN IMPACTS", imp.get_dbg_name()
        imp_id += 1
        impacts[imp_id] = {'name' : imp.get_name(), 'status' : imp.state, 'criticity' : imp.business_impact, 'since' : 'one hour', 'output' : imp.output, 'problems' : []}
        print "Got %d root problems" % len(imp.source_problems)
        for p in imp.source_problems:
            name = p.get_dbg_name()
            v = find_pb(problems, name)
            if v:
                print "Already got problem id", v
                impacts[imp_id]['problems'].append(v)
            else:
                # Create a new problem
                pb_id += 1
                problems[pb_id] = {'name' : name}
                print "Creating the problem", problems[pb_id]
                impacts[imp_id]['problems'].append(pb_id)

    return {'impacts' : impacts, 'problems' : problems}



pages = {show_impacts : { 'routes' : ['/impacts'], 'view' : 'impacts', 'static' : True}  }
