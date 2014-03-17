.. _gettingstarted/installations/shinken-env-setup:

================================
Configure Shinken for Production
================================

If you have installed Shinken with packages, they should be production-ready. Otherwise, you should do the following steps to ensure everything is fine.


Enable Shinken at boot
=======================

This depend on your Linux distribution (actually it's related to the init mechanism : upstart, systemd, sysv ..) you may use one of the following tool.

Systemd
--------

This enable Shinken service on a systemd base OS. Note that a Shinken service can be used to start all service.

::

  for i in arbiter poller reactionner scheduler broker receiver; do
  systemctl enable shinken.service;
  done


RedHat / CentOS
----------------

This enable Shinken service on a RedHat/CentOS. Note that a Shinken service can be used to start all service.

::

  chkconfig shinken on


Debian / Ubuntu
----------------

This enable Shinken service on a Debian/Ubuntu.

::

  update-rc.d shinken defaults


Start Shinken
==============

This also depend on the OS you are running. You can start Shinken with one of the following:

::

  /etc/init.d/shinken start
  service shinken start
  systemctl start shinken


Configure Shinken for Sandbox
==============================

If you want to try Shinken and keep a simple configuration you may not need to have Shinken enabled at boot.
In this case you can just start Shinken with the simple shell script provided into the sources.

::

  ./bin/launch_all.sh


You will have Shinken Core working. No module are loaded for now. You need to install some with the :ref:`command line interface <shinken_cli>`


Configure Shinken for Development
==================================

If you are willing to edit Shinken source code, you should have chosen the third installation method.
In this case you have currently the whole source code in a directory.

The first thing to do is edit the **etc/shinken.cfg** and change the shinken user and group (you can comment the line). You don't need a shinken user do you?
Just run shinken as the current user, creating user is for real shinken setup :)

To manually launch Shinken do the following :

::

   ./bin/shinken-scheduler -c /etc/shinken/daemons/schedulerd.ini -d
   ./bin/shinken-poller -c /etc/shinken/daemons/pollerd.ini -d
   ./bin/shinken-broker -c /etc/shinken/daemons/brokerd.ini -d
   ./bin/shinken-reactionner -c /etc/shinken/daemons/reactionnerd.ini -d
   ./bin/shinken-arbiter -c /etc/shinken/shinken.cfg -d
   ./bin/shinken-receiver -c /etc/shinken/daemons/receiverd.ini -d

