from django.template import Context, loader
from django.http import HttpResponse

def index(request):
    template = 'common/page.html'
    context = {
               "doc":"common/doc/doc.reactionners.html",
               "title":"Reactionners",
               "page":"reactionners",
               "form":"reactionners/form.reactionners.html"
               }
    t = loader.get_template(template)
    c = Context(context)
    return HttpResponse(t.render(c))