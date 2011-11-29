#!/usr/bin/env python
#   Autor : David Hannequin <david.hannequin@gmail.com>
#   Date : 24 Oct 2011

import sys
import os
import getopt 
import argparse
import smtplib

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hnsHariotS:v", ["help", "notification", "servicedesc", "hostname", "hostaddress", "servicestate", "shortdatetime", "output", "to", "sender" ])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) 
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-n", "--notification"):
            notification = a
        elif o in ("-s", "--servicedesc"):
            servicedesc = a
        elif o in ("-H", "--hostname"):
            hostname = a
        elif o in ("-a", "--hostaddress"):
            hostaddress = a
        elif o in ("-r", "--servicestate"):
            servicestate = a
        elif o in ("-i", "--shortdatetime"):
            shortdatetime = a
        elif o in ("-o", "--output"):
            serviceoutput = a
        elif o in ("-t", "--to"):
            to = a
        elif o in ("-S", "--sender"):
            to = a
        else:
            assert False, "unhandled option"

def usage():
    print 'Usage :'
    print sys.argv[0] + ' -s <service name> -n <notification type> -H <hostname> -a <address> -i <date> -o <service output> -t <email>'
    print '-s --servicedesc : service description' 
    print '-n --notification : notification type' 
    print '-H --hostname : hostname'
    print '-a --hostaddress : host address'
    print '-r --servicestate : service state'
    print '-i --shortdatetime : date'
    print '-o --output : service output'
    print '-t --to : email send to'
    print '-S --sender : email from'

if __name__ == "__main__":
    main()

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--notification')
    parser.add_argument('-s', '--servicedesc')
    parser.add_argument('-H', '--hostname')
    parser.add_argument('-a', '--hostaddress')
    parser.add_argument('-r', '--servicestate')
    parser.add_argument('-i', '--shortdatetime')
    parser.add_argument('-o', '--output')
    parser.add_argument('-t', '--to')
    parser.add_argument('-S', '--sender')
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
html = "<html><head></head><body><strong> ***** Shinken Notification ***** </strong><br><br>\r Notification : "+ notify +"<br><br>\rService : "+ desc +" <br>\r Host : "+ hostname +" <br>\r Address : "+ hostaddress +" <br>\r State : "+ state +"<br><br>\r Date/Time : "+ datetime +" Additional Info : "+ output + "</body></html>"

# Record the MIME types of one parts - text/html.
part1 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)

# Send the message via local SMTP server.
s = smtplib.SMTP('localhost')
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(sender, to, msg.as_string())
s.quit()
