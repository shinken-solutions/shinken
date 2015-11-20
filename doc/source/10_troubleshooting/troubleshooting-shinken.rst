.. _troubleshooting/troubleshooting-shinken:

==============================
FAQ - Shinken troubleshooting 
==============================


FAQ Summary
============

Shinken users, developers, administrators possess a body of knowledge that usually provides a quick path to problem resolutions. The Frequently Asked Questions questions are compiled from user questions and issues developers may run into.

Have you consulted at all the :ref:`resources available for users and developers <contributing/index>`.

**__Before posting a question to the forum:__**

  * Read the through the  :ref:`Getting Started tutorials <gettingstarted/index>`
  * Search the documentation wiki
  * Use this FAQ
  * Bonus: Update this FAQ if you found the answer and think it would benefit someone else

Doing this will improve the quality of the answers and your own expertise.


Frequently asked questions 
---------------------------

  * :ref:`How to set my daemons in debug mode to review the logs? <troubleshooting/troubleshooting-shinken#FAQ-1>`
  * :ref:`I am getting an OSError read-only filesystem <troubleshooting/troubleshooting-shinken#FAQ-3>`
  * :ref:`I am getting an OSError [Errno 24] Too many open files <troubleshooting/troubleshooting-shinken#FAQ-4>`
  * :ref:`Notification emails have generic-host instead of host_name <troubleshooting/troubleshooting-shinken#FAQ-5>`




General Shinken troubleshooting steps to resolve common issue
---------------------------------------------------------------

  * Have you mixed installation methods! :ref:`Cleanup and install using a single method <gettingstarted/installations/shinken-installation>`.
  * Have you installed the :ref:`check scripts and addon software <gettingstarted/installations/shinken-installation>`
  * Is Shinken even running?
  * Have you checked the :ref:`Shinken pre-requisites <gettingstarted/installations/shinken-installation#requirements>`?
  * Have you :ref:`configured the WebUI module <integration/webui>` in your brokers/broker-master.cfg file
  * Have you :ref:`completed the Shinken basic configuration <configuration/index>` and :ref:`Shinken WebUI configuration <integration/webui>`
  * Have you reviewed your Shinken centralized (:ref:`Simple-log broker module <the_broker_modules>`) logs for errors
  * Have you reviewed your :ref:`Shinken daemon specific logs <troubleshooting/troubleshooting-shinken#FAQ-1>` for errors or tracebacks (what the system was doing just before a crash)
  * Have you reviewed your :ref:`configuration syntax <configuration/config>` (keywords and values)
  * Is what you are trying to use installed? Are its dependencies installed! Does it even work.
  * Is what you are trying to use :ref:`a supported version <gettingstarted/installations/shinken-installation#requirements>`?
  * Are you using the same Python Pyro module version on all your hosts running a Shinken daemon (You have to!)
  * Are you using the same Python version on all your hosts running a Shinken daemon (You have to!)
  * Have you installed Shinken with the SAME prefix (ex: /usr/local) on all your hosts running a Shinken daemon (You have to!)
  * Have you enabled debugging logs on your daemon(s)
  * How to identify the source of a Pyro MemoryError
  * Problem with Livestatus, did it start, is it listening on the expected TCP port, have you enabled and configured the module in /etc/shinken/modules/livestatus.cfg.
  * Have you installed the check scripts as the shinken user and not as root
  * Have you executed/tested your command as the shinken user
  * Have you manually generated check results
  * Can you connect to your remote agent NRPE, NSClient++, etc. 
  * Have you defined a module on the wrong daemon (ex. NSCA receiver module on a Broker)
  * Have you created a diagram illustrating your templates and inheritance
  * System logs (/var/messages, windows event log)
  * Application logs (MongoDB, SQLite, Apache, etc)
  * Security logs (Filters, Firewalls operational logs)
  * Use top or Microsoft Task manager or process monitor (Microsoft sysinternals tools) to look for memory, cpu and process issues.
  * Use nagiostat to check latency and other core related metrics.
  * Is your check command timeout too long
  * Have you looked at your Graphite Carbon metrics
  * Can you connect to the Graphite web interface
  * Are there gaps in your data
  * Have you configured your storage schema (retention interval and aggregation rules) for Graphite collected data.
  * Are you sending data more often than what is expected by your storage schema.
  * Storing data to the Graphite databases, are you using the correct IP, port and protocol, are both modules enabled; Graphite_UI and graphite export.


FAQ Answers
===========

.. _troubleshooting/troubleshooting-shinken#FAQ-1:

Review the daemon logs
----------------------

A daemon is a Shinken process. Each daemon generates a log file by default. If you need to learn more about what is what, go back to :ref:`the shinken architecture <architecture/the-shinken-architecture>`.
The configuration of a daemon is set in the .ini configuration file(ex. brokerd.ini).
Logging is enabled and set to level INFO by default.

Default log file location ''local_log=%(workdir)s/schedulerd.log''

The log file will contain information on the Shinken process and any problems the daemon encounters.


.. _troubleshooting/troubleshooting-shinken#FAQ-2:

Changing the log level in the configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit the <daemon-name>.ini file, where daemon name is pollerd, schedulerd, arbiterd, reactionnerd, receiverd.
Set the log level to: DEBUG 
Possible values: DEBUG,INFO,WARNING,ERROR,CRITICAL

Re-start the Shinken process.


.. _troubleshooting/troubleshooting-shinken#FAQ-3:

OSError read-only filesystem error
----------------------------------

You poller daemon and reactionner daemons are not starting and you get a traceback for an OSError in your logs.

''OSError [30] read-only filesystem''

Execute a 'mount' and verify if /tmp or /tmpfs is set to 'ro' (Read-only).
As root modify your /etc/fstab to set the filesystem to read-write.


.. _troubleshooting/troubleshooting-shinken#FAQ-4:

OSError too many files open
---------------------------

The operating system cannot open anymore files and generates an error. Shinken opens a lot of files during runtime, this is normal. Increase the limits.

Google: changing the max number of open files linux / debian / centos / RHEL

cat /proc/sys/fs/file-max

# su - shinken
$ ulimit -Hn
$ ulimit -Sn

This typically changing a system wide file limit and potentially user specific file limits. (ulimit, limits.conf, sysctl, sysctl.conf, cat /proc/sys/fs/file-max)

# To immediately apply changes
ulimit -n xxxxx now


.. _troubleshooting/troubleshooting-shinken#FAQ-5:

Notification emails have generic-host instead of host_name
----------------------------------------------------------

Try defining host_alias, which is often the field used by the notification methods.

Why does Shinken use both host_alias and host_name. Flexibility and historicaly as Nagios did it this way.


