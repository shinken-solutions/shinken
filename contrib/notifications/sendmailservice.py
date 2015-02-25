#!/usr/bin/env python2
#   Autor: David Hannequin <david.hannequin@gmail.com>
#   Date: 24 Oct 2011

import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEXT_template = """***** Shinken Notification *****

Notification: %(notify)s

Service: %(service)s
Host: %(hostname)s
Address: %(hostaddress)s
State: %(state)s
Date/Time: %(datetime)s
Additional Info: %(output)s
"""

HTML_template = '''<html>
<head></head><body>
<style type="text/css">
.recovery { color:ForestGreen }
.acknowledgement { color:ForestGreen }
.problem { color: red }
.ok { color:ForestGreen }
.critical { color:red }
.warning { color:orange }
.unknown { color:gray }
.bold { font-weight:bold }
</style>
<strong> ***** Shinken Notification ***** </strong><br><br>
Notification: <span class="%(notify)s bold">%(notify)s</span><br><br>
State: <span class="%(state)s bold">%(state)s</span><br><br>
Service: %(service)s <br>
Host: %(hostname)s <br>
Address: %(hostaddress)s <br>
Date/Time: %(datetime)s<br>
Additional Info : %(output)s
</body></html>
'''

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--notification', default='unknown', dest='notify')
parser.add_argument('-s', '--servicedesc', default='unknown', dest='service')
parser.add_argument('-H', '--hostname', default='unknown')
parser.add_argument('-a', '--hostaddress', default='unknown')
parser.add_argument('-r', '--servicestate', default='unknown', dest='state')
parser.add_argument('-i', '--shortdatetime', default='unknown', dest='datetime')
parser.add_argument('-o', '--output', default='')
group = parser.add_argument_group('Mail options')
group.add_argument('-t', '--to')
group.add_argument('-S', '--sender')
group.add_argument('--server', default='localhost')
group.add_argument('--port', default=smtplib.SMTP_PORT, type=int)
args = parser.parse_args()

subject = ("** %(notify)s alert - %(hostname)s/%(service)s is %(state)s **"
           % vars(args))

## Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = args.sender
msg['To'] = args.to

# Create the body of the message (a plain-text and an HTML version).
#
# According to RFC 2046, the last part of a multipart message, in this
# case the HTML message, is best and preferred.
#
# :fixme: need to encode the body if not ascii, see
# http://mg.pov.lt/blog/unicode-emails-in-python.html for a nice
# solution.
#
msg.attach(MIMEText(TEXT_template % vars(args), 'plain'))
# :fixme: need to html-escape all values and encode the body
msg.attach(MIMEText(HTML_template % vars(args), 'html'))

# Send the message via local SMTP server.
s = smtplib.SMTP(args.server, args.port)
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(args.sender, args.to, msg.as_string())
s.quit()
