from django.template import Context, loader
from django.http import HttpResponse

def index(request):
    template = 'common/page.html'
    context = {
               "doc":"common/doc/doc.brokers.html",
               "title":"Brokers",
               "page":"brokers",
               "form":"brokers/form.brokers.html"
               }
    t = loader.get_template(template)
    c = Context(context)
    return HttpResponse(t.render(c))