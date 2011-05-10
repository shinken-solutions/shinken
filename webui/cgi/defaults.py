# These defaults are used for running check_mk directly
# from the source directory without installing it.

import os

my_dir = os.path.dirname(__file__)


default_config_dir          = '.'
check_mk_configdir          = 'conf.d'
checks_dir                  = 'checks'
check_manpages_dir          = 'checkman'
agents_dir                  = 'agents'
modules_dir                 = 'modules'
var_dir                     = 'var'
autochecksdir               = 'var/autochecks'
precompiled_hostchecks_dir  = 'var/precompiled'
counters_directory          = 'var/counters'
tcp_cache_dir		    = 'var/cache'
rrd_path                    = 'var/rrd'
nagios_command_pipe_path    = 'nagios/nagios.cmd'
nagios_conf_dir             = ''
nagios_objects_file         = 'var/check_mk_objects.cfg'
nagios_user                 = 'nagios'
lib_dir                     = 'livestatus'
apache_config_dir           = '/etc/apache2/conf.d/'
nagios_status_file          = '/var/lib/nagios/status.dat'
htpasswd_file               = 'webusers'
#livestatus_unix_socket      = 'nagios/live'
livestatus_tcp_socket       = 'localhost:50000'
#web_dir                     = 'C:\\wamp\\www\\web\\'

#Web dir is one level higer than myself
web_dir                     = os.path.dirname(my_dir)# #'/home/shinken/check_mk/web'
#cgi_dir                     = os.path.join(web_dir, 'cgi')
www_group                   = 'www-data'
check_mk_version            = '1.1.11i1'
url_prefix                  = '/'
