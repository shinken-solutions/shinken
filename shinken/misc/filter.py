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

"""
Helper functions for some filtering, like for user based
"""


# Tells whether an host/service should be hidden to the user.
def is_svc_hidden(svc, user):
    if user.hide_ui_problems:
        # This problem should be hidden to the user
        if svc.hide_in_ui_problems:
            return True
        # If problem is a service, and host should be hidden, hide service also
        if hasattr(svc, "host") and svc.host is not None and svc.host.hide_in_ui_problems:
            return True
    return False


# Get only user relevant items for the user
def only_related_to(lst, user):
    # if the user is an admin, show all
    if user.is_admin:
        return [i for i in lst if not is_svc_hidden(i, user)]

    # Ok the user is a simple user, we should filter
    r = set()
    for i in lst:
        # Maybe the user is a direct contact
        if user in i.contacts:
            r.add(i)
            continue
        # TODO: add a notified_contact pass

        # Maybe it's a contact of a linked elements (source problems or impacts)
        is_find = False
        for s in i.source_problems:
            if user in s.contacts:
                r.add(i)
                is_find = True
        # Ok skip this object now
        if is_find:
            continue
        # Now impacts related maybe?
        for imp in i.impacts:
            if user in imp.contacts:
                r.add(i)

    return [i for i in r if not is_svc_hidden(i, user)]
