.. _runningshinken-startstop:




===============================
 Starting and Stopping Shinken 
===============================

There's more than one way to start, stop, and restart Shinken. Here are some of the more common ones...

Always make sure you :ref:`Verifying Your Configuration <runningshinken-verifyconfig>` before you (re)start Shinken.



Starting Shinken 
=================


- Init Script: The easiest way to start the Shinken daemon is by using the init script like so:

::

  linux:~ # /etc/rc.d/init.d/shinken start
  
- Manually: You can start the Shinken daemon manually with the "-d" command line option like so:

::

  linux:~ # /usr/local/shinken/bin/shinken-scheduler -d -c /usr/local/shinken/etc/schedulerd.ini
  linux:~ # /usr/local/shinken/bin/shinken-poller -d -c /usr/local/shinken/etc/pollerd.ini
  linux:~ # /usr/local/shinken/bin/shinken-reactionner -d -c /usr/local/shinken/etc/reactionnerd.ini
  linux:~ # /usr/local/shinken/bin/shinken-broker -d -c /usr/local/shinken/etc/brokerd.ini
  linux:~ # /usr/local/shinken/bin/shinken-arbiter -d -c /usr/local/shinken/etc/nagios.cfg -c /usr/local/shinken/etc/shinken-specific.cfg
  
.. important::  Enabling debugging output under windows requires changing registry values associated with Shinken



Restarting Shinken 
===================


Restarting/reloading is nececessary when you modify your configuration files and want those changes to take effect.

- Init Script: The easiest way to restart the Shinken daemon is by using the init script like so:

::

  linux:~ # /etc/rc.d/init.d/shinken restart

- Manually: You can restart the Shinken process by sending it a SIGTERM signal like so:

::

  linux:~ # kill <arbiter_pid>
  linux:~ # /usr/local/shinken/bin/shinken-arbiter. -d -c /usr/local/shinken/etc/nagios.cfg
  
  


Stopping Shinken 
=================


- Init Script: The easiest way to stop the Shinken daemons is by using the init script like so:

::

  linux:~ # /etc/rc.d/init.d/shinken stop
  
- Manually: You can stop the Shinken process by sending it a SIGTERM signal like so:

::

  linux:~ # kill <arbiter_pid> <scheduler_pid> <poller_pid> <reactionner_pid> <broker_pid>
  
