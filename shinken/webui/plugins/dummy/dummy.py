### Will be populated by the UI with it's own value
app = None

# Our page
def get_page(arg1='nothing'):
    return get_data(arg1)



def get_data(arg1):
    return {'host_name' : arg1}



pages = {get_page : { 'routes' : ['/dummy/:arg1', '/dummy/'], 'view' : 'dummy', 'static' : True}}

