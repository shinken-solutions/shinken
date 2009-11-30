-- --------------------------------------------------------
-- oracle.sql
-- DB definition for Oracle
--
-- requires ocilib, oracle (instantclient) libs+sdk  to work
-- specify oracle (instantclient) libs+sdk in ocilib configure
-- ./configure \
--	--with-oracle-headers-path=/opt/oracle/product/instantclient/instantclient_11_1/sdk/include \
--	--with-oracle-lib-path=/opt/oracle/product/instantclient/instantclient_11_1/
--
-- enable ocilib in Icinga with
-- ./configure --enable-idoutils --enable--oracle
-- 
-- copy to $ORACLE_HOME 
-- # sqlplus username/password
-- SQL> @oracle.sql
--
-- initial version: 2008-02-20 David Schmidt
-- current version: 2009-09-05 Michael Friedrich <michael.friedrich(at)univie.ac.at>
--
-- -- --------------------------------------------------------



-- set escape character
SET ESCAPE \

--
-- Helper Function to convert from unix timestamp to Oracle Date
--
CREATE OR REPLACE FUNCTION unixts2date( n_seconds   IN    PLS_INTEGER)
        RETURN    DATE
IS
        unix_start  DATE    := TO_DATE('01.01.1970','DD.MM.YYYY');
        unix_max    PLS_INTEGER  := 2145916799;
        unix_min    PLS_INTEGER     := -2114380800;

BEGIN

        IF n_seconds > unix_max THEN
                RAISE_APPLICATION_ERROR( -20901, 'UNIX timestamp too large for 32 bit limit' );
        ELSIF n_seconds < unix_min THEN
                RAISE_APPLICATION_ERROR( -20901, 'UNIX timestamp too small for 32 bit limit' );
        ELSE
                RETURN unix_start + NUMTODSINTERVAL( n_seconds, 'SECOND' );
        END IF;

EXCEPTION
        WHEN OTHERS THEN
                RAISE;
END;
/


-- 
-- Database: icinga
-- 

-- --------------------------------------------------------

-- 
-- Table structure for table acknowledgements
-- 

CREATE TABLE acknowledgements (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  entry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  entry_time_usec number(11) default 0 NOT NULL,
  acknowledgement_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  state number(6) default 0 NOT NULL,
  author_name varchar2(64),
  comment_data varchar2(1024),
  is_sticky number(6) default 0 NOT NULL,
  persistent_comment number(6) default 0 NOT NULL,
  notify_contacts number(6) default 0 NOT NULL,
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table commands
-- 

CREATE TABLE commands (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  command_line varchar2(1024),
  PRIMARY KEY  (id),
  CONSTRAINT commands UNIQUE (instance_id,object_id,config_type)
);

-- --------------------------------------------------------

-- 
-- Table structure for table commenthistory
-- 

CREATE TABLE commenthistory (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  entry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  entry_time_usec number(11) default 0 NOT NULL,
  comment_type number(6) default 0 NOT NULL,
  entry_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  comment_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  internal_comment_id number(11) default 0 NOT NULL,
  author_name varchar2(64),
  comment_data varchar2(1024),
  is_persistent number(6) default 0 NOT NULL,
  comment_source number(6) default 0 NOT NULL,
  expires number(6) default 0 NOT NULL,
  expiration_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  deletion_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  deletion_time_usec number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT commenthistory UNIQUE (instance_id,comment_time,internal_comment_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table comments
-- 

CREATE TABLE comments (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  entry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  entry_time_usec number(11) default 0 NOT NULL,
  comment_type number(6) default 0 NOT NULL,
  entry_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  comment_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  internal_comment_id number(11) default 0 NOT NULL,
  author_name varchar2(64),
  comment_data varchar2(1024),
  is_persistent number(6) default 0 NOT NULL,
  comment_source number(6) default 0 NOT NULL,
  expires number(6) default 0 NOT NULL,
  expiration_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT comments UNIQUE (instance_id,comment_time,internal_comment_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table configfiles
-- 

CREATE TABLE configfiles (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  configfile_type number(6) default 0 NOT NULL,
  configfile_path varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT configfiles UNIQUE (instance_id,configfile_type,configfile_path)
);

-- --------------------------------------------------------

-- 
-- Table structure for table configfilevariables
-- 

CREATE TABLE configfilevariables (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  configfile_id number(11) default 0 NOT NULL,
  varname varchar2(64),
  varvalue varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT configfilevariables UNIQUE (instance_id,configfile_id,varname)
);

-- --------------------------------------------------------

-- 
-- Table structure for table conninfo
-- 

CREATE TABLE conninfo (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  agent_name varchar2(32),
  agent_version varchar2(8),
  disposition varchar2(16),
  connect_source varchar2(16),
  connect_type varchar2(16),
  connect_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  disconnect_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_checkin_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  data_start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  data_end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  bytes_processed number(11) default 0 NOT NULL,
  lines_processed number(11) default 0 NOT NULL,
  entries_processed number(11) default 0 NOT NULL,
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contact_addresses
-- 

CREATE TABLE contact_addresses (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  contact_id number(11) default 0 NOT NULL,
  address_number number(6) default 0 NOT NULL,
  address varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT contact_addresses UNIQUE (contact_id,address_number)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contact_notificationcommands
-- 
CREATE TABLE contact_notificationcommands (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  contact_id number(11) default 0 NOT NULL,
  notification_type number(6) default 0 NOT NULL,
  command_object_id number(11) default 0 NOT NULL,
  command_args varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT contact_notificationcommands UNIQUE (contact_id,notification_type,command_object_id,command_args)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contactgroup_members
-- 

CREATE TABLE contactgroup_members (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  contactgroup_id number(11) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT contactgroup_members UNIQUE (contactgroup_id,contact_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contactgroups
-- 

CREATE TABLE contactgroups (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  contactgroup_object_id number(11) default 0 NOT NULL,
  alias varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT contactgroups UNIQUE (instance_id,config_type,contactgroup_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contactnotificationmethods
-- 

CREATE TABLE contactnotificationmethods (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  contactnotification_id number(11) default 0 NOT NULL,
  start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  start_time_usec number(11) default 0 NOT NULL,
  end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  end_time_usec number(11) default 0 NOT NULL,
  command_object_id number(11) default 0 NOT NULL,
  command_args varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT contactnotificationmethods UNIQUE (instance_id,contactnotification_id,start_time,start_time_usec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contactnotifications
-- 

CREATE TABLE contactnotifications (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  notification_id number(11) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  start_time_usec number(11) default 0 NOT NULL,
  end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  end_time_usec number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT contactnotifications UNIQUE (instance_id,contact_object_id,start_time,start_time_usec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contacts
-- 

CREATE TABLE contacts (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  alias varchar2(64),
  email_address varchar2(255),
  pager_address varchar2(64),
  host_timeperiod_object_id number(11) default 0 NOT NULL,
  service_timeperiod_object_id number(11) default 0 NOT NULL,
  host_notifications_enabled number(6) default 0 NOT NULL,
  service_notifications_enabled number(6) default 0 NOT NULL,
  can_submit_commands number(6) default 0 NOT NULL,
  notify_service_recovery number(6) default 0 NOT NULL,
  notify_service_warning number(6) default 0 NOT NULL,
  notify_service_unknown number(6) default 0 NOT NULL,
  notify_service_critical number(6) default 0 NOT NULL,
  notify_service_flapping number(6) default 0 NOT NULL,
  notify_service_downtime number(6) default 0 NOT NULL,
  notify_host_recovery number(6) default 0 NOT NULL,
  notify_host_down number(6) default 0 NOT NULL,
  notify_host_unreachable number(6) default 0 NOT NULL,
  notify_host_flapping number(6) default 0 NOT NULL,
  notify_host_downtime number(6) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT contacts UNIQUE (instance_id,config_type,contact_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table contactstatus
-- 

CREATE TABLE contactstatus (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  status_update_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  host_notifications_enabled number(6) default 0 NOT NULL,
  service_notifications_enabled number(6) default 0 NOT NULL,
  last_host_notification date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_service_notification date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  modified_attributes number(11) default 0 NOT NULL,
  modified_host_attributes number(11) default 0 NOT NULL,
  modified_service_attributes number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT contactstatus UNIQUE (contact_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table customvariables
-- 

CREATE TABLE customvariables (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  has_been_modified number(6) default 0 NOT NULL,
  varname varchar2(255),
  varvalue varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT customvariables UNIQUE (object_id,config_type,varname)
);
CREATE INDEX customvariables_i ON customvariables(varname);

-- --------------------------------------------------------

-- 
-- Table structure for table customvariablestatus
-- 

CREATE TABLE customvariablestatus (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  status_update_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  has_been_modified number(6) default 0 NOT NULL,
  varname varchar2(255),
  varvalue varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT customvariablestatus UNIQUE (object_id,varname)
);
CREATE INDEX customvariablestatus_i ON customvariablestatus(varname);

-- --------------------------------------------------------

-- 
-- Table structure for table dbversion
-- 

CREATE TABLE dbversion (
  name varchar2(10),
  version varchar2(10)
);

-- --------------------------------------------------------

-- 
-- Table structure for table downtimehistory
-- 

CREATE TABLE downtimehistory (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  downtime_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  entry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  author_name varchar2(64),
  comment_data varchar2(1024),
  internal_downtime_id number(11) default 0 NOT NULL,
  triggered_by_id number(11) default 0 NOT NULL,
  is_fixed number(6) default 0 NOT NULL,
  duration number(6) default 0 NOT NULL,
  scheduled_start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  scheduled_end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  was_started number(6) default 0 NOT NULL,
  actual_start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  actual_start_time_usec number(11) default 0 NOT NULL,
  actual_end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  actual_end_time_usec number(11) default 0 NOT NULL,
  was_cancelled number(6) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT downtimehistory UNIQUE (instance_id,object_id,entry_time,internal_downtime_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table eventhandlers
-- 

CREATE TABLE eventhandlers (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  eventhandler_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  state number(6) default 0 NOT NULL,
  state_type number(6) default 0 NOT NULL,
  start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  start_time_usec number(11) default 0 NOT NULL,
  end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  end_time_usec number(11) default 0 NOT NULL,
  command_object_id number(11) default 0 NOT NULL,
  command_args varchar2(255),
  command_line varchar2(255),
  timeout number(6) default 0 NOT NULL,
  early_timeout number(6) default 0 NOT NULL,
  execution_time number default 0 NOT NULL,
  return_code number(6) default 0 NOT NULL,
  output varchar2(1024),
  PRIMARY KEY  (id),
  CONSTRAINT eventhandlers UNIQUE (instance_id,object_id,start_time,start_time_usec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table externalcommands
-- 

CREATE TABLE externalcommands (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  entry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  command_type number(6) default 0 NOT NULL,
  command_name varchar2(128),
  command_args varchar2(255),
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table flappinghistory
-- 

CREATE TABLE flappinghistory (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  event_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  event_time_usec number(11) default 0 NOT NULL,
  event_type number(6) default 0 NOT NULL,
  reason_type number(6) default 0 NOT NULL,
  flapping_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  percent_state_change number default 0 NOT NULL,
  low_threshold number default 0 NOT NULL,
  high_threshold number default 0 NOT NULL,
  comment_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  internal_comment_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table host_contactgroups
-- 

CREATE TABLE host_contactgroups (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  host_id number(11) default 0 NOT NULL,
  contactgroup_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT host_contactgroups UNIQUE (host_id,contactgroup_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table host_contacts
-- 

CREATE TABLE host_contacts (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  host_id number(11) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT host_contacts UNIQUE (instance_id,host_id,contact_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table host_parenthosts
-- 

CREATE TABLE host_parenthosts (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  host_id number(11) default 0 NOT NULL,
  parent_host_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT host_parenthosts UNIQUE (host_id,parent_host_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hostchecks
-- 

CREATE TABLE hostchecks (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  host_object_id number(11) default 0 NOT NULL,
  check_type number(6) default 0 NOT NULL,
  is_raw_check number(6) default 0 NOT NULL,
  current_check_attempt number(6) default 0 NOT NULL,
  max_check_attempts number(6) default 0 NOT NULL,
  state number(6) default 0 NOT NULL,
  state_type number(6) default 0 NOT NULL,
  start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  start_time_usec number(11) default 0 NOT NULL,
  end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  end_time_usec number(11) default 0 NOT NULL,
  command_object_id number(11) default 0 NOT NULL,
  command_args varchar2(255),
  command_line varchar2(255),
  timeout number(6) default 0 NOT NULL,
  early_timeout number(6) default 0 NOT NULL,
  execution_time number default 0 NOT NULL,
  latency number default 0 NOT NULL,
  return_code number(6) default 0 NOT NULL,
  output varchar2(1024),
  long_output clob,
  perfdata varchar2(1024),
  PRIMARY KEY  (id),
  CONSTRAINT hostchecks UNIQUE (instance_id,host_object_id,start_time,start_time_usec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hostdependencies
-- 

CREATE TABLE hostdependencies (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  host_object_id number(11) default 0 NOT NULL,
  dependent_host_object_id number(11) default 0 NOT NULL,
  dependency_type number(6) default 0 NOT NULL,
  inherits_parent number(6) default 0 NOT NULL,
  timeperiod_object_id number(11) default 0 NOT NULL,
  fail_on_up number(6) default 0 NOT NULL,
  fail_on_down number(6) default 0 NOT NULL,
  fail_on_unreachable number(6) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT hostdependencies UNIQUE (instance_id,config_type,host_object_id,dependent_host_object_id,dependency_type,inherits_parent,fail_on_up,fail_on_down,fail_on_unreachable)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hostescalation_contactgroups
-- 

CREATE TABLE hostescalation_contactgroups (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  hostescalation_id number(11) default 0 NOT NULL,
  contactgroup_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT hostescalation_contactgroups UNIQUE (hostescalation_id,contactgroup_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hostescalation_contacts
-- 

CREATE TABLE hostescalation_contacts (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  hostescalation_id number(11) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT hostescalation_contacts UNIQUE (instance_id,hostescalation_id,contact_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hostescalations
-- 

CREATE TABLE hostescalations (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  host_object_id number(11) default 0 NOT NULL,
  timeperiod_object_id number(11) default 0 NOT NULL,
  first_notification number(6) default 0 NOT NULL,
  last_notification number(6) default 0 NOT NULL,
  notification_interval number default 0 NOT NULL,
  escalate_on_recovery number(6) default 0 NOT NULL,
  escalate_on_down number(6) default 0 NOT NULL,
  escalate_on_unreachable number(6) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT hostescalations UNIQUE (instance_id,config_type,host_object_id,timeperiod_object_id,first_notification,last_notification)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hostgroup_members
-- 

CREATE TABLE hostgroup_members (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  hostgroup_id number(11) default 0 NOT NULL,
  host_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT hostgroup_members UNIQUE (hostgroup_id,host_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hostgroups
-- 

CREATE TABLE hostgroups (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  hostgroup_object_id number(11) default 0 NOT NULL,
  alias varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT hostgroups UNIQUE (instance_id,hostgroup_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hosts
-- 

CREATE TABLE hosts (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  host_object_id number(11) default 0 NOT NULL,
  alias varchar2(255),
  display_name varchar2(255),
  address varchar2(128),
  check_command_object_id number(11) default 0 NOT NULL,
  check_command_args varchar2(255),
  eventhandler_command_object_id number(11) default 0 NOT NULL,
  eventhandler_command_args varchar2(255),
  notif_timeperiod_object_id number(11) default 0 NOT NULL, 
  check_timeperiod_object_id number(11) default 0 NOT NULL,
  failure_prediction_options varchar2(64),
  check_interval number default 0 NOT NULL,
  retry_interval number default 0 NOT NULL,
  max_check_attempts number(6) default 0 NOT NULL,
  first_notification_delay number default 0 NOT NULL,
  notification_interval number default 0 NOT NULL,
  notify_on_down number(6) default 0 NOT NULL,
  notify_on_unreachable number(6) default 0 NOT NULL,
  notify_on_recovery number(6) default 0 NOT NULL,
  notify_on_flapping number(6) default 0 NOT NULL,
  notify_on_downtime number(6) default 0 NOT NULL,
  stalk_on_up number(6) default 0 NOT NULL,
  stalk_on_down number(6) default 0 NOT NULL,
  stalk_on_unreachable number(6) default 0 NOT NULL,
  flap_detection_enabled number(6) default 0 NOT NULL,
  flap_detection_on_up number(6) default 0 NOT NULL,
  flap_detection_on_down number(6) default 0 NOT NULL,
  flap_detection_on_unreachable number(6) default 0 NOT NULL,
  low_flap_threshold number default 0 NOT NULL,
  high_flap_threshold number default 0 NOT NULL,
  process_performance_data number(6) default 0 NOT NULL,
  freshness_checks_enabled number(6) default 0 NOT NULL,
  freshness_threshold number(6) default 0 NOT NULL,
  passive_checks_enabled number(6) default 0 NOT NULL,
  event_handler_enabled number(6) default 0 NOT NULL,
  active_checks_enabled number(6) default 0 NOT NULL,
  retain_status_information number(6) default 0 NOT NULL,
  retain_nonstatus_information number(6) default 0 NOT NULL,
  notifications_enabled number(6) default 0 NOT NULL,
  obsess_over_host number(6) default 0 NOT NULL,
  failure_prediction_enabled number(6) default 0 NOT NULL,
  notes varchar2(255),
  notes_url varchar2(255),
  action_url varchar2(255),
  icon_image varchar2(255),
  icon_image_alt varchar2(255),
  vrml_image varchar2(255),
  statusmap_image varchar2(255),
  have_2d_coords number(6) default 0 NOT NULL,
  x_2d number(6) default 0 NOT NULL,
  y_2d number(6) default 0 NOT NULL,
  have_3d_coords number(6) default 0 NOT NULL,
  x_3d number default 0 NOT NULL,
  y_3d number default 0 NOT NULL,
  z_3d number default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT hosts UNIQUE (instance_id,config_type,host_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table hoststatus
-- 

CREATE TABLE hoststatus (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  host_object_id number(11) default 0 NOT NULL,
  status_update_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  output varchar2(1024),
  long_output clob,
  perfdata varchar2(1024),
  current_state number(6) default 0 NOT NULL,
  has_been_checked number(6) default 0 NOT NULL,
  should_be_scheduled number(6) default 0 NOT NULL,
  current_check_attempt number(6) default 0 NOT NULL,
  max_check_attempts number(6) default 0 NOT NULL,
  last_check date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  next_check date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  check_type number(6) default 0 NOT NULL,
  last_state_change date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_hard_state_change date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_hard_state number(6) default 0 NOT NULL,
  last_time_up date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_time_down date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_time_unreachable date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  state_type number(6) default 0 NOT NULL,
  last_notification date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  next_notification date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  no_more_notifications number(6) default 0 NOT NULL,
  notifications_enabled number(6) default 0 NOT NULL,
  problem_has_been_acknowledged number(6) default 0 NOT NULL,
  acknowledgement_type number(6) default 0 NOT NULL,
  current_notification_number number(6) default 0 NOT NULL,
  passive_checks_enabled number(6) default 0 NOT NULL,
  active_checks_enabled number(6) default 0 NOT NULL,
  event_handler_enabled number(6) default 0 NOT NULL,
  flap_detection_enabled number(6) default 0 NOT NULL,
  is_flapping number(6) default 0 NOT NULL,
  percent_state_change number default 0 NOT NULL,
  latency number default 0 NOT NULL,
  execution_time number default 0 NOT NULL,
  scheduled_downtime_depth number(6) default 0 NOT NULL,
  failure_prediction_enabled number(6) default 0 NOT NULL,
  process_performance_data number(6) default 0 NOT NULL,
  obsess_over_host number(6) default 0 NOT NULL,
  modified_host_attributes number(11) default 0 NOT NULL,
  event_handler varchar2(255),
  check_command varchar2(255),
  normal_check_interval number default 0 NOT NULL,
  retry_check_interval number default 0 NOT NULL,
  check_timeperiod_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT hoststatus UNIQUE (host_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table instances
-- 

CREATE TABLE instances (
  id number(11) NOT NULL,
  instance_name varchar2(64),
  instance_description varchar2(128),
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table logentries
-- 

CREATE TABLE logentries (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  logentry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  entry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  entry_time_usec number(11) default 0 NOT NULL,
  logentry_type number(11) default 0 NOT NULL,
  logentry_data varchar2(1024),
  realtime_data number(6) default 0 NOT NULL,
  inferred_data_extracted number(6) default 0 NOT NULL,
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table notifications
-- 

CREATE TABLE notifications (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  notification_type number(6) default 0 NOT NULL,
  notification_reason number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  start_time_usec number(11) default 0 NOT NULL,
  end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  end_time_usec number(11) default 0 NOT NULL,
  state number(6) default 0 NOT NULL,
  output varchar2(1024),
  long_output clob,
  escalated number(6) default 0 NOT NULL,
  contacts_notified number(6) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT notifications UNIQUE (instance_id,object_id,start_time,start_time_usec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table objects
-- 

CREATE TABLE objects (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  objecttype_id number(6) default 0 NOT NULL,
  name1 varchar2(128),
  name2 varchar2(128),
  is_active number(6) default 0 NOT NULL,
  PRIMARY KEY  (id)
);
CREATE INDEX objects_i ON objects(objecttype_id,name1,name2);

-- --------------------------------------------------------

-- 
-- Table structure for table processevents
-- 

CREATE TABLE processevents (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  event_type number(6) default 0 NOT NULL,
  event_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  event_time_usec number(11) default 0 NOT NULL,
  process_id number(11) default 0 NOT NULL,
  program_name varchar2(16),
  program_version varchar2(20),
  program_date varchar2(10),
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table programstatus
-- 

CREATE TABLE programstatus (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  status_update_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  program_start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  program_end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  is_currently_running number(6) default 0 NOT NULL,
  process_id number(11) default 0 NOT NULL,
  daemon_mode number(6) default 0 NOT NULL,
  last_command_check date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_log_rotation date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  notifications_enabled number(6) default 0 NOT NULL,
  active_service_checks_enabled number(6) default 0 NOT NULL,
  passive_service_checks_enabled number(6) default 0 NOT NULL,
  active_host_checks_enabled number(6) default 0 NOT NULL,
  passive_host_checks_enabled number(6) default 0 NOT NULL,
  event_handlers_enabled number(6) default 0 NOT NULL,
  flap_detection_enabled number(6) default 0 NOT NULL,
  failure_prediction_enabled number(6) default 0 NOT NULL,
  process_performance_data number(6) default 0 NOT NULL,
  obsess_over_hosts number(6) default 0 NOT NULL,
  obsess_over_services number(6) default 0 NOT NULL,
  modified_host_attributes number(11) default 0 NOT NULL,
  modified_service_attributes number(11) default 0 NOT NULL,
  global_host_event_handler varchar2(255),
  global_service_event_handler varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT programstatus UNIQUE (instance_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table runtimevariables
-- 

CREATE TABLE runtimevariables (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  varname varchar2(64),
  varvalue varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT runtimevariables UNIQUE (instance_id,varname)
);

-- --------------------------------------------------------

-- 
-- Table structure for table scheduleddowntime
-- 

CREATE TABLE scheduleddowntime (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  downtime_type number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  entry_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  author_name varchar2(64),
  comment_data varchar2(1024),
  internal_downtime_id number(11) default 0 NOT NULL,
  triggered_by_id number(11) default 0 NOT NULL,
  is_fixed number(6) default 0 NOT NULL,
  duration number(6) default 0 NOT NULL,
  scheduled_start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  scheduled_end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  was_started number(6) default 0 NOT NULL,
  actual_start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  actual_start_time_usec number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT scheduleddowntime UNIQUE (instance_id,object_id,entry_time,internal_downtime_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table service_contactgroups
-- 

CREATE TABLE service_contactgroups (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  service_id number(11) default 0 NOT NULL,
  contactgroup_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT service_contactgroups UNIQUE (service_id,contactgroup_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table service_contacts
-- 

CREATE TABLE service_contacts (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  service_id number(11) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT service_contacts UNIQUE (instance_id,service_id,contact_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table servicechecks
-- 

CREATE TABLE servicechecks (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  service_object_id number(11) default 0 NOT NULL,
  check_type number(6) default 0 NOT NULL,
  current_check_attempt number(6) default 0 NOT NULL,
  max_check_attempts number(6) default 0 NOT NULL,
  state number(6) default 0 NOT NULL,
  state_type number(6) default 0 NOT NULL,
  start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  start_time_usec number(11) default 0 NOT NULL,
  end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  end_time_usec number(11) default 0 NOT NULL,
  command_object_id number(11) default 0 NOT NULL,
  command_args varchar2(255),
  command_line varchar2(255),
  timeout number(6) default 0 NOT NULL,
  early_timeout number(6) default 0 NOT NULL,
  execution_time number default 0 NOT NULL,
  latency number default 0 NOT NULL,
  return_code number(6) default 0 NOT NULL,
  output varchar2(1024),
  long_output clob,
  perfdata varchar2(1024),
  PRIMARY KEY  (id),
  CONSTRAINT servicechecks UNIQUE (instance_id,service_object_id,start_time,start_time_usec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table servicedependencies
-- 

CREATE TABLE servicedependencies (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  service_object_id number(11) default 0 NOT NULL,
  dependent_service_object_id number(11) default 0 NOT NULL,
  dependency_type number(6) default 0 NOT NULL,
  inherits_parent number(6) default 0 NOT NULL,
  timeperiod_object_id number(11) default 0 NOT NULL,
  fail_on_ok number(6) default 0 NOT NULL,
  fail_on_warning number(6) default 0 NOT NULL,
  fail_on_unknown number(6) default 0 NOT NULL,
  fail_on_critical number(6) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT servicedependencies UNIQUE (instance_id,config_type,service_object_id,dependent_service_object_id,dependency_type,inherits_parent,fail_on_ok,fail_on_warning,fail_on_unknown,fail_on_critical)
);

-- --------------------------------------------------------

-- 
-- Table structure for table serviceescalationcontactgroups
-- 

CREATE TABLE serviceescalationcontactgroups (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  serviceescalation_id number(11) default 0 NOT NULL,
  contactgroup_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT serviceescalationcontactgroups UNIQUE (serviceescalation_id,contactgroup_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table serviceescalation_contacts
-- 

CREATE TABLE serviceescalation_contacts (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  serviceescalation_id number(11) default 0 NOT NULL,
  contact_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT serviceescalation_contacts UNIQUE (instance_id,serviceescalation_id,contact_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table serviceescalations
-- 

CREATE TABLE serviceescalations (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  service_object_id number(11) default 0 NOT NULL,
  timeperiod_object_id number(11) default 0 NOT NULL,
  first_notification number(6) default 0 NOT NULL,
  last_notification number(6) default 0 NOT NULL,
  notification_interval number default 0 NOT NULL,
  escalate_on_recovery number(6) default 0 NOT NULL,
  escalate_on_warning number(6) default 0 NOT NULL,
  escalate_on_unknown number(6) default 0 NOT NULL,
  escalate_on_critical number(6) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT serviceescalations UNIQUE (instance_id,config_type,service_object_id,timeperiod_object_id,first_notification,last_notification)
);

-- --------------------------------------------------------

-- 
-- Table structure for table servicegroup_members
-- 

CREATE TABLE servicegroup_members (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  servicegroup_id number(11) default 0 NOT NULL,
  service_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT servicegroup_members UNIQUE (servicegroup_id,service_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table servicegroups
-- 

CREATE TABLE servicegroups (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  servicegroup_object_id number(11) default 0 NOT NULL,
  alias varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT servicegroups UNIQUE (instance_id,config_type,servicegroup_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table services
-- 

CREATE TABLE services (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  host_object_id number(11) default 0 NOT NULL,
  service_object_id number(11) default 0 NOT NULL,
  display_name varchar2(64),
  check_command_object_id number(11) default 0 NOT NULL,
  check_command_args varchar2(255),
  eventhandler_command_object_id number(11) default 0 NOT NULL,
  eventhandler_command_args varchar2(255),
  notif_timeperiod_object_id number(11) default 0 NOT NULL,
  check_timeperiod_object_id number(11) default 0 NOT NULL,
  failure_prediction_options varchar2(64),
  check_interval number default 0 NOT NULL,
  retry_interval number default 0 NOT NULL,
  max_check_attempts number(6) default 0 NOT NULL,
  first_notification_delay number default 0 NOT NULL,
  notification_interval number default 0 NOT NULL,
  notify_on_warning number(6) default 0 NOT NULL,
  notify_on_unknown number(6) default 0 NOT NULL,
  notify_on_critical number(6) default 0 NOT NULL,
  notify_on_recovery number(6) default 0 NOT NULL,
  notify_on_flapping number(6) default 0 NOT NULL,
  notify_on_downtime number(6) default 0 NOT NULL,
  stalk_on_ok number(6) default 0 NOT NULL,
  stalk_on_warning number(6) default 0 NOT NULL,
  stalk_on_unknown number(6) default 0 NOT NULL,
  stalk_on_critical number(6) default 0 NOT NULL,
  is_volatile number(6) default 0 NOT NULL,
  flap_detection_enabled number(6) default 0 NOT NULL,
  flap_detection_on_ok number(6) default 0 NOT NULL,
  flap_detection_on_warning number(6) default 0 NOT NULL,
  flap_detection_on_unknown number(6) default 0 NOT NULL,
  flap_detection_on_critical number(6) default 0 NOT NULL,
  low_flap_threshold number default 0 NOT NULL,
  high_flap_threshold number default 0 NOT NULL,
  process_performance_data number(6) default 0 NOT NULL,
  freshness_checks_enabled number(6) default 0 NOT NULL,
  freshness_threshold number(6) default 0 NOT NULL,
  passive_checks_enabled number(6) default 0 NOT NULL,
  event_handler_enabled number(6) default 0 NOT NULL,
  active_checks_enabled number(6) default 0 NOT NULL,
  retain_status_information number(6) default 0 NOT NULL,
  retain_nonstatus_information number(6) default 0 NOT NULL,
  notifications_enabled number(6) default 0 NOT NULL,
  obsess_over_service number(6) default 0 NOT NULL,
  failure_prediction_enabled number(6) default 0 NOT NULL,
  notes varchar2(255),
  notes_url varchar2(255),
  action_url varchar2(255),
  icon_image varchar2(255),
  icon_image_alt varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT services UNIQUE (instance_id,config_type,service_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table servicestatus
-- 

CREATE TABLE servicestatus (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  service_object_id number(11) default 0 NOT NULL,
  status_update_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  output varchar2(1024),
  long_output clob,
  perfdata varchar2(1024),
  current_state number(6) default 0 NOT NULL,
  has_been_checked number(6) default 0 NOT NULL,
  should_be_scheduled number(6) default 0 NOT NULL,
  current_check_attempt number(6) default 0 NOT NULL,
  max_check_attempts number(6) default 0 NOT NULL,
  last_check date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  next_check date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  check_type number(6) default 0 NOT NULL,
  last_state_change date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_hard_state_change date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_hard_state number(6) default 0 NOT NULL,
  last_time_ok date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_time_warning date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_time_unknown date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  last_time_critical date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  state_type number(6) default 0 NOT NULL,
  last_notification date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  next_notification date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  no_more_notifications number(6) default 0 NOT NULL,
  notifications_enabled number(6) default 0 NOT NULL,
  problem_has_been_acknowledged number(6) default 0 NOT NULL,
  acknowledgement_type number(6) default 0 NOT NULL,
  current_notification_number number(6) default 0 NOT NULL,
  passive_checks_enabled number(6) default 0 NOT NULL,
  active_checks_enabled number(6) default 0 NOT NULL,
  event_handler_enabled number(6) default 0 NOT NULL,
  flap_detection_enabled number(6) default 0 NOT NULL,
  is_flapping number(6) default 0 NOT NULL,
  percent_state_change number default 0 NOT NULL,
  latency number default 0 NOT NULL,
  execution_time number default 0 NOT NULL,
  scheduled_downtime_depth number(6) default 0 NOT NULL,
  failure_prediction_enabled number(6) default 0 NOT NULL,
  process_performance_data number(6) default 0 NOT NULL,
  obsess_over_service number(6) default 0 NOT NULL,
  modified_service_attributes number(11) default 0 NOT NULL,
  event_handler varchar2(255),
  check_command varchar2(255),
  normal_check_interval number default 0 NOT NULL,
  retry_check_interval number default 0 NOT NULL,
  check_timeperiod_object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT servicestatus UNIQUE (service_object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table statehistory
-- 

CREATE TABLE statehistory (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  state_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  state_time_usec number(11) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  state_change number(6) default 0 NOT NULL,
  state number(6) default 0 NOT NULL,
  state_type number(6) default 0 NOT NULL,
  current_check_attempt number(6) default 0 NOT NULL,
  max_check_attempts number(6) default 0 NOT NULL,
  last_state number(6) default -1 NOT NULL,
  last_hard_state number(6) default -1 NOT NULL,
  output varchar2(1024),
  long_output clob,
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table systemcommands
-- 

CREATE TABLE systemcommands (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  start_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  start_time_usec number(11) default 0 NOT NULL,
  end_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  end_time_usec number(11) default 0 NOT NULL,
  command_line varchar2(255),
  timeout number(6) default 0 NOT NULL,
  early_timeout number(6) default 0 NOT NULL,
  execution_time number default 0 NOT NULL,
  return_code number(6) default 0 NOT NULL,
  output varchar2(1024),
  long_output clob,
  PRIMARY KEY  (id),
  CONSTRAINT systemcommands UNIQUE (instance_id,start_time,start_time_usec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table timedeventqueue
-- 

CREATE TABLE timedeventqueue (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  event_type number(6) default 0 NOT NULL,
  queued_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  queued_time_usec number(11) default 0 NOT NULL,
  scheduled_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  recurring_event number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  PRIMARY KEY  (id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table timedevents
-- 

CREATE TABLE timedevents (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  event_type number(6) default 0 NOT NULL,
  queued_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  queued_time_usec number(11) default 0 NOT NULL,
  event_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  event_time_usec number(11) default 0 NOT NULL,
  scheduled_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  recurring_event number(6) default 0 NOT NULL,
  object_id number(11) default 0 NOT NULL,
  deletion_time date default TO_DATE('1970-01-01 00:00:00','YYYY-MM-DD HH24:MI:SS') NOT NULL,
  deletion_time_usec number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT timedevents UNIQUE (instance_id,event_type,scheduled_time,object_id)
);

-- --------------------------------------------------------

-- 
-- Table structure for table timeperiod_timeranges
-- 

CREATE TABLE timeperiod_timeranges (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  timeperiod_id number(11) default 0 NOT NULL,
  day number(6) default 0 NOT NULL,
  start_sec number(11) default 0 NOT NULL,
  end_sec number(11) default 0 NOT NULL,
  PRIMARY KEY  (id),
  CONSTRAINT timeperiod_timeranges UNIQUE (timeperiod_id,day,start_sec,end_sec)
);

-- --------------------------------------------------------

-- 
-- Table structure for table timeperiods
-- 

CREATE TABLE timeperiods (
  id number(11) NOT NULL,
  instance_id number(11) default 0 NOT NULL,
  config_type number(6) default 0 NOT NULL,
  timeperiod_object_id number(11) default 0 NOT NULL,
  alias varchar2(255),
  PRIMARY KEY  (id),
  CONSTRAINT timeperiods UNIQUE (instance_id,config_type,timeperiod_object_id)
);

CREATE SEQUENCE autoincrement
   start with 1
   increment by 1
   nomaxvalue;

CREATE TRIGGER acknowledgements
   before insert on acknowledgements
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER commands
   before insert on commands
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER commenthistory
   before insert on commenthistory
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER comments
   before insert on comments
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER configfiles
   before insert on configfiles
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER configfilevariables
   before insert on configfilevariables
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER conninfo
   before insert on conninfo
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contact_addresses
   before insert on contact_addresses
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contact_notificationcommands
   before insert on contact_notificationcommands
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contactgroup_members
   before insert on contactgroup_members
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contactgroups
   before insert on contactgroups
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contactnotificationmethods
   before insert on contactnotificationmethods
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contactnotifications
   before insert on contactnotifications
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contacts
   before insert on contacts
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER contactstatus
   before insert on contactstatus
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER customvariables
   before insert on customvariables
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER customvariablestatus
   before insert on customvariablestatus
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

--CREATE TRIGGER dbversion
--   before insert on dbversion
--   for each row
--   begin
--   select autoincrement.nextval into :new.id from dual;
--   end;
--/

CREATE TRIGGER downtimehistory
   before insert on downtimehistory
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER eventhandlers
   before insert on eventhandlers
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER externalcommands
   before insert on externalcommands
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER flappinghistory
   before insert on flappinghistory
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER host_contactgroups
   before insert on host_contactgroups
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER host_contacts
   before insert on host_contacts
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER host_parenthosts
   before insert on host_parenthosts
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hostchecks
   before insert on hostchecks
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hostdependencies
   before insert on hostdependencies
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hostescalation_contactgroups
   before insert on hostescalation_contactgroups
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hostescalation_contacts
   before insert on hostescalation_contacts
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hostescalations
   before insert on hostescalations
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hostgroup_members
   before insert on hostgroup_members
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hostgroups
   before insert on hostgroups
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hosts
   before insert on hosts
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER hoststatus
   before insert on hoststatus
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER instances
   before insert on instances
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER logentries
   before insert on logentries
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER notifications
   before insert on notifications
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER objects
   before insert on objects
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER processevents
   before insert on processevents
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER programstatus
   before insert on programstatus
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER runtimevariables
   before insert on runtimevariables
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER scheduleddowntime
   before insert on scheduleddowntime
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER service_contactgroups
   before insert on service_contactgroups
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER service_contacts
   before insert on service_contacts
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER servicechecks
   before insert on servicechecks
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER servicedependencies
   before insert on servicedependencies
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER serviceescalationcontactgroups
   before insert on serviceescalationcontactgroups
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER serviceescalation_contacts
   before insert on serviceescalation_contacts
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER serviceescalations
   before insert on serviceescalations
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER servicegroup_members
   before insert on servicegroup_members
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER servicegroups
   before insert on servicegroups
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER services
   before insert on services
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER servicestatus
   before insert on servicestatus
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER statehistory
   before insert on statehistory
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER systemcommands
   before insert on systemcommands
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER timedeventqueue
   before insert on timedeventqueue
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER timedevents
   before insert on timedevents
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER timeperiod_timeranges
   before insert on timeperiod_timeranges
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/

CREATE TRIGGER timeperiods
   before insert on timeperiods
   for each row
   begin
   select autoincrement.nextval into :new.id from dual;
   end;
/
