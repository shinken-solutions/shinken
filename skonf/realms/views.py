from django.template import Context, loader
from django.http import HttpResponse

def index(request):
    template = 'common/page.html'
    context = {
               "doc":"realms/doc/doc.realms.html",
               "title":"Realms",
               "page":"realms",
               "form":"realms/form.realms.html"
               }
    t = loader.get_template(template)
    c = Context(context)
    return HttpResponse(t.render(c))