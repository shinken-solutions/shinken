.. _troubleshooting_shinken:



==============================
FAQ - Shinken troubleshooting 
==============================




FAQ Summary
============


Shinken users, developers, administrators possess a body of knowledge that usually provides a quick path to problem resolutions. The Frequently Asked Questions questions are compiled from user questions and issues developers may run into.

Have you consulted at all the :ref:`resources available for users and developers <how_to_contribute>`.

**__Before posting a question to the forum:__**
   * Read the through the  :ref:`Getting Started tutorials <gettingstarted-index>`
   * Search the documentation wiki
   * Use this FAQ
   * Bonus: Update this FAQ if you found the answer and think it would benefit someone else

Doing this will improve the quality of the answers and your own expertise.



Frequently asked questions 
---------------------------


  - :ref:`How to set my daemons in debug mode to review the logs? <Review the daemon logs>`
  - :ref:`I am getting an OSError read-only filesystem OSError read-only filesystem error>`
  - :ref:`I am getting an OSError [Errno 24] Too many open files <OSError too many files open>`
  - :ref:`Notification emails have generic-host instead of host_name <Notification emails have generic-host instead of host_name>`
  - :ref:`Thruk/Multisite reporting doesn't work using Shinken 1.2 <Reporting does not work with Shinken 1.2>`



General Shinken troubleshooting steps to resolve common issue
---------------------------------------------------------------

  - Have you mixed installation methods! :ref:`Cleanup and install using a single method <shinken_installation>`.
  - Have you installed the :ref:`check scripts and addon software <shinken_installation>`
  - Is Shinken even running?
  - Have you checked the :ref:`Shinken pre-requisites <prerequisites_1_2>`?
  - Have you :ref:`configured the WebUI module <use_with_webui>` in your shinken-specific.cfg file
  - Have you :ref:`completed the Shinken basic configuration <configure_shinken>` and :ref:`Shinken WebUI configuration <use_with_webui>`
  - Have you reviewed your Shinken centralized (:ref:`Simple-log broker module <the_broker_modules>`) logs for errors
  - Have you reviewed your :ref:`Shinken daemon specific logs <troubleshooting_shinken#Review the daemon logs>` for errors or tracebacks (what the system was doing just before a crash)
  - Have you reviewed your :ref:`configuration syntax <configuringshinken-config>` (keywords and values)
  - Is what you are trying to use installed? Are its dependancies installed! Does it even work.
  - Is what you are trying to use :ref:`a supported version <shinken_installation_requirements>`?
  - Are you using the same Python version on all your hosts running a Shinken daemon (You have to!)
  - Have you installed Shinken with the SAME prefix (ex: /usr/local) on all your hosts running a Shinken daemon (You have to!)
  - Have you enabled debugging logs on your daemon(s)
  - Problem with Livestatus, did it start, is it listening on the exppected TCP port, have you enabled and configured the module in shinken-specific.cfg.
  - Have you installed the check scripts as the shinken user and not as root
  - Have you executed/tested your command as the shinken user
  - Have you manually generated check results
  - Can you connect to your remote agent NRPE, NSClient++, etc. 
  - Have you defined a module on the wrong daemon (ex. NSCA receiver module on a Broker)
  - Have you created a diagram illustrating your templates and inheritance
  - System logs (/var/messages, windows event log)
  - Application logs (MongoDB, SQLite, Apache, etc)
  - Security logs (Filters, Firewalls operational logs)
  - Use top or Microsoft Task manager or process monitor (Microsoft sysinternals tools) to look for memory, cpu and process issues.
  - Use nagiostat to check latency and other core related metrics.
  - Is your check command timeout too long
  - Have you looked at your Graphite Carbon metrics
  - Can you connect to the Graphite web interface
  - Are there gaps in your data
  - Have you configured your storage schema (retention interval and aggregation rules) for Graphite collected data.
  - Are you sending data more often than what is expected by your storage schema.
  - Storing data to the Graphite databases, are you using the correct IP, port and protocol, are both modules enabled; Graphite_UI and graphite export.



FAQ Answers 
============




Review the daemon logs 
-----------------------


A daemon is a Shinken process. Each daemon generates a log file by default. If you need to learn more about what is what, go back to :ref:`the shinken architecture <the_shinken_architecture>`.
The configuration of a daemon is set in the .ini configuration file(ex. brokerd.ini).
Logging is enabled and set to level INFO by default.

Default log file location ''local_log=%(workdir)s/schedulerd.log''

The log file will contain information on the Shinken process and any problems the daemon encounters.



Changing the log level during runtime 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


shinken-admin is a command line script that can change the logging level of a running daemon.

''linux-server# ./shinken-admin ...''



Changing the log level in the configuration 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Edit the <daemon-name>.ini file, where daemon name is pollerd, schedulerd, arbiterd, reactionnerd, receiverd.
Set the log level to: DEBUG 
Possible values: DEBUG,INFO,WARNING,ERROR,CRITICAL

Re-start the Shinken process.


OSError read-only filesystem error  
------------------------------------


You poller daemon and reactionner daemons are not starting and you get a traceback for an OSError in your logs.

''OSError [30] read-only filesystem''

Execute a 'mount' and verify if /tmp or /tmpfs is set to 'ro' (Read-only).
As root modify your /etc/fstab to set the filesystem to read-write.



OSError too many files open  
-----------------------------


The operating system cannot open anymore files and generates an error. Shinken opens a lot of files during runtime, this is normal. Increase the limits.

Google: changing the max number of open files linux / debian / centos / RHEL

cat /proc/sys/fs/file-max

# su - shinken
$ ulimit -Hn
$ ulimit -Sn

This typically changing a system wide file limit and potentially user specific file limits. (ulimit, limits.conf, sysctl, sysctl.conf, cat /proc/sys/fs/file-max)

# To immediately apply changes
ulimit -n xxxxx now



Notification emails have generic-host instead of host_name 
-----------------------------------------------------------


Try defining host_alias, which is often the field used by the notification methods.

Why does Shinken use both host_alias and host_name. Flexibility and historicaly as Nagios did it this way.




