#!/usr/bin/env python
# -*- coding: utf-8 -*-

# /usr/local/shinken/libexec/link_xen_host_vm.py
# This file is proposed for Shinken to link vm and xenserver.
# Devers Renaud rdevers@chavers.org
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


import sys
import XenAPI
from string import split
import shutil
import optparse

# Try to load json (2.5 and higer) or simplejson if failed (python2.4)
try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        sys.exit("Error: you need the json or simplejson module for this script")

VERSION = '0.1'

# Split and clean the rules from a string to a list
def _split_rules(rules):
    return [r.strip() for r in rules.split('|')]


# Apply all rules on the objects names
def _apply_rules(name, rules):
    if 'nofqdn' in rules:
        name = name.split(' ', 1)[0]
        name = name.split('.', 1)[0]
    if 'lower' in rules:
        name = name.lower()
    return name


def create_all_links(res,rules):
    r = []
    for host in res:
        for vm in res[host]:
            # First we apply rules on the names
            host_name = _apply_rules(host,rules)
            vm_name = _apply_rules(vm,rules)
            v = (('host', host_name), ('host', vm_name))
            r.append(v)
    return r

def write_output(path,r):
    try:
        f = open(path + '.tmp', 'wb')
        buf = json.dumps(r)
        f.write(buf)
        f.close()
        shutil.move(path + '.tmp', path)
        print "File %s wrote" % path
    except IOError, exp:
        sys.exit("Error writing the file %s: %s" % (path, exp))

def con_poolmaster(xs, user, password):
  try:
    s = XenAPI.Session("http://%s" % xs)
    s.xenapi.login_with_password(user,password)
    return s
  except XenAPI.Failure, msg:
     if  msg.details[0] == "HOST_IS_SLAVE":
        host = msg.details[1]
        s = XenAPI.Session("http://%s" % host)
        s.xenapi.login_with_password(user, password)
        return s
     else:
        print "Error: pool con:",  xs, sys.exc_info()[0]
        pass
  except Exception:
    print "Error: pool con:",  xs, sys.exc_info()[0]
    pass
  return None

def main(output, user, password, rules, xenserver):
  res = {}
  for xs in xenserver:
    try:
      s = con_poolmaster(xs, user, password)
      vms = s.xenapi.VM.get_all()
      for vm in vms:
        record = s.xenapi.VM.get_record(vm)
        if not(record["is_a_template"]) and not(record["is_control_domain"]):
          vhost = s.xenapi.VM.get_resident_on(vm)
          if vhost != "OpaqueRef:NULL":
            host = s.xenapi.host.get_hostname(vhost)
            vm_name = s.xenapi.VM.get_name_label(vm)
            if host in res.keys():
              res[host].append(vm_name)
            else:
              res[host] = [vm_name]
      s.xenapi.session.logout()
    except Exception:
      pass
  r = create_all_links(res,rules)
  print "Created %d links" % len(r)

  write_output(output, r)
  print "Finished!"

if __name__ == "__main__":
    # Manage the options
    parser = optparse.OptionParser(
        version="Shinken XenServer/XCP links dumping script version %s" % VERSION)
    parser.add_option("-o", "--output",
                      default='/tmp/xen_mapping_file.json',
                      help="Path of the generated mapping file.")
    parser.add_option("-u", "--user",
                      help="User name to connect to this Vcenter")
    parser.add_option("-p", "--password",
                      help="The password of this user")
    parser.add_option('-r', '--rules', default='',
                      help="Rules of name transformation. Valid names are: "
                      "`lower`: to lower names, "
                      "`nofqdn`: keep only the first name (server.mydomain.com -> server)."
                      "You can use several rules like `lower|nofqdn`")
    parser.add_option('-x','--xenserver',action="append",
                      help="multiple ip/fqdn of your XenServer/XCP poll master (or member). "
                      "ex: -x poolmaster1 -x poolmaster2 -x poolmaster3 "
                      "If pool member was use, the poll master was found")

    opts, args = parser.parse_args()
    if args:
        parser.error("does not take any positional arguments")

    if opts.user is None:
        parser.error("missing -u or --user option for the pool master username")
    if opts.password is None:
        error = True
        parser.error("missing -p or --password option for the pool master password")
    if opts.output is None:
        parser.error("missing -o or --output option for the output mapping file")
    if opts.xenserver is None:
        parser.error("missing -x or --xenserver option for pool master list")

    main(**opts.__dict__)
