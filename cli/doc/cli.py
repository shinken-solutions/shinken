#!/usr/bin/env python

# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


import os

from shinken.log import logger

# Will be populated by the shinken CLI command
CONFIG = None



############# ********************        SERVE           ****************###########
def serve(port):
    port = int(port)
    logger.info("Serving documentation at port %s", port)
    import SimpleHTTPServer
    import SocketServer
    doc_dir   = CONFIG['paths']['doc']
    html_dir  = os.path.join(doc_dir, 'build', 'html')
    os.chdir(html_dir)
    try:
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(("", port), Handler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception, exp:
        logger.error(exp)

def do_serve(port='8080'):
    if port is None:
        port = '8080'
    logger.debug("WILL CALL serve with %s", port)
    serve(port)




################" *********************** COMPILE *************** ##################
def _compile():
    try:
        from sphinx import main
    except ImportError:
        logger.error('Cannot import the sphinx lib, please install it')
        return
    doc_dir     = CONFIG['paths']['doc']
    html_dir = os.path.join(doc_dir, 'build', 'html')
    doctrees_dir = os.path.join(doc_dir, 'build', 'doctrees')
    source_dir = os.path.join(doc_dir, 'source')

    try:
        s = 'sphinx-build -b html -d %s %s %s' % (doctrees_dir, source_dir, html_dir)
        args = s.split(' ')
        main(args)
    except Exception, exp:
        logger.error(exp)
    return

def do_compile():
    logger.debug("CALL compile")
    _compile()


exports = {
    do_serve : {
        'keywords': ['doc-serve'],
        'args': [
            {'name' : '--port', 'default':'8080', 'description':'Port to expose the http doc. Default to 8080'},

            ],
        'description': 'Publish the online doc on this server'
        },

    do_compile  : {'keywords': ['doc-compile'], 'args': [],
                  'description': 'Compile the doc before enabling it online'
                  },
    }
