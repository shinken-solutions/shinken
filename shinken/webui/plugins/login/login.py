from shinken.webui.bottle import redirect

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
    is_auth = app.check_auth(login, password)

    if is_auth:
        app.response.set_cookie('user', login, secret=app.auth_secret)
        redirect("/problems")
    else:
        redirect("/login")

    return {'app' : app, 'is_auth' : is_auth}

pages = {get_page : { 'routes' : ['/login', '/login/'], 'view' : 'login'},
         auth : { 'routes' : ['/auth'], 'view' : 'auth', 'method' : 'POST'}
             }

