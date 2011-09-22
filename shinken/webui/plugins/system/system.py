### Will be populated by the UI with it's own value
app = None


def system_page():
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
    
    schedulers = app.datamgr.get_schedulers()
    brokers = app.datamgr.get_brokers()
    reactionners = app.datamgr.get_reactionners()
    receivers = app.datamgr.get_receivers()
    pollers = app.datamgr.get_pollers()

    return {'app' : app, 'user' : user, 'schedulers' : schedulers,
            'brokers' : brokers, 'reactionners' : reactionners,
            'receivers' : receivers, 'pollers' : pollers,
            }



pages = {system_page : { 'routes' : ['/system', '/system/'], 'view' : 'system'}}

