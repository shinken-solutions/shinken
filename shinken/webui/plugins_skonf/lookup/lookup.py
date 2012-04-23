### Will be populated by the UI with it's own value
app = None

try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error : you need the json or simplejson module"
        raise


def lookup(name=''):
    app.response.content_type = 'application/json'

    user = app.get_user_auth()
    if not user:
        return []

    if len(name) < 3:
        print "Lookup %s too short, bail out" % name
        return []

    hnames = (h.host_name for h in app.datamgr.get_hosts())
    r  = [n for n in hnames if n.startswith(name)]

    return json.dumps(r)


def lookup_tag_post():
    app.response.content_type = 'application/json'

#    user = app.get_user_auth()
#    if not user:
#        return []

    name = app.request.forms.get('value')
    if not name or len(name) < 3:
        print "Lookup POST %s too short, bail out" % name
        return []

    print "Lookup for", name
    tags = set()
    for h in app.host_templates.values():
        print "Template", h
        if hasattr(h, 'name'):
            tags.add(h.name)
    r  = [n for n in tags if n.startswith(name)]

    print "RES", r

    return json.dumps(r)



pages = {lookup_tag_post : { 'routes' : ['/lookup/tag'] , 'method' : 'POST'}
         }

