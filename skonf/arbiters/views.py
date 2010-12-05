from django.template import Context, loader
from django.http import HttpResponse

def index(request):
    template = 'common/page.html'
    context = {
               "doc":"common/doc/doc.arbiters.html",
               "title":"Arbiters",
               "page":"arbiters",
               "form":"arbiters/form.arbiters.html"
               }
    t = loader.get_template(template)
    c = Context(context)
    return HttpResponse(t.render(c))