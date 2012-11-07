use CENTREON;

update CENTREON.cfg_nagios set
	log_file='TARGET/var/nagios.log',
	cfg_dir='TARGET/etc/',
	temp_file='TARGET/var/nagios.tmp',
	status_file='TARGET/var/status.log',
	log_archive_path='TARGET/var/archives',
	command_file='TARGET/var/rw/nagios.cmd',
	downtime_file='TARGET/var/downtime.log',
	comment_file='TARGET/var/comment.log',
	lock_file='TARGET/var/nagios.lock',
	state_retention_file='TARGET/var/status.sav'
where
nagios_id = '1';

update CENTREON.nagios_server set
	nagios_bin='TARGET/bin/nagios',
	init_script='/etc/init.d/shinken',
	nagios_perfdata='TARGET/var/service-perfdata'
where
id = '1';

update CENTREON.options set value='TARGET' where `key`='nagios_path';

update CENTREON.options set value='TARGET/bin/nagios' where `key`='nagios_path_bin';

update CENTREON.options set value='/etc/init.d/shinken' where `key`='nagios_init_script';

update CENTREON.cfg_cgi set main_config_file='TARGET/etc/nagios.cfg' where cgi_id=10;

