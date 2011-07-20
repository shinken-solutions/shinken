### Will be populated by the UI with it's own value
app = None

# Our page
def get_page():
    return get_data()



def get_data():
    return {}



pages = {get_page : { 'routes' : ['/login', '/login/'], 'view' : 'login'}}

