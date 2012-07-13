#!/usr/bin/env python
#   Autor: David Hannequin <david.hannequin@gmail.com>
#   Date: 24 Oct 2011

import sys
import os
import getopt
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

HTML_template = """<html>
<head></head><body>
<strong> ***** Shinken Notification ***** </strong><br><br>
Notification: %(notify)s<br><br>
Service: %(service)s <br>
Host: %(hostname)s <br>
Address: %(hostaddress)s <br>
State: %(state)s <br><br>
Date/Time: %(datetime)s<br>
Additional Info : %(output)s
</body></html>
"""

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
msg.attach(MIMEText(TEXT_template % vars(args), 'plain'))
msg.attach(MIMEText(HTML_template % vars(args), 'html'))

# Send the message via local SMTP server.
s = smtplib.SMTP(args.server, args.port)
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(args.sender, args.to, msg.as_string())
s.quit()
