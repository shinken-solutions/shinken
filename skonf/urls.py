from django.conf.urls.defaults import *
from django.conf import settings
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^sconf/', include('sconf.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^$','reactionners.views.index'),
    (r'^arbiters','arbiters.views.index'),
    (r'^realms','realms.views.index'),
    (r'^schedulers','schedulers.views.index'),    
    (r'^pollers','pollers.views.index'),
    (r'^reactionners','reactionners.views.index'),
    (r'^brokers','brokers.views.index'),    
    (r'^modules','modules.views.index'),    
    (r'^tpl','tpl.views.index'),    
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATICFILES_ROOT}),
    )
    