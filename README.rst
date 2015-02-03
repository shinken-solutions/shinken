===================================
Presentation of the Shinken project
===================================

Welcome to the Shinken project.

.. image:: https://pypip.in/version/Shinken/badge.svg
    :target: https://pypi.python.org/pypi//Shinken/
    :alt: Version
.. image:: https://api.travis-ci.org/naparuba/shinken.svg?branch=master
  :target: https://travis-ci.org/naparuba/shinken

Shinken is a modern, Nagios compatible monitoring framework, written in
Python. Its main goal is to give users a flexible architecture for
their monitoring system that is designed to scale to large environments.

Shinken is backwards-compatible with the Nagios configuration standard
and plugins. It works on any operating system and architecture that
supports Python, which includes Windows and GNU/Linux.

Requirements
============

See the `Documentation`__ 

__ https://shinken.readthedocs.org/en/latest/02_gettingstarted/installations/shinken-installation.html#requirements

There are mandatory and conditional requirements for the installation
methods which are described below.


Installing Shinken
==================

See the `Documentation`__ 

__ https://shinken.readthedocs.org/en/latest/02_gettingstarted/installations/shinken-installation.html



Update
------

Launch:

  python setup.py update

It will only update the shinken lib and scripts, but won't touch your current configuration


Running
-------

Shinken is installed with `init.d` scripts, enables them at boot time and starts them right after the install process ends. Based on your linux distro you only need to do:

  chkconfig --add shinken
  chkconfig shinken on

or :

  update-rc.d shinken defaults 20



Where is the configuration?
===========================

The configuration is on the directory, `/etc/shinken`.


Where are the logs?
===================

Logs are in /var/log/shinken
(what did you expect?)


I got a bug, how to launch the daemons in debug mode?
=====================================================

You only need to launch:

  /etc/init.d/shinken -d start

Debug logs will be based on the log directory (/var/log/shinken)


I switched from Nagios, do I need to change my existing Nagios configuration?
=============================================================================

No, there is no need to change the existing configuration - unless
you want to add some new hosts and services. Once you are comfortable
with Shinken you can start to use its unique and powerful features.


Learn more about how to use and configure Shinken
=================================================

Jump to the Shinken documentation__.

__ https://shinken.readthedocs.org/en/latest/


If you find a bug
================================

Bugs are tracked in the `issue list on GitHub`__ . Always search for existing issues before filing a new one (use the search field at the top of the page).
When filing a new bug, please remember to include:

*	A helpful title - use descriptive keywords in the title and body so others can find your bug (avoiding duplicates).
*	Steps to reproduce the problem, with actual vs. expected results
*	Shinken version (or if you're pulling directly from the Git repo, your current commit SHA - use git rev-parse HEAD)
*	OS version
*	If the problem happens with specific code, link to test files (`gist.github.com`__  is a great place to upload code).
*	Screenshots are very helpful if you're seeing an error message or a UI display problem. (Just drag an image into the issue description field to include it).

__ https://github.com/naparuba/shinken/issues/
__ https://gist.github.com/


Install Shinken as python lib
=============================

In  avirtualenv ::

  virtualenv env
  source env/bin/activate
  python setup.py install_lib
  python -c 'from shinken.bin import VERSION; print(VERSION)'

Or directly on your system::

  sudo python setup.py install_lib
  python -c 'from shinken.bin import VERSION; print(VERSION)'


Get Shinken dev environment
===========================


To setup Shinken dev environment::

  virtualenv env
  source env/bin/activate
  python setup.py develop
  python setup.py install_data

If you want to use init scripts in your virtualenv you have to REsource ``activate``::

  source env/bin/activate


Folders
-------

env/etc: Configuration folder

env/var/lib/shinken/modules: Modules folder

env/var/log/shinken: Logs folder

env/var/run/shinken: Pid files folder

Launch daemons
--------------

With binaries
~~~~~~~~~~~~~

Arbiter::

  shinken-arbiter -c env/etc/shinken/shinken.cfg

Broker::

  shinken-broker -c env/etc/shinken/daemons/brokerd.ini

Scheduler::

  shinken-scheduler -c env/etc/shinken/daemons/schedulerd.ini

Poller::

  shinken-poller -c env/etc/shinken/daemons/pollerd.ini

Reactionner::

  shinken-reactionner -c env/etc/shinken/daemons/reactionnerd.ini

Receiver::

  shinken-receiver -c env/etc/shinken/daemons/receiverd.ini


With init scripts
~~~~~~~~~~~~~~~~~

Arbiter::

  env/etc/init.d/shinken-arbiter start

Broker::

  env/etc/init.d/shinken-broker start

Scheduler::

  env/etc/init.d/shinken-scheduler start

Poller::

  env/etc/init.d/shinken-poller start

Reactionner::

  env/etc/init.d/shinken-reactionner start

Receiver::

  env/etc/init.d/shinken-receiver start
