

### Will be populated by the UI with it's own value
app = None

# Our page
def get_page():
    return get_data()



def get_data():
    return {}



def auth():
    print "Got forms"
    login = app.request.forms.get('login', '')
    password = app.request.forms.get('password', '')
    sid = app.check_auth(login, password)

    if sid is not None:
        app.response.set_cookie('user', login, secret=app.auth_secret)#'toto')

    return {'app' : app, 'sid' : sid}

pages = {get_page : { 'routes' : ['/login', '/login/'], 'view' : 'login'},
         auth : { 'routes' : ['/auth'], 'view' : 'auth', 'method' : 'POST'}
             }

