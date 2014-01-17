.. _install_script:



Review of script's option and parameters
========================================

.. important::  It's recommended to use option one by one! Some options have a parsing trick that prevent from being mixed with other. Call the install script as much as you need is better.

Here are the options for the install script : 

======================== ================================================================================================================================
``-k | --kill``          Kill shinken
``-i | --install``       Install shinken
``-u | --uninstall``     Remove shinken and all of the addons. if an argument is specified then just remove the specified argument
``-b | --backup``        Backup shinken configuration plugins and data
``-r | --restore``       Restore shinken configuration plugins and data
``-l | --listbackups``   List shinken backups
``-c | --compresslogs``  Compress rotated logs
``-e | --enabledaemons`` Which daemons to keep enabled at boot time. It's a quoted list of shinken daemons that should be enabled at startup. Daemons are:
                         * arbiter
                         * scheduler
                         * poller
                         * broker
                         * reactionner
                         * receiver
                         * skonf
``-p | --plugin``        Install plugins. Argument should be one of the following:
                         * check_esx3
                         * nagios-plugins
                         * check_oracle_health
                         * check_mysql_health
                         * capture_plugin
                         * check_wmi_plus
                         * check_mongodb
                         * check_emc_clariion
                         * check_nwc_health
                         * manubulon (snmp plugins)
                         * check_hpasm
                         * check_netapp2
                         * check_mem (local enhanced memory check plugin)
                         * check_snmp_bandwidth (check bandwidth usage with snmp)
                         * check_netint (enhanced version of check_snmp_int plugins)
                         * check_IBM
                         * check_IBM_DS
                         * check_HPUX
                         * check_rsync
``-a | --addon``         Install addons. Argument should be one of the following:
                         * pnp4nagios
                         * multisite
                         * nagvis
                         * mongodb
                         * nconf (experimental)
                         * notify_by_xmpp
``--nconf-import-packs`` Import shinken packs into nconf (experimental). This require nconf to be installed
``--register``           Register on community (experimental)
``--enableeue``          Enable application performance monitoring stack (experimental)
``-h | --help``          Show help
======================== ================================================================================================================================


Review of variable used in the script
=====================================


The following variables can bet set before running the script in order to modify its behavior.

====================== ===========================================================================================================================================
Unordered List ItemTMP Specify the temp folder for Shinken installation. Default : /tmp
LOGFILE                Specify the logs file used during Shinken installation. Default : $TMP/shinken.install.log"
USEPROXY               Specify if the server is behind a proxy. Used during installing prerequisites. Default : 0 (No)
SKIPPREREQUISITES      Specify if the script check and install Shinken prerequisites. All prerequisites are not compulsory for a "small" install  Default : 0 (No)
TARGET                 Specify the target directory for Shinken installation. Default : /usr/local/shinken
ETC                    Specify the etc directory for Shinken installation (configuration files directory). Default : $TARGET/etc 
LIBEXEC                Specify the libexec directory for Shinken installation (plugin directory). Default : $TARGET/libexec
VAR                    Specify the var directory for Shinken installation(logs directory). Default : $TARGET/var
BACKUPDIR              Specify the backup directory. Default : /opt/backup
SKUSER                 Specify the Shinken user. Default : shinken
SKGROUP                Specify the Shinken group. Default : shinken
MANAGEPYRO             Specify if the script will install a "managed" version of Pyro (Pyro4 lib) Defaukt : 0 (No)
KEEPDAYSLOG            Specify the number of days to keep the logs (for Sqlite purge). Default : 7
RETENTIONMODULE        Specify the default retention module (pickle|mongodb). Default pickle
====================== ===========================================================================================================================================
