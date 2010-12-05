from django.template import Context, loader
from django.http import HttpResponse

def render(template,context):
    t = loader.get_template(template)
    c = Context(context)
    return t.render(c)

def output(data):
    return HttpResponse(data)
    
   
