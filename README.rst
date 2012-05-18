===================================
Presentation of the Shinken project
===================================

Welcome to the Shinken project.

Shinken is a new, Nagios compatible monitoring tool, written in
Python. Its main goal is to give users a flexible architecture for
their monitoring system that is designed to scale to large environments.
It’s as simple as in all the marketing “cloud computing” slides, but here,
it’s real!

Shinken is backwards-compatible with the Nagios configuration standard
and plug-ins. It works on any operating system and architecture that
supports Python, which includes Windows and GNU/Linux.


How to install Shinken
=========================

You just need to add a shinken user (in the shinken group) on your
system::

   useradd --user-group shinken
   usermod --lock shinken

First way: all in a directory (ugly but quick way ;)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Then move the shinken directory and give it to the shinken user::

  mv shinken /usr/local
  chown -R shinken:shinken /usr/local/shinken

Second way: district directory (clean way)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can install really the application by using the `setup.py` script.
It will install the shinken library in the python path, create the
`/etc/shinken` and `/var/lib/shinken` directory (you can change them in
the `setup.cfg` file before launching `setup.py`). You will
need the `python-setuptools` package for it. Then just run::

  sudo python setup.py install --install-scripts=/usr/bin/

For the compilation part in both way it's easy: there is no
compilation!

Third way: install script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note : NEVER EVER MIX THE DIFFERENTS INSTALLATION WAYS. THIS WILL RUN YOU IN BIG TROUBLES. IF YOU CHOOSE ONE WAY DO NOT TRY OTHERS OR CLEAN UP BEFORE.

You can use the install utility script located at the root of the shinken sources.
The script creates the user and group, installs all dependencies and then it installs shinken. It is compatible with Debian, Ubuntu, Centos/Redhat 5.x and 6.x
The only requirement is an internet connection for the server on which you want to install shinken. It also allows to modify the installation folder in a configuration file.

If you want shinken installed in seconds (default in /usr/local/shinken), just run ::

  install -i

see install.d/README file for further informations.


How to update
=========================

If you used the setup.py way, launch ::
    sudo python setup.py update --install-scripts=/usr/bin/

If you used the install script way :

1 - grab the latest shinken archive and extract it's content 

2 - cd into the resulting folder

3 - backup shinken configuration plugins and addons and copy the backup id::
    
  ./install -b

4 - remove shinken (if you installed addons with the installer say no to the question about removing the addons)::
    
  ./install -u

5 - install shinken::

  ./install -i

6 - restore the backup::

  ./install -r backupid


Requirements
=========================

`shinken` requires

* `Python`__ 2.4 or higher (Python 2.6 or higher is recommended if you want to use the Web interface)
* `setuptools`__ or `distribute`__ for installation (see below).
* `Pyro`__
* `multiprocessing` Python package when using Python 2.4 or 2.5
  (`multiprocessing` is already included in Python 2.6 and higher)

__ http://www.python.org/download/
__ pyro
__ http://pypi.python.org/pypi/multiprocessing/

If (and only if) you plan to use the `livestatus` module or the web interface, I'll also
need

* `simplejson`__ 
* `pysqlite`__

__ http://pypi.python.org/pypi/simplejson/ and
__ http://code.google.com/p/pysqlite/

Just untar and launch `python setup.py install` (and be sure to have
installed the `python-devel` package too).

For Python, it should be okay with almost all distribution.

Under ubuntu, you can grab the Pyro module with::

  sudo apt-get install pyro

Under other distributions, you can search for it::

  yum search pyro

And if you do not find it, you can install it from PyPI::

  easy_install pyro

And that's all folks :)


Where is the configuration?
================================

The configuration is where you put the etc directory (in
`/usr/local/shinken/etc` for a quick and dirty install, `/etc/shinken`
for a clean one).

The `nagios.cfg` file is meant to be shared with Nagios. All Shinken
specific objects (like links to daemons or realms) are in the file
`shinken-specific.cfg`.


Do I need to change my existing Nagios configuration?
===================================================

No, there is no need to change the existing configuration - unless
you want to add some new hosts and services. Once you are comfortable
with Shinken you can start to use its unique and powerful features.


How to run Shinken
================================

Quick and dirty way
~~~~~~~~~~~~~~~~~~~~

It's easy, there is a already launch script for you::

  shinken/bin/launch_all.sh

Clean way
~~~~~~~~~~~~~~~~~~~~

The `setup.py` install some `init.d` scripts, let's use them::

  /etc/init.d/shinken-scheduler start
  /etc/init.d/shinken-poller start
  /etc/init.d/shinken-reactionner start
  /etc/init.d/shinken-broker start
  /etc/init.d/shinken-arbiter start

Install script
~~~~~~~~~~~~~~~~~~~~

The install script also install some `init.d` scripts and enable them at boot time and start them right after install process end. 

Known bugs
================================

None that we know of. :)

If you find one, please post it to the bug and issue tracker :
https://github.com/naparuba/shinken/issues


How to run uninstall Shinken
================================

Clean all :)
~~~~~~~~~~~~~~~~~~~~

There is a script called clean.sh in the source directory for this task.
Beware, it will supress all Shinken related files!

If you used install script 
~~~~~~~~~~~~~~~~~~~~~~~~~~

cd into shinken source folder and run::
  ./install -u

