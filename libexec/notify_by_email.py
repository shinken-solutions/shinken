#!/usr/bin/env python
#-*-coding:utf-8-*-

import os
import sys
import socket
import logging
import getpass
import smtplib
import urllib
from html import HTML
from optparse import OptionParser
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
from email.mime.multipart import MIMEMultipart
from shinken.objects.config import Config

# Global var
shinken_image_dir = '/var/lib/shinken/share/images'
shinken_customer_logo = 'customer_logo.png'
webui_config_file = '/etc/shinken/modules/webui.cfg'


shinken_notification_object_var = { 
    'service': {
        'Service description': os.getenv('NAGIOS_SERVICEDESC'),
        'Service state': os.getenv('NAGIOS_SERVICESTATE'),
        'Service output': os.getenv('NAGIOS_SERVICEOUTPUT'),
        'Service duration': os.getenv('NAGIOS_SERVICEDURATION') 
    },
    'host': {
        'Host alias': os.getenv('NAGIOS_HOSTALIAS'),
        'Host state': os.getenv('NAGIOS_HOSTSTATE'), 
        'Host duration': os.getenv('NAGIOS_HOSTDURATION') 
    }
}

shinken_var = {
    'Notification type': os.getenv('NAGIOS_NOTIFICATIONTYPE'),
    'Hostname': os.getenv('NAGIOS_HOSTNAME'),
    'Host address': os.getenv('NAGIOS_HOSTADDRESS'),
    'Date' : os.getenv('NAGIOS_LONGDATETIME'),
    'Contact email': os.getenv('NAGIOS_CONTACTEMAIL') 
}

# Set up root logging
def setup_logging():
    log_level = logging.INFO
    if opts.debug:
        log_level = logging.DEBUG
    if opts.logfile:
        logging.basicConfig(filename=opts.logfile, level=log_level, format='%(asctime)s:%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=log_level, format='%(asctime)s:%(levelname)s: %(message)s')

def overload_test_variable():
    shinken_notification_object_var = {
        'service': {
            'Service description': 'CPU load',
            'Service state': 'PROBLEM',
            'Service output': 'Houston, we got a problem here! Oh, wait. No. It\'s just a test.',
            'Service duration': '00h 00min 10s'
        },
        'host': {
            'Host alias': 'Shinken monitoring solution: Test host',
            'Host state': 'TEST PROBLEM',
            'Host duration': '00h 00h 20s'
        }
    }

    shinken_var = {
        'Hostname': 'shinken.domain.tld',
        'Host address': '127.0.0.1',
        'Notification type': 'TEST',
        'Date': 'Now, test',
        'Contact email': '@'.join((getpass.getuser(), socket.gethostname())) 
    }
    return (shinken_notification_object_var, shinken_var)

def read_webui_cfg():
    config = Config()
    webui_config_raw = config.read_config([webui_config_file])
    webui_config = config.read_config_buf(webui_config_raw)
    
    return webui_config['module'][0]

def get_shinken_url():
    hostname = socket.gethostname()
    webui_config = read_webui_cfg()
    url = 'http://%s:%s/%s/%s' % (hostname, webui_config['port'][0], opts.notification_object, urllib.quote(shinken_var['Hostname']))

    # Append service if we notify a service object
    if opts.notification_object == 'service':
        url += '/%s' % (urllib.quote(shinken_notification_object_var['service']['Service description']))

    return url

# Get current process user that will be the mail sender
def get_user():
    return '@'.join((getpass.getuser(), socket.gethostname()))
    

#############################################################################
# Common mail functions and var
#############################################################################
mail_welcome = 'Shinken Monitoring System Notification'
mail_format = { 'html': MIMEMultipart(), 'txt': MIMEMultipart('alternative') }

# Construct mail subject field based on which object we notify
def get_mail_subject(object):
    mail_subject = { 'host': 'Host %s alert for %s since %s' % (shinken_notification_object_var['host']['Host state'], shinken_var['Hostname'], shinken_notification_object_var['host']['Host duration']), 'service': '%s on Host: %s about service %s since %s' % (shinken_notification_object_var['service']['Service state'], shinken_notification_object_var['host']['Host alias'], shinken_notification_object_var['service']['Service description'], shinken_notification_object_var['service']['Service duration'])}

    return mail_subject[object]

# This just create mail skeleton and doesn't have any content.
# But can be used to add multiple and differents contents.
def create_mail(format):
    # Fill SMTP header and body.
    # It has to be multipart since we can include an image in it.
    logging.debug('Mail format: %s' % (mail_format[format]))
    msg = mail_format[format]
    logging.debug('From: %s' % (get_user()))
    msg['From'] = get_user()
    logging.debug('To: %s' % (opts.receivers))
    msg['To'] = opts.receivers
    logging.debug('Subject: %s' % (get_mail_subject(opts.notification_object)))
    msg['Subject'] = get_mail_subject(opts.notification_object)
    
    return msg

def get_content_to_send():
    shinken_var.update(shinken_notification_object_var[opts.notification_object])

#############################################################################
# Txt creation lair
#############################################################################
def create_txt_message(msg):
    txt_content = [mail_welcome]

    get_content_to_send()
    for k,v in sorted(shinken_var.iteritems()):
        txt_content.append(k + ': ' + v)

    txt_content = '\r\n'.join(txt_content)
    
    # Add url at the end
    url = get_shinken_url()
    txt_content = 'More details on Shinken WebUI at : %s' % (url)

    msgText = MIMEText(txt_content, 'text')
    msg.attach(msgText)

    return msg
    
#############################################################################
# Html creation lair
#############################################################################

# Process customer logo into mail message so it can be referenced in it later
def add_image2mail(img, mail):
    fp = open(img, 'rb')
    msgLogo = MIMEImage(fp.read())
    fp.close()
    msgLogo.add_header('Content-ID', '<customer_logo>')
    mail.attach(msgLogo)

    return mail

def create_html_message(msg):
    # Get url and add it in footer
    url = get_shinken_url()
    logging.debug('Grabbed Shinken URL : %s' % url)

    # Header part
    html_content = ['''<html><head>\r
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><style type="text/css">body {text-align: center; font-family: Verdana, sans-serif; font-size: 10pt;}\r
img.logo {float: left; margin: 10px 10px 10px; vertical-align: middle}\r
span {font-family: Verdana, sans-serif; font-size: 12pt;}\r
table {text-align:center; margin-left: auto; margin-right: auto;}\r
th {white-space: nowrap;}\r
th.even {background-color: #D9D9D9;}\r
td.even {background-color: #F2F2F2;}\r
th.odd {background-color: #F2F2F2;}\r
td.odd {background-color: #FFFFFF;}\r
th,td {font-family: Verdana, sans-serif; font-size: 10pt; text-align:left;}\r
th.customer {width: 600px; background-color: #004488; color: #ffffff;}</style></head><body>\r''']
    
    full_logo_path = os.path.join(shinken_image_dir, shinken_customer_logo)
    if os.path.isfile(full_logo_path):
        msg = add_image2mail(full_logo_path, msg)
        html_content.append('<img src="cid:customer_logo">')
        html_content.append('<table width="600px"><tr><th colspan="2"><span>%s</span></th></tr>' % mail_welcome)
    else:
        html_content.append('<table width="600px"><tr><th colspan="2"><span>%s</span></th></tr>' %  mail_welcome)

    # Update shinken_var dict with appropriate dict depending which is object notified
    # then we can fill mail content.
    odd=True
    get_content_to_send()
    logging.debug('Content to send: %s' % shinken_var)
    for k,v in sorted(shinken_var.iteritems()):
        logging.debug('type %s : %s' % (k, type(v)))
        if odd:
            html_content.append('<tr><th class="odd">' + k + '</th><td class="odd">' + v + '</td></tr>')
            odd=False
        else:
            html_content.append('<tr><th class="even">' + k + '</th><td class="even">' + v + '</td></tr>')
            odd=True

    html_content.append('</table>')
    html_content.append('More details on Shinken WebUI at : <a href="%s">%s</a></body></html>' % (url, url))

    # Make final string var to send and encode it to stdout encoding
    # avoiding decoding error.
    html_content = '\r\n'.join(html_content)
    html_msg = html_content.encode(sys.stdout.encoding)

    logging.debug('HTML string: %s' % html_msg)
    
    msgText = MIMEText(html_msg, 'html')
    logging.debug('MIMEText: %s' % msgText)
    msg.attach(msgText)
    logging.debug('Mail object: %s' % msg)

    return msg

if __name__ == "__main__":
    parser = OptionParser(description='Notify by email receivers of Shinken alerts. Message will be formatted in html and can embed customer logo. To included customer logo, just load png image named customer_logo.png in '+shinken_image_dir)
    
    parser.add_option('-D', '--debug', dest='debug', default=False,
                      action='store_true', help='Generate a test mail message')
    parser.add_option('-t', '--test', dest='test',
                      action='store_true', help='Generate a test mail message')
    parser.add_option('-f', '--format', dest='format', type='choice', choices=['txt', 'html'], 
                      default='html', help='Mail format "html" or "txt". Default: html')
    parser.add_option('-l', '--logfile', dest='logfile',
                      help='Specify a log file. Default: log to stdout.')
    parser.add_option('-d', '--detailleddesc', dest='detailleddesc',
                      help='Specify $_SERVICEDETAILLEDDESC$ custom macros')
    parser.add_option('-i', '--impact', dest='impact',
                      help='Specify the $_SERVICEIMPACT$ custom macros')
    parser.add_option('-a', '--action', dest='fixaction',
                      help='Specify the $_SERVICEFIXACTIONS$ custom macros')
    parser.add_option('-r', '--receivers', dest='receivers', default=shinken_var['Contact email'],
                      help='Mail recipients comma-separated list')
    parser.add_option('-n', '--notification-object', dest='notification_object', type='choice', default='host',
                      choices=['host', 'service'], help='Notify a service Shinken alert. Else it is an host alert.')
    parser.add_option('-S', '--SMTP', dest='smtp', default='localhost',
                      help='Target SMTP hostname. Default: localhost')
    
    (opts, args) = parser.parse_args()
    
    setup_logging()
    
    # Check and process arguments
    # Load test values
    if opts.test:
        shinken_notification_object_var, shinken_var = overload_test_variable()
        opts.receivers = ','.join((opts.receivers, shinken_var['Contact email']))
    
    if opts.detailleddesc:
        shinken_var['Detailled description'] = opts.detailleddesc.decode(sys.stdin.encoding)
    if opts.impact:
        shinken_var['Impact'] = opts.impact.decode(sys.stdin.encoding)
    if opts.fixaction:
        shinken_var['Fix actions'] = opts.fixaction.decode(sys.stdin.encoding)
    
    logging.debug('Create mail skeleton')
    mail = create_mail(opts.format)
    logging.debug('Create %s mail content' % (opts.format))
    if opts.format == 'html':
        mail = create_html_message(mail)
    elif opts.format == 'txt':
        mail = create_txt_message(mail)

    logging.debug('Connect to %s smtp server' % (opts.smtp))
    smtp = smtplib.SMTP(opts.smtp)
    logging.debug('Send the mail')
    smtp.sendmail(get_user(), opts.receivers.split(','), mail.as_string())
    logging.info("Mail sent successfuly")
