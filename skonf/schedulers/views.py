# Create your views here.
from common.render import *

def index(request):
    content = render('schedulers/schedulers.html','')
    return output(content)
