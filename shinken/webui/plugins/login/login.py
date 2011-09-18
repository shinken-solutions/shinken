from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None

# Our page
def get_page():
    return user_login()

def user_login():
    user = app.get_user_auth()
    if user:
        redirect("/problems")
    return {}

def user_login_redirect():
    redirect("/user/login")
    return {}

def user_logout():
    # To delete it, send the same, with different date
    user_name = app.request.get_cookie("user", secret=app.auth_secret)
    if user_name:
        app.response.set_cookie('user', False, secret=app.auth_secret, path='/')
    else:
        app.response.set_cookie('user', '', secret=app.auth_secret, path='/')
    redirect("/user/login")
    return {}

def user_auth():
    print "Got forms"
    login = app.request.forms.get('login', '')
    password = app.request.forms.get('password', '')
    is_auth = app.check_auth(login, password)

    if is_auth:
        app.response.set_cookie('user', login, secret=app.auth_secret, path='/')
        redirect("/problems")
    else:
        redirect("/user/login")

    return {'app' : app, 'is_auth' : is_auth}

pages = { user_login : { 'routes' : ['/user/login', '/user/login/'], 
                         'view' : 'login'},
          user_login_redirect : { 'routes' : ['/login'] },
          user_auth : { 'routes' : ['/user/auth'], 
                        'view' : 'auth', 
                        'method' : 'POST'},
          user_logout : { 'routes' : ['/user/logout'] }}

