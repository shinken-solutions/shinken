#!/usr/bin/env python2.7

import os
import sys
from optparse import OptionParser
import requests
import urllib

def post_slack(token, ch, msg, bot, slackuser):
  url = 'https://slack.com/api/chat.postMessage?token=' + token + '&channel=' + urllib.quote(ch) + '&text=' + urllib.quote(msg) + '&username=+' + bot + '&as_user=' + slackuser + '&pretty=1'
  res = requests.get(url)
  #print url

def create_text(dict):
  if opts.weblink and opts.notification_object == "service":
    msg = "%s, %s, %s, <http://%s/service/%s/%s|%s>" %(dict['duration'], dict['state'], dict['hostname'], opts.weblink, dict['hostname'], dict['servicename'], dict['servicename'])
  elif opts.weblink:
    msg = "%s, %s, <http://%s/host/%s|%s>" %(dict['duration'], dict['state'], opts.weblink, dict['hostname'], dict['hostname'])
  elif opts.notification_object == "service":
    msg = "%s, %s, %s, %s" %(dict['duration'], dict['state'], dict['hostname'], dict['servicename'])
  else:
    msg = "%s, %s, %s" %(dict['duration'], dict['state'], dict['hostname'])
  return msg

if __name__ == "__main__":
  parser = OptionParser(description='Scrpit to send the alerts to a slack channel to help monitor services via slack than email')
  parser.add_option('-n', '--notification-object', dest='notification_object', type='choice', default='host',
                    choices=['host', 'service'], help='Choose between host or service notification.')
  parser.add_option('-c', '--commonmacro', dest='commonmacros',
                    help='Hostname which is effected       \
                    -c "$HOSTNAME$"')
  parser.add_option('-o', '--objectmacro', dest='objectmacros',
                    help='Object info for alerting, e.g.\
                    "$HOSTSTATE$,,$HOSTDURATION"\
                    "$SERVICEDESC$,,$SERVICESTATE$,,$SERVICEDURATION$"')
  parser.add_option('-w', '--weblink', dest='weblink',
                    help='Link to create weblink for the Objects\
                    <shinken-webui-hostname>:<port>')
  parser.add_option('--token', dest='token',
                    help='Auth token for Slack')
  parser.add_option('--bot', dest='bot',
                    help='Bot to call slack as')
  parser.add_option('--su', '--slackuser', dest='slackuser',
                    help='User for slack whom token belongs to')
  parser.add_option('--ch', '--channel', dest='ch',
                    help='Slack channel to post to        \
                    --ch "#test-channel"')

  (opts, args) = parser.parse_args()


  if opts.commonmacros == None:
    shinken_var = {
      'Hostname': os.getenv('NAGIOS_HOSTNAME')
    }
  else:
    shinken_var = {
      'Hostname': opts.commonmacros
    }

  if opts.objectmacros == None:
    shinken_var.update({
      'Service description': os.getenv('NAGIOS_SERVICEDESC'),
      'Service state': os.getenv('NAGIOS_SERVICESTATE'),
      'Service duration': os.getenv('NAGIOS_SERVICEDURATION'),
      'Host state': os.getenv('NAGIOS_HOSTSTATE'),
      'Host duration': os.getenv('NAGIOS_HOSTDURATION')
    })
  else:
    macros = opts.objectmacros.split(',,')
    if opts.notification_object == 'service':
      shinken_var.update({
        'Service description': macros[0],
        'Service state': macros[1],
        'Service duration': macros[2]
      })
    else:
      shinken_var.update({
        'Host state': macros[0],
        'Host duration': macros[1]
      })

  if opts.notification_object == 'service':
    dict = {'duration': shinken_var['Service duration'], 'state': shinken_var['Service state'], 'servicename': shinken_var['Service description'], 'hostname': shinken_var['Hostname']}
  else:
    dict = {'duration': shinken_var['Host duration'], 'state': shinken_var['Host state'], 'hostname': shinken_var['Hostname']}
    
  msg = create_text(dict)
  post_slack(opts.token, opts.ch, msg, opts.bot, opts.slackuser)
