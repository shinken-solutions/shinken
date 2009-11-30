SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
--
-- Database design for the merlin database
--

DROP TABLE IF EXISTS downtime;
CREATE TABLE downtime(
	id						int NOT NULL PRIMARY KEY AUTO_INCREMENT,
	downtime_id				int NOT NULL,
	instance_id				int NOT NULL DEFAULT 0,
	host_name				varchar(255),
	service_description		varchar(255),
	entry_time				int(11),
	start_time				int(11),
	end_time				int(11),
	triggered_by			int,
	fixed					int,
	duration				int(11),
	author					varchar(255) NOT NULL DEFAULT '',
	comment					text,
	KEY host_name(host_name),
	KEY service(host_name, service_description),
	KEY end_time(end_time),
	KEY downtime_id(downtime_id)
);

DROP TABLE IF EXISTS notification;
CREATE TABLE notification(
	instance_id				int NOT NULL DEFAULT 0,
	id						int NOT NULL PRIMARY KEY AUTO_INCREMENT,
	notification_type		int,
	start_time				int(11),
	end_time				int(11),
	host_name				varchar(255),
	service_description		varchar(255),
	reason_type				int,
	state					int,
	output					text,
	ack_author				varchar(255),
	ack_data				text,
	escalated				int,
	contacts_notified		int,
	KEY host_name(host_name),
	KEY service_name(host_name, service_description)
);

DROP TABLE IF EXISTS program_status;
CREATE TABLE program_status(
	instance_id						int NOT NULL DEFAULT 0 PRIMARY KEY,
	instance_name					varchar(255),
	is_running						tinyint(2),
	last_alive						int(10),
	program_start					int(10),
	pid								int(6),
	daemon_mode						tinyint(2),
	last_command_check				int(10),
	last_log_rotation				int(10),
	notifications_enabled			tinyint(2),
	active_service_checks_enabled	tinyint(2),
	passive_service_checks_enabled	tinyint(2),
	active_host_checks_enabled		tinyint(2),
	passive_host_checks_enabled		tinyint(2),
	event_handlers_enabled			tinyint(2),
	flap_detection_enabled			tinyint(2),
	failure_prediction_enabled		tinyint(2),
	process_performance_data		tinyint(2),
	obsess_over_hosts				tinyint(2),
	obsess_over_services			tinyint(2),
	check_host_freshness			tinyint(2),
	check_service_freshness			tinyint(2),
	modified_host_attributes		int,
	modified_service_attributes		int,
	global_host_event_handler		text,
	global_service_event_handler	text
);
INSERT INTO program_status(instance_id, instance_name) VALUES(0, "Local Nagios/Merlin Instance");

DROP TABLE IF EXISTS scheduled_downtime;
CREATE TABLE scheduled_downtime(
	instance_id				int NOT NULL DEFAULT 0,
	id						INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
	downtime_type			int,
	host_name				varchar(255),
	service_description		varchar(255),
	entry_time				int(11),
	author_name				varchar(255),
	comment_data			text,
	start_time				int(11),
	end_time				int(11),
	fixed					tinyint(2),
	duration				int(11),
	triggered_by			int,
	downtime_id				int NOT NULL,
	KEY host_downtime(host_name),
	KEY service_downtime(service_description),
	UNIQUE KEY downtime_id(downtime_id)
);

DROP TABLE IF EXISTS comment;
CREATE TABLE comment(
	instance_id			int NOT NULL DEFAULT 0,
	id					INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	host_name			varchar(255),
	service_description	varchar(255),
	comment_type		int,
	entry_time			int(10),
	author_name			varchar(255),
	comment_data		text,
	persistent			tinyint(2),
	source				int,
	entry_type			int,
	expires				int,
	expire_time			int(10),
	comment_id			int not null,
	KEY host_comment(host_name),
	KEY service_comment(host_name, service_description),
	UNIQUE KEY comment_id(comment_id)
);


DROP TABLE IF EXISTS gui_action_log;
CREATE TABLE gui_action_log(
	user			VARCHAR(30) NOT NULL,
	action			VARCHAR(50) NOT NULL,
	time			TIMESTAMP
) ;

DROP TABLE IF EXISTS gui_access;
CREATE TABLE gui_access(
	user			VARCHAR(30) NOT NULL PRIMARY KEY,
	view			BOOL,
	view_all		BOOL,
	modify_obj		BOOL,
	modify_any		BOOL,
	delete_obj		BOOL,
	delete_all		BOOL,
	import			BOOL,
	probe			BOOL,
	admin			BOOL
) ;
INSERT INTO gui_access VALUES('monitor', 1, 1, 1, 1, 1, 1, 1, 1, 1);


DROP TABLE IF EXISTS contact;
CREATE TABLE contact(
	instance_id							INT NOT NULL DEFAULT 0,
	id								    INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	contact_name					    VARCHAR(75),
	alias							    VARCHAR(160) NOT NULL,
	host_notifications_enabled			BOOL,
	service_notifications_enabled		BOOL,
	can_submit_commands					BOOL,
	retain_status_information			BOOL,
	retain_nonstatus_information		BOOL,
	host_notification_period		    INT,
	service_notification_period		    INT,
	host_notification_options		    VARCHAR(15),
	service_notification_options	    VARCHAR(15),
	host_notification_commands		    TEXT,
	service_notification_commands       TEXT,
	email							    VARCHAR(60),
	pager							    VARCHAR(18),
	address1						    VARCHAR(100),
	address2						    VARCHAR(100),
	address3						    VARCHAR(100),
	address4						    VARCHAR(100),
	address5						    VARCHAR(100),
	address6						    VARCHAR(100),
	last_host_notification				INT(10),
	last_service_notification			INT(10)
) ;
CREATE UNIQUE INDEX contact_name ON contact(contact_name);

-- contact, contactgroup:
DROP TABLE IF EXISTS contact_contactgroup;
CREATE TABLE contact_contactgroup(
	contact			INT NOT NULL,
	contactgroup	INT NOT NULL
) ;


DROP TABLE IF EXISTS contactgroup;
CREATE TABLE contactgroup(
	instance_id			int NOT NULL DEFAULT 0,
	id					INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	contactgroup_name	VARCHAR(75) NOT NULL,
	alias				VARCHAR(160) NOT NULL
) ;
CREATE UNIQUE INDEX contactgroup_name ON contactgroup(contactgroup_name);

DROP TABLE IF EXISTS timeperiod;
CREATE TABLE timeperiod(
	instance_id				int NOT NULL DEFAULT 0,
	id						INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	timeperiod_name			VARCHAR(75) NOT NULL,
	alias					VARCHAR(160) NOT NULL,
	sunday					VARCHAR(50),
	monday					VARCHAR(50),
	tuesday					VARCHAR(50),
	wednesday				VARCHAR(50),
	thursday				VARCHAR(50),
	friday					VARCHAR(50),
	saturday				VARCHAR(50)
) ;
CREATE UNIQUE INDEX timeperiod_name ON timeperiod(timeperiod_name);

-- junction table for timeperiod<->exclude
DROP TABLE IF EXISTS timeperiod_exclude;
CREATE TABLE timeperiod_exclude(
	timeperiod	INT NOT NULL,
	exclude		INT NOT NULL
) ;


DROP TABLE IF EXISTS command;
CREATE TABLE command(
	instance_id		int NOT NULL DEFAULT 0,
	id				INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	command_name	VARCHAR(75) NOT NULL,
	command_line	BLOB NOT NULL
) ;
CREATE UNIQUE INDEX command_name ON command(command_name);


-- host table
DROP TABLE IF EXISTS host;
CREATE TABLE host(
	instance_id						int NOT NULL DEFAULT 0,
	id								INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	host_name						VARCHAR(75),
	alias							VARCHAR(100) NOT NULL,
	display_name					VARCHAR(100),
	address							VARCHAR(75) NOT NULL,
	initial_state					VARCHAR(18),
	check_command					TEXT,
	max_check_attempts				SMALLINT,
	check_interval					SMALLINT,
	retry_interval					SMALLINT,
	active_checks_enabled			BOOL,
	passive_checks_enabled			BOOL,
	check_period					VARCHAR(75),
	obsess_over_host				BOOL,
	check_freshness					BOOL,
	freshness_threshold				FLOAT,
	event_handler					INT,
	event_handler_args				TEXT,
	event_handler_enabled			BOOL,
	low_flap_threshold				FLOAT,
	high_flap_threshold				FLOAT,
	flap_detection_enabled			BOOL,
	flap_detection_options			VARCHAR(18),
	process_perf_data				BOOL,
	retain_status_information 		BOOL,
	retain_nonstatus_information	BOOL,
	notification_interval			MEDIUMINT,
	first_notification_delay		INT,
	notification_period				VARCHAR(75),
	notification_options			VARCHAR(15),
	notifications_enabled			BOOL,
	stalking_options				VARCHAR(15),
	notes				VARCHAR(255),
	notes_url			VARCHAR(255),
	action_url			VARCHAR(255),
	icon_image			VARCHAR(60),
	icon_image_alt		VARCHAR(60),
	statusmap_image		VARCHAR(60),
	2d_coords			VARCHAR(20),
	3d_coords			VARCHAR(30),
	vrml_image			VARCHAR(60),
	failure_prediction_enabled		BOOL,
	problem_has_been_acknowledged int(10) NOT NULL default 0,
	acknowledgement_type int(10) NOT NULL default 0,
	check_type int(10) NOT NULL default '0',
	current_state int(10) NOT NULL default '0',
	last_state int(10) NOT NULL default '0',
	last_hard_state int(10) NOT NULL default '0',
	last_notification int(10) NOT NULL default '0',
	output text,
	long_output text,
	perf_data text,
	state_type int(10) NOT NULL default '0',
	current_attempt int(10) NOT NULL default '0',
	latency float,
	execution_time float,
	is_executing int(10) NOT NULL default '0',
	check_options int(10) NOT NULL default '0',
	last_host_notification int(10),
	next_host_notification int(10),
	next_check int(10),
	should_be_scheduled int(10) NOT NULL default '0',
	last_check int(10),
	last_state_change int(10),
	last_hard_state_change int(10),
	last_time_up int(10),
	last_time_down int(10),
	last_time_unreachable int(10),
	has_been_checked int(10) NOT NULL default '0',
	is_being_freshened int(10) NOT NULL default '0',
	notified_on_down int(10) NOT NULL default '0',
	notified_on_unreachable int(10) NOT NULL default '0',
	current_notification_number int(10) NOT NULL default '0',
	no_more_notifications int(10) NOT NULL default '0',
	current_notification_id int(10) NOT NULL default '0',
	check_flapping_recovery_notification int(10) NOT NULL default '0',
	scheduled_downtime_depth int(10) NOT NULL default '0',
	pending_flex_downtime int(10) NOT NULL default '0',
	is_flapping int(10) NOT NULL default '0',
	flapping_comment_id int(10) NOT NULL default '0',
	percent_state_change float,
	total_services int(10) NOT NULL default '0',
	total_service_check_interval int(10) NOT NULL default '0',
	modified_attributes int(10) NOT NULL default '0',
	current_problem_id int(10) NOT NULL default '0',
	last_problem_id int(10) NOT NULL default '0',
	max_attempts int(10) NOT NULL default '1',
	current_event_id int(10) NOT NULL default '0',
	last_event_id int(10) NOT NULL default '0',
	process_performance_data int(10) NOT NULL default '0',
	last_update int(10) NOT NULL default '0',
	timeout int(10),
	start_time int(10),
	end_time int(10),
	early_timeout smallint(1),
	return_code smallint(8),
	KEY host_status_1_idx (next_check, host_name),
	KEY host_status_2_idx (last_check, host_name),
	KEY host_status_3_idx (last_state_change, host_name),
	KEY host_status_4_idx (last_hard_state_change, host_name),
	KEY host_status_5_idx (last_time_up, host_name),
	KEY host_status_6_idx (last_time_down, host_name),
	KEY host_status_7_idx (last_time_unreachable, host_name),
	KEY host_status_8_idx (latency, host_name),
	KEY host_status_9_idx (execution_time, host_name)
) ;
CREATE UNIQUE INDEX host_name ON host(host_name);

-- junctions for host objects
DROP TABLE IF EXISTS host_parents;
CREATE TABLE host_parents(
	host	 INT NOT NULL,
	parents	 INT NOT NULL
) ;

DROP TABLE IF EXISTS host_contact;
CREATE TABLE host_contact(
	host	INT NOT NULL,
	contact	INT NOT NULL
) ;

DROP TABLE IF EXISTS host_contactgroup;
CREATE TABLE host_contactgroup(
	host			INT NOT NULL,
	contactgroup	INT NOT NULL
) ;

DROP TABLE IF EXISTS host_hostgroup;
CREATE TABLE host_hostgroup(
	host		INT NOT NULL,
	hostgroup	INT NOT NULL
) ;


DROP TABLE IF EXISTS hostgroup;
CREATE TABLE hostgroup(
	instance_id			int NOT NULL DEFAULT 0,
	id 		 			INT NOT NULL PRIMARY KEY,
	hostgroup_name		VARCHAR(75),
	alias				VARCHAR(160),
	notes				VARCHAR(160),
	notes_url			VARCHAR(160),
	action_url			VARCHAR(160)
) ;
CREATE UNIQUE INDEX hostgroup_name ON hostgroup(hostgroup_name);


DROP TABLE IF EXISTS service;
CREATE TABLE service(
	instance_id						int NOT NULL DEFAULT 0,
	id								INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	host_name						VARCHAR(75) NOT NULL,
	service_description				VARCHAR(160) NOT NULL,
	display_name					VARCHAR(160),
	is_volatile						BOOL,
	check_command					TEXT,
	initial_state					VARCHAR(1),
	max_check_attempts				SMALLINT,
	check_interval					SMALLINT,
	retry_interval					SMALLINT,
	active_checks_enabled			BOOL,
	passive_checks_enabled			BOOL,
	check_period					VARCHAR(75),
	parallelize_check				BOOL,
	obsess_over_service				BOOL,
	check_freshness					BOOL,
	freshness_threshold				INT,
	event_handler					INT,
	event_handler_args				TEXT,
	event_handler_enabled			BOOL,
	low_flap_threshold				FLOAT,
	high_flap_threshold				FLOAT,
	flap_detection_enabled			BOOL,
	flap_detection_options			VARCHAR(18),
	process_perf_data				BOOL,
	retain_status_information		BOOL,
	retain_nonstatus_information	BOOL,
	notification_interval			INT,
	first_notification_delay		INT,
	notification_period				VARCHAR(75),
	notification_options			VARCHAR(15),
	notifications_enabled			BOOL,
	stalking_options				VARCHAR(15),
	notes							VARCHAR(255),
	notes_url						VARCHAR(255),
	action_url						VARCHAR(255),
	icon_image						VARCHAR(60),
	icon_image_alt					VARCHAR(60),
	failure_prediction_enabled		BOOL,
	problem_has_been_acknowledged int(10) NOT NULL default '0',
	acknowledgement_type int(10) NOT NULL default '0',
	host_problem_at_last_check int(10) NOT NULL default '0',
	check_type int(10) NOT NULL default '0',
	current_state int(10) NOT NULL default '0',
	last_state int(10) NOT NULL default '0',
	last_hard_state int(10) NOT NULL default '0',
	output text,
	long_output text,
	perf_data text,
	state_type int(10) NOT NULL default '0',
	next_check int(10),
	should_be_scheduled int(10) NOT NULL default '0',
	last_check int(10),
	current_attempt int(10) NOT NULL default '0',
	current_event_id int(10) NOT NULL default '0',
	last_event_id int(10) NOT NULL default '0',
	current_problem_id int(10) NOT NULL default '0',
	last_problem_id int(10) NOT NULL default '0',
	last_notification int(10),
	next_notification int(10),
	no_more_notifications int(10) NOT NULL default '0',
	check_flapping_recovery_notification int(10) NOT NULL default '0',
	last_state_change int(10),
	last_hard_state_change int(10),
	last_time_ok int(10),
	last_time_warning int(10),
	last_time_unknown int(10),
	last_time_critical int(10),
	has_been_checked int(10) NOT NULL default '0',
	is_being_freshened int(10) NOT NULL default '0',
	notified_on_unknown int(10) NOT NULL default '0',
	notified_on_warning int(10) NOT NULL default '0',
	notified_on_critical int(10) NOT NULL default '0',
	current_notification_number int(10) NOT NULL default '0',
	current_notification_id int(10) NOT NULL default '0',
	latency float,
	execution_time float,
	is_executing int(10) NOT NULL default '0',
	check_options int(10) NOT NULL default '0',
	scheduled_downtime_depth int(10) NOT NULL default '0',
	pending_flex_downtime int(10) NOT NULL default '0',
	is_flapping int(10) NOT NULL default '0',
	flapping_comment_id int(10) NOT NULL default '0',
	percent_state_change float,
	modified_attributes int(10) NOT NULL default '0',
	max_attempts int(10) NOT NULL default '0',
	process_performance_data int(10) NOT NULL default '0',
	last_update int(10) NOT NULL default '0',
	timeout int(10),
	start_time int(10),
	end_time int(10),
	early_timeout smallint(1),
	return_code smallint(8),
	UNIQUE KEY service_name(host_name, service_description),
	KEY service_status_1_idx (next_check, host_name, service_description),
	KEY service_status_2_idx (last_check, host_name, service_description),
	KEY service_status_3_idx (last_state_change, host_name, service_description),
	KEY service_status_4_idx (last_hard_state_change, host_name, service_description),
	KEY service_status_5_idx (last_time_ok, host_name, service_description),
	KEY service_status_6_idx (last_time_warning, host_name, service_description),
	KEY service_status_7_idx (last_time_unknown, host_name, service_description),
	KEY service_status_8_idx (last_time_critical, host_name, service_description),
	KEY service_status_9_idx (latency, host_name, service_description),
	KEY service_status_10_idx (execution_time, host_name, service_description)
) ;

-- junctions for service objects
DROP TABLE IF EXISTS service_contact;
CREATE TABLE service_contact(
	service	INT NOT NULL,
	contact	INT NOT NULL
) ;

DROP TABLE IF EXISTS service_contactgroup;
CREATE TABLE service_contactgroup(
	service			INT NOT NULL,
	contactgroup	INT NOT NULL
) ;

DROP TABLE IF EXISTS service_servicegroup;
CREATE TABLE service_servicegroup(
	service			INT NOT NULL,
	servicegroup	INT NOT NULL
) ;


DROP TABLE IF EXISTS servicegroup;
CREATE TABLE servicegroup(
	instance_id			int NOT NULL DEFAULT 0,
	id					INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	servicegroup_name	VARCHAR(75) NOT NULL,
	alias				VARCHAR(160) NOT NULL,
	notes				VARCHAR(160),
	notes_url			VARCHAR(160),
	action_url			VARCHAR(160)
) ;
CREATE UNIQUE INDEX servicegroup_name ON servicegroup(servicegroup_name);


DROP TABLE IF EXISTS servicedependency;
CREATE TABLE servicedependency(
	id								INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	service							INT NOT NULL,
	dependent_service				INT NOT NULL,
	dependency_period				VARCHAR(75),
	inherits_parent					BOOL,
	execution_failure_options		VARCHAR(15),
	notification_failure_options	VARCHAR(15)
) ;


DROP TABLE IF EXISTS serviceescalation;
CREATE TABLE serviceescalation(
	instance_id						int NOT NULL DEFAULT 0,
	id								INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	service							INT NOT NULL,
	first_notification				MEDIUMINT,
	last_notification				MEDIUMINT,
	notification_interval			MEDIUMINT,
	escalation_period				VARCHAR(75),
	escalation_options				VARCHAR(15)
) ;

-- junctions for serviceescalation objects
DROP TABLE IF EXISTS serviceescalation_contact;
CREATE TABLE serviceescalation_contact(
	serviceescalation	INT NOT NULL,
	contact				INT NOT NULL
) ;

DROP TABLE IF EXISTS serviceescalation_contactgroup;
CREATE TABLE serviceescalation_contactgroup(
	serviceescalation	INT NOT NULL,
	contactgroup		INT NOT NULL
) ;


DROP TABLE IF EXISTS hostdependency;
CREATE TABLE hostdependency(
	instance_id						int NOT NULL DEFAULT 0,
	id								INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	host_name						INT NOT NULL,
	dependent_host_name				INT NOT NULL,
	dependency_period				VARCHAR(75),
	inherits_parent					BOOL,
	execution_failure_options		VARCHAR(15),
	notification_failure_options	VARCHAR(15)
) ;

DROP TABLE IF EXISTS hostescalation;
CREATE TABLE hostescalation(
	instance_id						int NOT NULL DEFAULT 0,
	id								INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	template						INT,
	host_name						INT NOT NULL,
	first_notification				INT,
	last_notification				INT,
	notification_interval			INT,
	escalation_period				VARCHAR(75),
	escalation_options				VARCHAR(15)
) ;


DROP TABLE IF EXISTS hostescalation_contact;
CREATE TABLE hostescalation_contact(
	hostescalation	INT NOT NULL,
	contact			INT NOT NULL
) ;

DROP TABLE IF EXISTS hostescalation_contactgroup;
CREATE TABLE hostescalation_contactgroup(
	hostescalation		INT NOT NULL,
	contactgroup		INT NOT NULL
) ;


-- custom variables
DROP TABLE IF EXISTS custom_vars;
CREATE TABLE custom_vars(
	obj_type	VARCHAR(30) NOT NULL,
	obj_id		INT NOT NULL,
	variable	VARCHAR(100),
	value		VARCHAR(255)
) ;
-- No single object can have multiple variables named the same
CREATE UNIQUE INDEX objvar ON custom_vars(obj_type, obj_id, variable);

-- gui <=> webconfig db scheme cross-pollination ends here

-- Obsoleted tables
DROP TABLE IF EXISTS hostextinfo;
DROP TABLE IF EXISTS serviceextinfo;

DROP TABLE IF EXISTS `db_version`;
CREATE TABLE `db_version` (
  `version` int(11)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
INSERT INTO db_version(version) VALUES(1);

DROP TABLE IF EXISTS `report_data`;
CREATE TABLE `report_data` (
  `id` int(11) NOT NULL auto_increment,
  `timestamp` int(11) NOT NULL default '0',
  `event_type` int(11) NOT NULL default '0',
  `flags` int(11),
  `attrib` int(11),
  `host_name` varchar(160) default '',
  `service_description` varchar(160) default '',
  `state` int(2) NOT NULL default '0',
  `hard` int(2) NOT NULL default '0',
  `retry` int(5) NOT NULL default '0',
  `downtime_depth` int(11),
  `output` text,
  PRIMARY KEY  (`id`),
  KEY          (`timestamp`),
  KEY event_type (event_type),
  KEY host_name (host_name),
  KEY host_name_2 (host_name,service_description),
  KEY state (state)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
