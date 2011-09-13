### Will be populated by the UI with it's own value
app = None

# We will need external commands here
import time
from shinken.external_command import ExternalCommand, ExternalCommandManager

# Our page
def get_page(cmd=None):

    # First we look for the user sid
    # so we bail out if it's a false one
    sid = app.request.get_cookie("sid")
    if not app.is_valid(sid):
        return {'status' : 401, 'text' : 'Invalid session'}


    now = int(time.time())
    print "Ask us an /action page", cmd
    elts = cmd.split('/')
    cmd_name = elts[0]
    cmd_args = elts[1:]
    print "Got command", cmd_name
    print "And args", cmd_args
    
    # Check if the command exist in the external command list
    if cmd_name not in ExternalCommandManager.commands:
        return {'status' : 404, 'text' : 'Unknown command %s' % cmd_name}

    extcmd = '[%d] %s' % (now, ';'.join(elts))
    print "Got the; form", extcmd
    
    # Ok, if good, we can launch the command
    extcmd = extcmd.decode('utf8', 'replace')
    e = ExternalCommand(extcmd)
    print "Creating the command", e.__dict__
    app.push_external_command(e)

    return {'status' : 200, 'text' : 'Command launched'}



pages = {get_page : { 'routes' : ['/action/:cmd#.+#']}}

