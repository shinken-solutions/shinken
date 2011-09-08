
### Will be populated by the UI with it's own value
app = None

# Main impacts view
def show_3dimpacts():
    return get_data()



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

    impacts = {}
    impacts[1] = {'name' : 'Mails', 'status' : 'Critical', 'criticity' : 5, 'since' : 'one hour', 'output' : 'No mails can be send nor received', 'problems' : [1, 3]}
    impacts[2] = {'name' : 'ERP', 'status' : 'Critical', 'criticity' : 4, 'since' : 'one day', 'output' : '', 'problems' : [1]}
    impacts[3] = {'name' : 'FileShare@server', 'status' : 'Warning', 'criticity' : 4, 'since' : 'one hour', 'output' : 'No more file access', 'problems' : [1]}
    impacts[4] = {'name' : 'Print@server', 'status' : 'Warning', 'criticity' : 3, 'since' : 'one day', 'output' : 'Printer service is stopped', 'problems' : [1, 2]}
    
    problems = {}
    problems[1] = {'name' : 'router-us is Down since 93294 with output Return in Dummy 2'}
    problems[2] = {'name' : 'router-asia is Down since 93294 with output Return in Dummy 2'}
    problems[3] = {'name' : 'Mssql@db-server is Down since 93294 with output connexion failed'}
    
    
    return {'impacts' : impacts, 'problems' : problems, 'app' : app}



pages = {show_3dimpacts : { 'routes' : ['/3dimpacts'], 'view' : 'threedimpacts', 'static' : True}}
