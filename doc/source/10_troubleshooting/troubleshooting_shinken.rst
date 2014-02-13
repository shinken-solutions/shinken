.. _troubleshooting_shinken:



==============================
FAQ - Shinken troubleshooting 
==============================




FAQ Summary =
=============


Shinken users, developers, administrators possess a body of knowledge that usually provides a quick path to problem resolutions. The Frequently Asked Questions questions are compiled from user questions and issues developers may run into.

Have you consulted at all the :ref:`resources available for users and developers <how_to_contribute>`.

**__Before posting a question to the forum:__**
   * Read the through the  :ref:`Getting Started tutorials <>`
   * Search the documentation wiki
   * Use this FAQ
   * Bonus: Update this FAQ if you found the answer and think it would benefit someone else

Doing this will improve the quality of the answers and your own expertise.



Frequently asked questions 
---------------------------


  - :ref:`How to set my daemons in debug mode to review the logs? <troubleshooting_shinken#Review the daemon logs>`
  - :ref:`I am getting an OSError read-only filesystem <troubleshooting_shinken#OSError read-only filesystem error>`
  - :ref:`I am getting an OSError [Errno 24] Too many open files <troubleshooting_shinken#OSError too many files open>`
  - :ref:`Notification emails have generic-host instead of host_name <troubleshooting_shinken#Notification emails have generic-host instead of host_name>`
  - :ref:`Thruk/Multisite reporting doesn't work using Shinken 1.2 <troubleshooting_shinken#Reporting does not work with Shinken 1.2>`
  - :ref:`Pyro MemoryError during configuration distribution by the Arbiter to other daemons(satellites) <troubleshooting_shinken#How to identify the source of a Pyro MemoryError>`



General Shinken troubleshooting steps to resolve common issue =
---------------------------------------------------------------

  - Have you mixed installation methods! :ref:`Cleanup and install using a single method <shinken_10min_start>`.
  - Have you installed the :ref:`check scripts and addon software <shinken_10min_start>`
  - Is Shinken even running?
  - Have you checked the :ref:`Shinken pre-requisites <prerequisites_1_2>`?
  - Have you :ref:`configured the WebUI module <use_with_webui>` in your shinken-specific.cfg file
  - Have you :ref:`completed the Shinken basic configuration <configure_shinken>` and :ref:`Shinken WebUI configuration <use_with_webui>`
  - Have you reviewed your Shinken centralized (:ref:`Simple-log broker module <the_broker_modules>`) logs for errors
  - Have you reviewed your :ref:`Shinken daemon specific logs <troubleshooting_shinken#Review the daemon logs>` for errors or tracebacks (what the system was doing just before a crash)
  - Have you reviewed your :ref:`configuration syntax <configuringshinken-config>` (keywords and values)
  - Is what you are trying to use installed? Are its dependancies installed! Does it even work.
  - Is what you are trying to use :ref:`a supported version <shinken_installation_requirements>`?
  - Are you using the same Python Pyro module version on all your hosts running a Shinken daemon (You have to!)
  - Are you using the same Python version on all your hosts running a Shinken daemon (You have to!)
  - Have you installed Shinken with the SAME prefix (ex: /usr/local) on all your hosts running a Shinken daemon (You have to!)
  - Have you enabled debugging logs on your daemon(s)
  - How to identify the source of a Pyro MemoryError
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




Reporting does not work with Shinken 1.2 
-----------------------------------------


Set your Scheduler log level to INFO by editing shinken/etc/scheduler.ini.

Upgrade to Shinken 1.2.1, which fixes a MongoDB pattern matching error.



How to identify the source of a Pyro MemoryError 
-------------------------------------------------


Are the satellites identical in every respect? 
All the others work just fine?
What is the memory usage of the scheduler after sending the configuration data for each scheduler?
Do you use multiple realms?
Does the memory use increase for each Scheduler?

Possible causes

1) Shinken Arbiter is not preparing the configuration correctly sending overlarge objects
2) there is a hardware problem that causes the error, for instance a faulty memory
chip or bad harddrive sector. Run a hardware diagnostics check and a memtest (http://www.memtest.org/) on
the failing device
3) a software package installed on the failing sattelite has become corrupted. Re-install all software related to Pyro, possibly the whole OS.
4) or perhaps, and probably very unlikely, that the network infrastructure
(cables/router/etc) experience a fault and deliver corrupt packets to the failing
sattelite, whereas the other sattelites get good data.. Do an direct server to server test or end to end test using iPerf to validate the bandwidth and packet loss on the communication path.


Other than that, here are some general thoughts. A MemoryError means:
"Raised when an operation runs out of memory but the situation may still be rescued
(by deleting some objects). The associated value is a string indicating what kind of
(internal) operation ran out of memory. Note that because of the underlying memory
management architecture (C"s malloc() function), the interpreter may not always be
able to completely recover from this situation; it nevertheless raises an exception so
that a stack traceback can be printed, in case a run-away program was the cause. "

5) Check on the server the actual memory usage of the Scheduler daemon.
Another possible reason for malloc() to fail can also be memory fragmentation, which
means that there's enough free RAM but just not a free chunk somewhere in between that
is large enough to hold the required new allocation size. No idea if this could be the
case in your situation, and I have no idea on how to debug for this.

It is not entirely clear to me where exactly the memoryerror occurs: is it indeed
raised on the sattelite device, and received and logged on the server? Or is the
server throwing it by itself?

6) Other avenues of investigation
Try running the python interpreter with warnings on (-Wall).
Try using the HMAC key feature of Pyro to validate the network packets.
Try using Pyro's multiplex server instead of the threadpool server.

