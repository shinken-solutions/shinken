#!/usr/bin/env python
#-*-coding:utf-8-*-
# Copyright (C) 2012:
#    Romain Forlot, rforlot@yahoo.com
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
import sys
import socket
import logging
import getpass
import smtplib
import urllib
from optparse import OptionParser, OptionGroup
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
from email.mime.multipart import MIMEMultipart

# Global var
shinken_image_dir = '/var/lib/shinken/share/images'
shinken_customer_logo = 'customer_logo.jpg'
webui_config_file = '/etc/shinken/modules/webui.cfg'

webui2_config_file = '/etc/shinken/modules/webui2.cfg'
webui2_image_dir = '/var/lib/shinken/share/photos'

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
            'Service description': 'Test_Service',
            'Service state': 'TEST',
            'Service output': 'Houston, we got a problem here! Oh, wait. No. It\'s just a test.',
            'Service state duration': '00h 00min 10s'
        },
        'host': {
            'Hostname': 'Test_Host',
            'Host state': 'TEST',
            'Host state duration': '00h 00h 20s'
        }
    }

    shinken_var = {
        'Hostname': 'shinken',
        'Host address': '127.0.0.1',
        'Notification type': 'TEST',
        'Date': 'Now, test'
    }
    return (shinken_notification_object_var, shinken_var)

def get_webui_logo():
    company_logo=''

    try:
        webui_config_fh = open(webui2_config_file)
    except IOError:
        # WebUI2 not installed ...
        full_logo_path = os.path.join(shinken_image_dir, shinken_customer_logo)
        if os.path.isfile(full_logo_path):
            return full_logo_path

    if opts.webui:
        # WebUI2 installed
        logging.debug('Webui2 is installed')
        webui_config = webui_config_fh.readlines()
        for line in webui_config:
            if 'company_logo' in line:
                company_logo = line.rsplit('company_logo')[1].strip()
                company_logo += '.png'
        logging.debug('Found company logo property: %s', company_logo)
        if company_logo:
            full_logo_path = os.path.join(webui2_image_dir, company_logo)
            if os.path.isfile(full_logo_path):
                logging.debug('Found company logo file: %s', full_logo_path)
                return full_logo_path
            else:
                logging.debug('File %s does not exist!', full_logo_path)
                return ''

    return company_logo

def get_webui_port():
    port=''

    try:
        webui_config_fh = open(webui2_config_file)
    except IOError:
        # WebUI2 not installed, try WebUI1
        try:
            webui_config_fh = open(webui_config_file)
        except IOError:
            # No WebUI
            return ''
        else:
            # WebUI1 installed
            logging.debug('Webui1 is installed')
    else:
        # WebUI2 installed
        logging.debug('Webui2 is installed')

    logging.debug('Webui file handler: %s' % (webui_config_fh))
    webui_config = webui_config_fh.readlines()
    logging.debug('Webui config: %s' % (webui_config))
    for line in webui_config:
        if 'port' in line:
            port = line.rsplit('port')[1].strip()
    return port

def get_shinken_url():
    if opts.webui:
        hostname = socket.getfqdn()
        webui_port = get_webui_port()
        if not webui_port:
            return

        if opts.webui_url:
            url = '%s/%s/%s' % (opts.webui_url, opts.notification_object, urllib.quote(shinken_var['Hostname']))
        else:
            url = 'http://%s:%s/%s/%s' % (hostname, webui_port, opts.notification_object, urllib.quote(shinken_var['Hostname']))

        # Append service if we notify a service object
        if opts.notification_object == 'service':
            url += '/%s' % (urllib.quote(shinken_notification_object_var['service']['Service description']))

        return url

# Get current process user that will be the mail sender
def get_user():
    if opts.sender:
        return opts.sender
    else:
        return '@'.join((getpass.getuser(), socket.getfqdn()))


#############################################################################
# Common mail functions and var
#############################################################################
mail_welcome = 'Shinken Monitoring System Notification'
mail_format = { 'html': MIMEMultipart(), 'txt': MIMEMultipart('alternative') }

# Construct mail subject field based on which object we notify
def get_mail_subject(object):
    mail_subject = {
        'host': 'Host %s alert for %s since %s' % (
            shinken_notification_object_var['host']['Host state'],
            shinken_var['Hostname'],
            shinken_notification_object_var['host']['Host state duration']
        ),
        'service': '%s on Host: %s about service %s since %s' % (
            shinken_notification_object_var['service']['Service state'],
            shinken_var['Hostname'],
            shinken_notification_object_var['service']['Service description'],
            shinken_notification_object_var['service']['Service state duration']
        )
    }

    return mail_subject[object]

def get_content_to_send():
    shinken_var.update(shinken_notification_object_var[opts.notification_object])

# Translate a comma separated list of mail recipient into a python list
def make_receivers_list(receivers):
    if ',' in receivers:
        ret = receivers.split(',')
    else:
        ret = [receivers]

    return ret

# This just create mail skeleton and doesn't have any content.
# But can be used to add multiple and differents contents.
def create_mail(format):
    # Fill SMTP header and body.
    # It has to be multipart since we can include an image in it.
    logging.debug('Mail format: %s' % (format))
    msg = mail_format[format]
    logging.debug('From: %s' % (get_user()))
    msg['From'] = get_user()
    logging.debug('To: %s' % (opts.receivers))
    msg['To'] = opts.receivers
    logging.debug('Subject: %s' % (opts.prefix + get_mail_subject(opts.notification_object)))
    msg['Subject'] = opts.prefix + get_mail_subject(opts.notification_object)

    return msg

#############################################################################
# Txt creation lair
#############################################################################
def create_txt_message(msg):
    txt_content = [mail_welcome]

    get_content_to_send()
    for k,v in sorted(shinken_var.iteritems()):
        txt_content.append(k + ': ' + v)


    # Add url at the end
    url = get_shinken_url()
    if url != None:
        txt_content.append('More details on : %s' % url)

    txt_content = '\r\n'.join(txt_content)

    msgText = MIMEText(txt_content, 'text')
    msg.attach(msgText)

    return msg

#############################################################################
# Html creation lair
#############################################################################

# Process customer logo into mail message so it can be referenced in it later
def add_image2mail(img, mail):
    fp = open(img, 'rb')
    try:
        msgLogo = MIMEImage(fp.read())
        msgLogo.add_header('Content-ID', '<customer_logo>')
        mail.attach(msgLogo)
    except:
        pass

    fp.close()
    return mail

def create_html_message(msg):
    # Get url and add it in footer
    url = get_shinken_url()
    logging.debug('Grabbed Shinken URL : %s' % url)

    # Header part
    html_content = ['''
<html>\r
<head>\r
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\r
<style type="text/css">\r
body {text-align: center; font-family: Verdana, sans-serif; font-size: 10pt;}\r
img.logo {float: left; margin: 10px 10px 10px; vertical-align: middle}\r
span {font-family: Verdana, sans-serif; font-size: 12pt;}\r
table {text-align:center; margin-left: auto; margin-right: auto;}\r
th {white-space: nowrap;}\r
th.even {background-color: #D9D9D9;}\r
td.even {background-color: #F2F2F2;}\r
th.odd {background-color: #F2F2F2;}\r
td.odd {background-color: #FFFFFF;}\r
th,td {font-family: Verdana, sans-serif; font-size: 10pt; text-align:left;}\r
th.customer {width: 600px; background-color: #004488; color: #ffffff;}\r
</style>\r
</head>\r
<body>\r'''
    ]

    full_logo_path = get_webui_logo()
    if full_logo_path:
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
    if url != None:
        html_content.append('More details on Shinken WebUI at : <a href="%s">%s</a></body></html>' % (url, url))
    else:
        html_content.append('</body></html>')

    # Make final string var to send and encode it to stdout encoding
    # avoiding decoding error.
    html_content = '\r\n'.join(html_content)
    try:
        if sys.stdout.encoding is not None:
            encoding = sys.stdout.encoding
        else:
            encoding = 'utf-8'
        html_msg = html_content.encode(encoding)
    except UnicodeDecodeError:
        logging.debug('Content is Unicode encoded.')
        html_msg = html_content.decode('utf-8').encode(encoding)


    logging.debug('HTML string: %s' % html_msg)

    msgText = MIMEText(html_msg, 'html')
    logging.debug('MIMEText: %s' % msgText)
    msg.attach(msgText)
    logging.debug('Mail object: %s' % msg)

    return msg

if __name__ == "__main__":
    parser = OptionParser(description='Notify by email receivers of Shinken alerts. Message will be formatted in html and can embed customer logo. To included customer logo, just load png image named customer_logo.png in '+shinken_image_dir)

    group_debug = OptionGroup(parser, 'Debugging and test options', 'Useful to debug script under shinken processes. Useful to just make a standalone test of script to see what it looks like.')
    group_general = OptionGroup(parser, 'General options', 'Default options to setup')
    group_shinken = OptionGroup(parser, 'Shinken macros to specify.', 'Used to specify usual shinken macros in notifications, if not specified then it will try to get them from environment variable. You need to enable_environment_macros in shinken.cfg if you want to used them. It isn\'t recommended to use environment macros for large environments. You \'d better use options -c and -s or -h depending on which object you\'ll notify for.')
    group_shinken_details = OptionGroup(parser, 'Details and additional information', 'You can include some useful additional information to notifications using these options. Good practice is to add HOST or SERVICE macros with these details and provide them to the script')
    group_shinken_webui = OptionGroup(parser, 'Shinken WebUI.', 'Used to include some Shinken WebUI information in the notifications.')

    # Debug and test options
    group_debug.add_option('-D', '--debug', dest='debug', default=False,
                      action='store_true', help='Generate a test mail message')
    group_debug.add_option('-t', '--test', dest='test', default=False,
                      action='store_true', help='Generate a test mail message')
    group_debug.add_option('-l', '--logfile', dest='logfile',
                      help='Specify a log file. Default: log to stdout.')

    # General options
    group_general.add_option('-f', '--format', dest='format', type='choice', choices=['txt', 'html'],
                      default='html', help='Mail format "html" or "txt". Default: html')
    group_general.add_option('-r', '--receivers', dest='receivers',
                      help='Mail recipients comma-separated list')
    group_general.add_option('-F', '--sender', dest='sender',
                      help='Sender email address, default is system user')
    group_general.add_option('-S', '--SMTP', dest='smtp', default='localhost',
                      help='Target SMTP hostname. None for just a sendmail lanch. Default: localhost')
    group_general.add_option('-p', '--prefix', dest='prefix', default='',
                      help='Mail subject prefix. Default is no prefix')

    # Shinken options
    group_shinken.add_option('-n', '--notification-object', dest='notification_object', type='choice', default='host',
                      choices=['host', 'service'], help='Choose between host or service notification.')
    group_shinken.add_option('-c', '--commonmacros', dest='commonmacros',
                      help='Double comma separated shinken macros in this order : "NOTIFICATIONTYPE$,,$HOSTNAME$,,$HOSTADDRESS$,,$LONGDATETIME$".')
    group_shinken.add_option('-o', '--objectmacros', dest='objectmacros',
                      help='Double comma separated object shinken macros in this order : "$SERVICEDESC$,,$SERVICESTATE$,,$SERVICEOUTPUT$,,$SERVICEDURATION$" for a service object and "$HOSTSTATE$,,$HOSTDURATION$" for an host object')
    group_shinken_details.add_option('-d', '--detailleddesc', dest='detailleddesc',
                      help='Specify $_SERVICEDETAILLEDDESC$ custom macros')
    group_shinken_details.add_option('-i', '--impact', dest='impact',
                      help='Specify the $_SERVICEIMPACT$ custom macros')
    group_shinken_details.add_option('-a', '--action', dest='fixaction',
                      help='Specify the $_SERVICEFIXACTIONS$ custom macros')

    # Shinken WebUI options
    group_shinken_webui.add_option('-w', '--webui', dest='webui', default=False,
                      action='store_true', help='Include link to the problem in Shinken WebUI.')
    group_shinken_webui.add_option('-u', '--url', dest='webui_url',
                      help='WebUI URL as http://my_webui:port/url')

    parser.add_option_group(group_debug)
    parser.add_option_group(group_general)
    parser.add_option_group(group_shinken)
    parser.add_option_group(group_shinken_details)
    parser.add_option_group(group_shinken_webui)

    (opts, args) = parser.parse_args()

    setup_logging()

    # Check and process arguments
    #
    # Retrieve and setup shinken macros that make the mail content
    if opts.commonmacros == None:
        shinken_var = {
            'Notification type': os.getenv('NAGIOS_NOTIFICATIONTYPE'),
            'Hostname': os.getenv('NAGIOS_HOSTNAME'),
            'Host address': os.getenv('NAGIOS_HOSTADDRESS'),
            'Date' : os.getenv('NAGIOS_LONGDATETIME')
        }
    else:
        macros = opts.commonmacros.split(',,')
        shinken_var = {
            'Notification type': macros[0],
            'Hostname': macros[1],
            'Host address': macros[2],
            'Date' : macros[3]
        }

    if opts.objectmacros == None:
        shinken_notification_object_var = {
            'service': {
                'Service description': os.getenv('NAGIOS_SERVICEDESC'),
                'Service state': os.getenv('NAGIOS_SERVICESTATE'),
                'Service output': os.getenv('NAGIOS_SERVICEOUTPUT'),
                'Service state duration': os.getenv('NAGIOS_SERVICEDURATION')
            },
            'host': {
                'Host state': os.getenv('NAGIOS_HOSTSTATE'),
                'Host state duration': os.getenv('NAGIOS_HOSTDURATION')
            }
        }
    else:
        macros = opts.objectmacros.split(',,')
        if opts.notification_object == 'service':
            shinken_notification_object_var = {
                'service': {
                    'Service description': macros[0],
                    'Service state': macros[1],
                    'Service output': macros[2],
                    'Service state duration': macros[3]
                },
                'host': {
                    'Host state': '',
                    'Host state duration': ''
            }

            }
        else:
            shinken_notification_object_var = {
                 'service': {
                    'Service description': '',
                    'Service state': '',
                    'Service output': '',
                    'Service state duration': ''
                },'host': {
                    'Host state': macros[0],
                    'Host state duration': macros[1]
                }
            }

    # Load test values
    if opts.test:
        shinken_notification_object_var, shinken_var = overload_test_variable()

    # check required arguments
    if opts.receivers == None:
        logging.error('You must define at least one mail recipient using -r')
        sys.exit(5)
    else:
        contactemail = opts.receivers



    if opts.detailleddesc:
        shinken_var['Detailled description'] = opts.detailleddesc.decode(sys.stdin.encoding)
    if opts.impact:
        shinken_var['Impact'] = opts.impact.decode(sys.stdin.encoding)
    if opts.fixaction:
        shinken_var['Fix actions'] = opts.fixaction.decode(sys.stdin.encoding)

    receivers = make_receivers_list(opts.receivers)

    logging.debug('Create mail skeleton')
    mail = create_mail(opts.format)
    logging.debug('Create %s mail content' % (opts.format))
    if opts.format == 'html':
        mail = create_html_message(mail)
    elif opts.format == 'txt':
        mail = create_txt_message(mail)

    # Use SMTP or sendmail to send the mail ...
    if opts.smtp != 'None':
        logging.debug('Connect to %s smtp server' % (opts.smtp))
        smtp = smtplib.SMTP(opts.smtp)
        logging.debug('Send the mail')
        smtp.sendmail(get_user(), receivers, mail.as_string())
        logging.info("Mail sent successfuly")
    else:
        sendmail = '/usr/sbin/sendmail'
        logging.debug('Send the mail')
        p = os.popen('%s -t' % sendmail, 'w')
        logging.debug('Final mail : ' + mail.as_string())
        logging.debug('Send the mail')
        p.write(mail.as_string())
        status = p.close()
        if status is not None:
            logging.error("Sendmail returned %s" % status)
        else:
            logging.info("Mail sent successfuly")
