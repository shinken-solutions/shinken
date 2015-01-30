# -*- coding: utf-8 -*-


from shinken.daemon import get_cur_user, get_cur_group

from shinken.objects.arbiterlink import ArbiterLink
from shinken.objects.brokerlink import BrokerLink
from shinken.objects.hostextinfo import HostExtInfo
from shinken.objects.pollerlink import PollerLink
from shinken.objects.reactionnerlink import ReactionnerLink
from shinken.objects.receiverlink import ReceiverLink
from shinken.objects.schedulerlink import SchedulerLink
from shinken.objects.service import Service
from shinken.objects.contact import Contact
from shinken.objects.host import Host

from shinken.property import (
    Property,
    UnusedProp,
    BoolProp,
    CharProp,
    StringProp,
    IntegerProp,
    LogLevelProp,
    ListProp,
)


not_interesting_txt = 'We do not think such an option is interesting to manage.'

no_longer_used_txt = (
    'This parameter is not longer take from the main file, but must be defined '
    'in the status_dat broker module instead. But Shinken will create you one '
    'if there are no present and use this parameter in it, so no worry.')


properties = {}  # will be populated at end of this file..


# Properties:
# *required: if True, there is not default, and the config must put them
# *default: if not set, take this value
# *pythonize: function call to
# *class_inherit: (Service, 'blabla'): must set this property to the
#  Service class with name blabla
#  if (Service, None): must set this property to the Service class with
#  same name
# *unused: just to warn the user that the option he use is no more used
#  in Shinken
# *usage_text: if present, will print it to explain why it's no more useful


prefix = StringProp(default='/usr/local/shinken/')

workdir = StringProp(default='/var/run/shinken/')

config_base_dir = StringProp(default='')  # will be set when we will load a file

modules_dir = StringProp(default='/var/lib/shinken/modules')

use_local_log = BoolProp(default=True)

log_level = LogLevelProp(default='WARNING')

local_log = StringProp(default='/var/log/shinken/arbiterd.log')

log_file = UnusedProp(text=no_longer_used_txt)

object_cache_file = UnusedProp(text=no_longer_used_txt)

precached_object_file = UnusedProp(text='Shinken does not use precached_object_files. Skipping.')

resource_file = StringProp(default='/tmp/resources.txt')

temp_file = UnusedProp(text='Temporary files are not used in the shinken architecture. Skipping')

status_file = UnusedProp(text=no_longer_used_txt)

status_update_interval = UnusedProp(text=no_longer_used_txt)

shinken_user = StringProp(default=get_cur_user())

shinken_group = StringProp(default=get_cur_group())

enable_notifications = BoolProp(default=True,
                                class_inherit=[(Host, None), (Service, None), (Contact, None)])

execute_service_checks = BoolProp(default=True, class_inherit=[(Service, 'execute_checks')])

accept_passive_service_checks = BoolProp(default=True,
                                         class_inherit=[(Service, 'accept_passive_checks')])

execute_host_checks = BoolProp(default=True, class_inherit=[(Host, 'execute_checks')])

accept_passive_host_checks = BoolProp(default=True, class_inherit=[(Host, 'accept_passive_checks')])

enable_event_handlers = BoolProp(default=True, class_inherit=[(Host, None), (Service, None)])

log_rotation_method = CharProp(default='d')

log_archive_path = StringProp(default='/usr/local/shinken/var/archives')

check_external_commands = BoolProp(default=True)

command_check_interval = UnusedProp(
    text='another value than look always the file is useless, so we fix it.')

command_file = StringProp(default='')

external_command_buffer_slots = UnusedProp(text='We do not limit the external command slot.')

check_for_updates = UnusedProp(
    text='network administrators will never allow such communication between '
         'server and the external world. Use your distribution packet manager '
         'to know if updates are available or go to the '
         'http://www.shinken-monitoring.org website instead.')

bare_update_checks = UnusedProp(text=None)

lock_file = StringProp(default='/var/run/shinken/arbiterd.pid')

retain_state_information = UnusedProp(
    text='sorry retain state information will not be implemented because it is useless.')

state_retention_file = StringProp(default='')

retention_update_interval = IntegerProp(default=60)

use_retained_program_state = UnusedProp(text=not_interesting_txt)

use_retained_scheduling_info = UnusedProp(text=not_interesting_txt)

retained_host_attribute_mask = UnusedProp(text=not_interesting_txt)

retained_service_attribute_mask = UnusedProp(text=not_interesting_txt)

retained_process_host_attribute_mask = UnusedProp(text=not_interesting_txt)

retained_process_service_attribute_mask = UnusedProp(text=not_interesting_txt)

retained_contact_host_attribute_mask = UnusedProp(text=not_interesting_txt)

retained_contact_service_attribute_mask = UnusedProp(text=not_interesting_txt)

use_syslog = BoolProp(default=False)

log_notifications = BoolProp(default=True, class_inherit=[(Host, None), (Service, None)])

log_service_retries = BoolProp(default=True, class_inherit=[(Service, 'log_retries')])

log_host_retries = BoolProp(default=True, class_inherit=[(Host, 'log_retries')])

log_event_handlers = BoolProp(default=True, class_inherit=[(Host, None), (Service, None)])

log_initial_states = BoolProp(default=True, class_inherit=[(Host, None), (Service, None)])

log_external_commands = BoolProp(default=True)

log_passive_checks = BoolProp(default=True)

global_host_event_handler = StringProp(default='', class_inherit=[(Host, 'global_event_handler')])

global_service_event_handler = StringProp(default='',
                                          class_inherit=[(Service, 'global_event_handler')])

sleep_time = UnusedProp(text='this deprecated option is useless in the shinken way of doing.')

service_inter_check_delay_method = UnusedProp(
    text='This option is useless in the Shinken scheduling. The only way is the smart way.')

max_service_check_spread = IntegerProp(default=30, class_inherit=[(Service, 'max_check_spread')])

service_interleave_factor = UnusedProp(
    text='This option is useless in the Shinken scheduling '
         'because it use a random distribution for initial checks.')

max_concurrent_checks = UnusedProp(
    text='Limiting the max concurrent checks is not helpful '
         'to got a good running monitoring server.')

check_result_reaper_frequency = UnusedProp(text='Shinken do not use reaper process.')

max_check_result_reaper_time = UnusedProp(text='Shinken do not use reaper process.')

check_result_path = UnusedProp(
    text='Shinken use in memory returns, not check results on flat file.')

max_check_result_file_age = UnusedProp(text='Shinken do not use flat file check resultfiles.')

host_inter_check_delay_method = UnusedProp(
    text='This option is unused in the Shinken scheduling because distribution '
         'of the initial check is a random one.')

max_host_check_spread = IntegerProp(default=30, class_inherit=[(Host, 'max_check_spread')])

interval_length = IntegerProp(default=60, class_inherit=[(Host, None), (Service, None)])

auto_reschedule_checks = BoolProp(managed=False, default=True)

auto_rescheduling_interval = IntegerProp(managed=False, default=1)

auto_rescheduling_window = IntegerProp(managed=False, default=180)

use_aggressive_host_checking = BoolProp(default=False, class_inherit=[(Host, None)])

translate_passive_host_checks = BoolProp(managed=False, default=True)

passive_host_checks_are_soft = BoolProp(managed=False, default=True)

enable_predictive_host_dependency_checks = BoolProp(
    managed=False, default=True,
    class_inherit=[(Host, 'enable_predictive_dependency_checks')])

enable_predictive_service_dependency_checks = BoolProp(managed=False, default=True)

cached_host_check_horizon = IntegerProp(default=0, class_inherit=[(Host, 'cached_check_horizon')])


cached_service_check_horizon = IntegerProp(default=0,
                                           class_inherit=[(Service, 'cached_check_horizon')])

use_large_installation_tweaks = UnusedProp(
    text='this option is deprecated because in shinken it is just an alias '
         'for enable_environment_macros=0')

free_child_process_memory = UnusedProp(text='this option is automatic in Python processes')

child_processes_fork_twice = UnusedProp(text='fork twice is not use.')

enable_environment_macros = BoolProp(default=True, class_inherit=[(Host, None), (Service, None)])

enable_flap_detection = BoolProp(default=True, class_inherit=[(Host, None), (Service, None)])

low_service_flap_threshold = IntegerProp(default=20,
                                         class_inherit=[(Service, 'global_low_flap_threshold')])

high_service_flap_threshold = IntegerProp(default=30,
                                          class_inherit=[(Service, 'global_high_flap_threshold')])

low_host_flap_threshold = IntegerProp(default=20,
                                      class_inherit=[(Host, 'global_low_flap_threshold')])

high_host_flap_threshold = IntegerProp(default=30,
                                       class_inherit=[(Host, 'global_high_flap_threshold')])

soft_state_dependencies = BoolProp(managed=False, default=False)

service_check_timeout = IntegerProp(default=60, class_inherit=[(Service, 'check_timeout')])

host_check_timeout = IntegerProp(default=30, class_inherit=[(Host, 'check_timeout')])

timeout_exit_status = IntegerProp(default=2)

event_handler_timeout = IntegerProp(default=30, class_inherit=[(Host, None), (Service, None)])

notification_timeout = IntegerProp(default=30, class_inherit=[(Host, None), (Service, None)])

ocsp_timeout = IntegerProp(default=15, class_inherit=[(Service, None)])

ochp_timeout = IntegerProp(default=15, class_inherit=[(Host, None)])

perfdata_timeout = IntegerProp(default=5, class_inherit=[(Host, None), (Service, None)])

obsess_over_services = BoolProp(default=False, class_inherit=[(Service, 'obsess_over')])

ocsp_command = StringProp(default='', class_inherit=[(Service, None)])

obsess_over_hosts = BoolProp(default=False, class_inherit=[(Host, 'obsess_over')])

ochp_command = StringProp(default='', class_inherit=[(Host, None)])

process_performance_data = BoolProp(default=True, class_inherit=[(Host, None), (Service, None)])

host_perfdata_command = StringProp(default='', class_inherit=[(Host, 'perfdata_command')])

service_perfdata_command = StringProp(default='', class_inherit=[(Service, 'perfdata_command')])

host_perfdata_file = StringProp(default='', class_inherit=[(Host, 'perfdata_file')])

service_perfdata_file = StringProp(default='', class_inherit=[(Service, 'perfdata_file')])

host_perfdata_file_template = StringProp(default='/tmp/host.perf',
                                         class_inherit=[(Host, 'perfdata_file_template')])

service_perfdata_file_template = StringProp(default='/tmp/host.perf',
                                            class_inherit=[(Service, 'perfdata_file_template')])

host_perfdata_file_mode = CharProp(default='a', class_inherit=[(Host, 'perfdata_file_mode')])

service_perfdata_file_mode = CharProp(default='a', class_inherit=[(Service, 'perfdata_file_mode')])

host_perfdata_file_processing_interval = IntegerProp(managed=False, default=15)

service_perfdata_file_processing_interval = IntegerProp(managed=False, default=15)

host_perfdata_file_processing_command = StringProp(
    managed=False, default='',
    class_inherit=[(Host, 'perfdata_file_processing_command')])

service_perfdata_file_processing_command = StringProp(managed=False, default=None)

check_for_orphaned_services = BoolProp(default=True,
                                       class_inherit=[(Service, 'check_for_orphaned')])

check_for_orphaned_hosts = BoolProp(default=True,
                                    class_inherit=[(Host, 'check_for_orphaned')])

check_service_freshness = BoolProp(default=True,
                                   class_inherit=[(Service, 'global_check_freshness')])

service_freshness_check_interval = IntegerProp(default=60)

check_host_freshness = BoolProp(default=True, class_inherit=[(Host, 'global_check_freshness')])

host_freshness_check_interval = IntegerProp(default=60)

additional_freshness_latency = IntegerProp(
    default=15, class_inherit=[(Host, None), (Service, None)])

enable_embedded_perl = BoolProp(
    managed=False, default=True,
    help='It will surely never be managed, '
         'but it should not be useful with poller performances.')

use_embedded_perl_implicitly = BoolProp(managed=False, default=False)

date_format = StringProp(managed=False, default=None)

use_timezone = StringProp(default='',
                          class_inherit=[(Host, None), (Service, None), (Contact, None)])

illegal_object_name_chars = StringProp(
    default="""`~!$%^&*"|'<>?,()=""",
    class_inherit=[(Host, None), (Service, None),
                   (Contact, None), (HostExtInfo, None)])

illegal_macro_output_chars = StringProp(
    default='',
    class_inherit=[(Host, None), (Service, None), (Contact, None)])

use_regexp_matching = BoolProp(
    managed=False, default=False,
    help='If you go some host or service definition like prod*, '
         'it will surely failed from now, sorry.')

use_true_regexp_matching = BoolProp(managed=False, default=None)

admin_email = UnusedProp(text='sorry, not yet implemented.')

admin_pager = UnusedProp(text='sorry, not yet implemented.')

event_broker_options = UnusedProp(
    text='event broker are replaced by modules with a real configuration template.')

broker_module = StringProp(default='')

debug_file = UnusedProp(text=None)

debug_level = UnusedProp(text=None)

debug_verbosity = UnusedProp(text=None)

max_debug_file_size = UnusedProp(text=None)

modified_attributes = IntegerProp(default=0L)
# '$USERn$: {'required':False, 'default':''} # Add at run in __init__

# SHINKEN SPECIFIC
idontcareaboutsecurity = BoolProp(default=False)

daemon_enabled = BoolProp(default=True)  # Put to 0 to disable the arbiter to run

daemon_thread_pool_size = IntegerProp(default=8)

flap_history = IntegerProp(default=20, class_inherit=[(Host, None), (Service, None)])

max_plugins_output_length = IntegerProp(default=8192, class_inherit=[(Host, None), (Service, None)])

no_event_handlers_during_downtimes = BoolProp(
    default=False, class_inherit=[(Host, None), (Service, None)])

# Interval between cleaning queues pass
cleaning_queues_interval = IntegerProp(default=900)

# Enable or not the notice about old Nagios parameters
disable_old_nagios_parameters_whining = BoolProp(default=False)

# Now for problem/impact states changes
enable_problem_impacts_states_change = BoolProp(
    default=False, class_inherit=[(Host, None), (Service, None)])

# More a running value in fact
resource_macros_names = ListProp(default=[])

http_backend = StringProp(default='auto')

# SSL PART
# global boolean for know if we use ssl or not
use_ssl = BoolProp(default=False,
                   class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                                  (BrokerLink, None), (PollerLink, None),
                                  (ReceiverLink, None),  (ArbiterLink, None)])

ca_cert = StringProp(default='etc/certs/ca.pem')

server_cert = StringProp(default='etc/certs/server.cert')

server_key = StringProp(default='etc/certs/server.key')

hard_ssl_name_check = BoolProp(default=False)

# Log format
human_timestamp_log = BoolProp(default=False)

# Discovery part
strip_idname_fqdn = BoolProp(default=True)

runners_timeout = IntegerProp(default=3600)

# pack_distribution_file is for keeping a distribution history
# of the host distribution in the several "packs" so a same
# scheduler will have more change of getting the same host
pack_distribution_file = StringProp(default='pack_distribution.dat')

# WEBUI part
webui_lock_file = StringProp(default='webui.pid')

webui_port = IntegerProp(default=8080)

webui_host = StringProp(default='0.0.0.0')

# Large env tweacks
use_multiprocesses_serializer = BoolProp(default=False)

# About shinken.io part
api_key = StringProp(default='',
                     class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                                    (BrokerLink, None), (PollerLink, None),
                                    (ReceiverLink, None),  (ArbiterLink, None)])

secret = StringProp(default='',
                    class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                                   (BrokerLink, None), (PollerLink, None),
                                   (ReceiverLink, None),  (ArbiterLink, None)])

http_proxy = StringProp(
    default='',
    class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                   (BrokerLink, None), (PollerLink, None),
                   (ReceiverLink, None),  (ArbiterLink, None)])

# and local statsd one
statsd_host = StringProp(
    default='localhost',
    class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                   (BrokerLink, None), (PollerLink, None),
                   (ReceiverLink, None),  (ArbiterLink, None)])

statsd_port = IntegerProp(
    default=8125,
    class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                   (BrokerLink, None), (PollerLink, None),
                   (ReceiverLink, None),  (ArbiterLink, None)])

statsd_prefix = StringProp(
    default='shinken',
    class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                   (BrokerLink, None), (PollerLink, None),
                   (ReceiverLink, None),  (ArbiterLink, None)])

statsd_enabled = BoolProp(
    default=False,
    class_inherit=[(SchedulerLink, None), (ReactionnerLink, None),
                   (BrokerLink, None), (PollerLink, None),
                   (ReceiverLink, None),  (ArbiterLink, None)])

# now load all Property instances into the `properties´ dict:
for k, v in locals().items():
    if isinstance(v, Property):
        properties[k] = v
