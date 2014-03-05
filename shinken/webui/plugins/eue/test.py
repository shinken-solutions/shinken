from pymongo.connection import Connection

id="GLPI"
records = []
con = Connection('localhost')
db = con.shinken
if not db:
    app = None # app is not otherwise
    message = "Error : Unable to connect to mongo database"
    return {'app': app, 'eue_data': {}, 'message': message }

parts = eueid.split(".")
parts.pop(0)
id =  ".".join(parts)

records=[]
for feature in db.eue.find({'key': { '$regex': id } }).sort("start_time",1).limit(100):
    date = feature["start_time"]
    failed = 0
    succeed = 0
    total = 0
    for scenario,scenario_data in feature["scenarios"].items():
        if scenario_data["status"] == 0:
            succeed += 1
        else:
            failed += 1

    total = succeed + failed
    records.append({
        "date" : int(date),
        "succeed" : succeed,
        "failed" : failed,
        "total" : total
    })

print records
