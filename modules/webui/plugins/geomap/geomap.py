#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
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

try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error: you need the json or simplejson module"
        raise


from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None


# Our page. If the user call /dummy/TOTO arg1 will be TOTO.
# if it's /dummy/, it will be 'nothing'
def get_page():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    return {'app': app, 'user': user}


def get_json():
    app.response.content_type = 'application/json'
    
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")
        return
    

    d = {
        "paris": {
            "comments": [],
            "h_equal": [],
            "h_match": [
                "srv-.*"
                ],
            "hg_equal": [
                "REALM_PARIS"
                ],
            "hg_match": [],
            "hosts": {
                "down": [
                    {
                        "host_groups": "",
                        "host_name": "srv-emc-clariion",
                        "last_hard_state_change": "1363775109",
                        "state": "1"
                        },
                    {
                        "host_groups": "",
                        "host_name": "srv-esx",
                        "last_hard_state_change": "1363775057",
                        "state": "1"
                        }
                    ],
                "up": [
                    {
                        "host_groups": "",
                        "host_name": "srv-checkways",
                        "last_hard_state_change": "1363774995",
                        "state": "0"
                    },
                    {
                        "host_groups": "",
                        "host_name": "srv-exchange",
                        "last_hard_state_change": "1363775080",
                        "state": "0"
                        },
                    {
                        "host_groups": "",
                        "host_name": "srv-exchange2",
                        "last_hard_state_change": "1363774975",
                    "state": "0"
                        }
                    ]
                },
            "position": {
                "latitude": "39.044036",
                "longitude": "-77.48709"
                },
            "services": {
                "critical": [
                    {
                        "comments_with_info": "",
                        "description": "Disks",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-emc-clariion",
                        "last_hard_state_change": "1363775192",
                        "plugin_output": "[Errno 2] No such file or directory",
                        "state": "2"
                        },
                    {
                        "comments_with_info": "",
                        "description": "FC-ports",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-emc-clariion",
                        "last_hard_state_change": "1363775154",
                        "plugin_output": "[Errno 2] No such file or directory",
                        "state": "2"
                        }
                    ],
                "ok": [
                    {
                        "comments_with_info": "",
                        "description": "Cpu",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-exchange",
                        "last_hard_state_change": "1363775099",
                        "plugin_output": "OK (Sample Period 301 sec) - Average CPU Utilisation 1.13%",
                        "state": "0"
                        },
                    {
                        "comments_with_info": "",
                        "description": "Disks",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-exchange",
                        "last_hard_state_change": "1363775043",
                        "plugin_output": "OK - C: Total=838.23GB, Used=72.59GB (8.7%), Free=765.64GB (91.3%)",
                        "state": "0"
                        }
                    ],
                "unknown": [
                                    {
                        "comments_with_info": "",
                        "description": "BigProcesses",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-exchange-cas",
                        "last_hard_state_change": "0.0",
                        "plugin_output": "INIFILE and/or INIDIR are set but there were no ini file(s) or an error occurred trying to read them.",
                        "state": "3"
                                        },
                                    {
                        "comments_with_info": "",
                        "description": "Cpu",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-exchange-cas",
                        "last_hard_state_change": "0.0",
                        "plugin_output": "UNKNOWN - The WMI query had problems. The error text from wmic is: [librpc/rpc/dcerpc_connect.c:329:dcerpc_pipe_connect_ncacn_ip_tcp_recv()] failed NT status (c0000017) in dcerpc_pipe_connect_ncacn_ip_tcp_recv",
                        "state": "3"
                        }
                    ],
                "warning": [
                                    {
                        "comments_with_info": "",
                        "description": "BigProcessesWarn",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-exchange-cas",
                        "last_hard_state_change": "0.0",
                        "plugin_output": "INIFILE and/or INIDIR are set but there were no ini file(s) or an error occurred trying to read them.",
                        "state": "3"
                                        },
                                    {
                        "comments_with_info": "",
                        "description": "CpuWarn",
                        "host_comments_with_info": "",
                        "host_groups": "",
                        "host_name": "srv-exchange-cas",
                        "last_hard_state_change": "0.0",
                        "plugin_output": "UNKNOWN - The WMI query had problems. The error text from wmic is: [librpc/rpc/dcerpc_connect.c:329:dcerpc_pipe_connect_ncacn_ip_tcp_recv()] failed NT status (c0000017) in dcerpc_pipe_connect_ncacn_ip_tcp_recv",
                        "state": "3"
                        }
                    ]
                }
            }
        
        
        }
                
                    
            
                

    

    return json.dumps(d)


pages = {get_page: {'routes': ['/geomap', '/geomap/'], 'view': 'geomap', 'static': True},
         get_json: {'routes': ['/geomap/json'], 'view': 'geomap', 'static': True}}
