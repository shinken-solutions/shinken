===================================
Presentation of the Shinken project
===================================

Welcome to the Shinken project.

Shinken is a modern, Nagios compatible monitoring fremawork, written in
Python. Its main goal is to give users a flexible architecture for
their monitoring system that is designed to scale to large environments.

Shinken is backwards-compatible with the Nagios configuration standard
and plugins. It works on any operating system and architecture that
supports Python, which includes Windows and GNU/Linux.

Requirements
============

There are mandatory and conditional requirements for the installation
methods which are described below.


Mandatory Requirements
----------------------

`shinken` requires

* `Python`__ 2.6 or higher (2.7 will get higher performances)
* `python-pycurl`__ Python package for Shinken daemon communications
* `setuptools`__ or `distribute` Python package for installation



__ http://www.python.org/download/
__ http://pycurl.sourceforge.net/
__ http://pypi.python.org/pypi/setuptools/




Conditional Requirements
------------------------

* `Python`__ 2.7 is required for developers to run the test suite, shinken/test/
* `python-cherrypy3`__ (recommanded) enhanceddaemons communications, especially in HTTPS mode

__ http://www.python.org/download/
__ http://www.cherrypy.org/

Installing/Checking Common Requirements on Windows
==================================================

There is an installation guide for Windows and an installation package.

* `Windows Installation guide on the Wiki`__

__ http://www.shinken-monitoring.org/wiki/shinken_10min_start


Installing on Linux
================================================


How to install Shinken
======================

You will need a specific user for running shinken :

   useradd --user-group shinken

You simply need to launch:

  python setup.py install


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
=====================================================

No, there is no need to change the existing configuration - unless
you want to add some new hosts and services. Once you are comfortable
with Shinken you can start to use its unique and powerful features.


Learn more about how to use and configure Shinken
=================================================

Jump to the `Shinken documentation wiki`__.

__ http://www.shinken-monitoring.org/wiki/


If you find a bug
================================

Bugs are tracked in the `issue list on GitHub`__ . Always search for existing issues before filing a new one (use the search field at the top of the page).
When filing a new bug, please remember to include:

*	A helpful title - use descriptive keywords in the title and body so others can find your bug (avoiding duplicates).
*	Steps to reproduce the problem, with actual vs. expected results
*	Shinken version (or if you're pulling directly from the Git repo, your current commit SHA - use git rev-parse HEAD)
*	OS version
*	If the problem happens with specific code, link to test files (gist.github.com is a great place to upload code).
*	Screenshots are very helpful if you're seeing an error message or a UI display problem. (Just drag an image into the issue description field to include it).

__ http://github.com/naparuba/shinken/issues/
