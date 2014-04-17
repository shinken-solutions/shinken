.. _runningshinken/startstop:

===============================
 Starting and Stopping Shinken 
===============================

There's more than one way to start, stop, and restart Shinken. Here are some of the more common ones...

Always make sure you :ref:`verify your configuration <runningshinken/verifyconfig>` before you (re)start Shinken.


Starting Shinken 
=================

- Init Script: The easiest way to start the Shinken daemon is by using the init script like so:

::

  linux:~ # /etc/rc.d/init.d/shinken start
  
- Manually: You can start the Shinken daemon manually with the "-d" command line option like so:

::

  linux:~ # /usr/bin/shinken/shinken-scheduler -d -c /etc/shinken/daemons/schedulerd.ini
  linux:~ # /usr/bin/shinken/shinken-poller -d -c /etc/shinken/daemons/pollerd.ini
  linux:~ # /usr/bin/shinken/shinken-reactionner -d -c /etc/shinken/daemons/reactionnerd.ini
  linux:~ # /usr/bin/shinken/shinken-broker -d -c /etc/shinken/daemons/brokerd.ini
  linux:~ # /usr/bin/shinken/shinken-arbiter -d -c /etc/shinken/shinken.cfg
  
.. important::  Enabling debugging output under windows requires changing registry values associated with Shinken


Restarting Shinken 
===================

Restarting/reloading is nececessary when you modify your configuration files and want those changes to take effect.

- Init Script: The easiest way to restart the Shinken daemon is by using the init script like so:

::

  linux:~ # /etc/rc.d/init.d/shinken restart

- Manually: You can restart the Shinken process by sending it a SIGTERM signal like so:

::

  linux:~ # kill <configobjects/arbiter_pid>
  linux:~ # /usr/bin/shinken-arbiter -d -c /etc/shinken/shinken.cfg


Stopping Shinken 
=================

- Init Script: The easiest way to stop the Shinken daemons is by using the init script like so:

::

  linux:~ # /etc/rc.d/init.d/shinken stop
  
- Manually: You can stop the Shinken process by sending it a SIGTERM signal like so:

::

  linux:~ # kill <configobjects/arbiter_pid> <configobjects/scheduler_pid> <configobjects/poller_pid> <configobjects/reactionner_pid> <configobjects/broker_pid>
  
