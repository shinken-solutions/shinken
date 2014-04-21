===================================
Presentation of the Shinken project
===================================

Welcome to the Shinken project.

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

Jump to the `Shinken documentation__.

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
