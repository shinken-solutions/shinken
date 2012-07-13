#!/usr/bin/env python
#   Autor: David Hannequin <david.hannequin@gmail.com>
#   Date: 24 Oct 2011

import sys
import os
import getopt
import argparse
import smtplib

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notification')
    parser.add_argument('-s', '--servicedesc')
    parser.add_argument('-H', '--hostname')
    parser.add_argument('-a', '--hostaddress')
    parser.add_argument('-r', '--servicestate')
    parser.add_argument('-i', '--shortdatetime')
    parser.add_argument('-o', '--output')
    group = parser.add_argument_group('Mail options')
    group.add_argument('-t', '--to')
    group.add_argument('-S', '--sender')
    group.add_argument('--server', default='localhost')
    group.add_argument('--port', default=smtplib.SMTP_PORT, type=int)
    args = parser.parse_args()

    notify = args.notification
    desc = args.servicedesc
    hostname = args.hostname
    hostaddress = args.hostaddress
    state = args.servicestate
    datetime = args.shortdatetime
    output = args.output
    to = args.to
    sender = args.sender

    subject = "** " + notify + " alert - " + hostname + "/" + desc + " is " + state + " **"

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

## Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = sender
msg['To'] = to

# Create the body of the message (a plain-text and an HTML version).
html = "<html><head></head><body><strong> ***** Shinken Notification ***** </strong><br><br>\r Notification : " + notify + "<br><br>\rService : " + desc + " <br>\r Host : " + hostname + " <br>\r Address : " + hostaddress + " <br>\r State : " + state + "<br><br>\r Date/Time : " + datetime + " Additional Info : " + output + "</body></html>"

# Record the MIME types of one parts - text/html.
part1 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)

# Send the message via local SMTP server.
s = smtplib.SMTP(args.server, args.port)
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(sender, to, msg.as_string())
s.quit()
