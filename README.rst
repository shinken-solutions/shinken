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

Requirements
============

There are common and conditional requirements for the three installation
methods which are described below. Keep in mind that you should never mix the methods.
Thus if you installed with the first method, you have to use
that method as well when you update or remove your installation.

The "install script" method (recommended) tries to
do all the necessary steps for you. You can choose that one if your OS is
compatible with it. If you choose that one, you can skip/skim
 over the requirements section and may come back to it later if something goes wrong.

However it is recommended to check any requirement manually just to make sure that
it should work.


Common Requirements
-------------------

`shinken` requires

* `Python`__ 2.4 or higher (Python 2.6 or higher is recommended if you want to use the Web interface)
* `setuptools` or `distribute` for installation (see below).
* Pyro less then 4.14
* `multiprocessing`__ Python package when using Python 2.4 or 2.5
  (`multiprocessing` is already included in Python 2.6 and higher)

__ http://www.python.org/download/
__ http://pypi.python.org/pypi/multiprocessing/

* python-devel Package


Conditional Requirements
------------------------

If (and only if) you plan to use the `livestatus` module or the web interface, you will also
need

* `simplejson`__
* `ujson`__  (ujson is used in Livestatus for its speed)
* `pysqlite`__

__ http://pypi.python.org/pypi/simplejson/
__ http://pypi.python.org/pypi/ujson/ 
__ http://code.google.com/p/pysqlite/

Installing/Checking Common Requirements on Windows
==================================================

There is an installation guide for Windows and an installation package.

* `Windows Installation guide on the Wiki`__

__ http://www.shinken-monitoring.org/wiki/shinken_10min_start

Installing/Checking Common Requirements on Linux
================================================

Python
------
For Python itself, the version which comes with almost all distributions
should be okay.

Pyro
----
Under ubuntu, you can grab the Pyro module with::

  sudo apt-get install pyro

Under other distributions, you can search for it::

  yum search pyro

And if you do not find it, you can install it from PyPI::

  easy_install pyro


How to install Shinken
======================


Preliminary Steps
-----------------

* Download and untar shinken.

* Create a user account and a group for shinken on your system (not necessary if using install script)::

   useradd --user-group shinken
   usermod --lock shinken

Important Note:: NEVER EVER MIX THE DIFFERENTS INSTALLATION METHODS. THIS WILL RUN YOU IN BIG TROUBLES. CHOOSE ONE AND UNINSTALL BEFORE TRYING THE OTHER.

First way: install script (recommended for end users)
=====================================================

Install
-------
You can use the install script utility located at the root of the shinken sources.
The script creates the user and group, installs all dependencies and then it installs shinken. It is compatible with Debian, Ubuntu, Centos/Redhat 5.x and 6.x
The only requirement is an internet connection for the server on which you want to install shinken. It also allows to modify the installation folder in a configuration file.

If you want shinken installed in seconds (default in /usr/local/shinken), just run ::

  install -i

see install.d/README file for further information.

Update
------
1 - grab the latest shinken archive and extract its content 

2 - cd into the resulting folder

3 - backup shinken configuration plugins and addons and copy the backup id::
    
  ./install -b

4 - remove shinken (if you installed addons with the installer say no to the question about removing the addons)::
    
  ./install -u

5 - install the new version::

  ./install -i

6 - restore the backup::

  ./install -r backupid


Remove
-------
cd into shinken source folder and run::
  ./install -u

Running
-------
The install script also installs some `init.d` scripts, enables them at boot time and starts them right after the install process ends. 



Second way: district directory (clean way)
=====================================================

Install
-------
In fact you can install the application by using the `setup.py` script.
No compilation is needed!
`setup.py` will install the shinken library in the python path, create the
`/etc/shinken` and `/var/lib/shinken` directory (you can change them in
the `setup.cfg` file before launching `setup.py`). You will
need the `python-setuptools` package for it. Then just run::

  sudo python setup.py install --install-scripts=/usr/bin/

Update
------

For this way you can launch ::
    sudo python setup.py update --install-scripts=/usr/bin/

Remove
------
There is a script called clean.sh in the source directory for this task.
It contains relative paths so it should be run from within the source dir.
Beware, it will delete all Shinken related files!

Running
-------
The `setup.py` installs some `init.d` scripts, let's use them::

  /etc/init.d/shinken-scheduler start
  /etc/init.d/shinken-poller start
  /etc/init.d/shinken-reactionner start
  /etc/init.d/shinken-broker start
  /etc/init.d/shinken-arbiter start



Third way: all in a directory (ugly but quick way ;)
=====================================================

Install
-------
After unpacking the tarball move the shinken directory to the desired destination
and give it to the shinken user::

  mv shinken /usr/local
  chown -R shinken:shinken /usr/local/shinken

Update / Remove
--------------
Should be easy here.

Running
-------
It's easy, there is already a launch script for you::

  shinken/bin/launch_all.sh



Where is the configuration?
===========================

The configuration is where you put the etc directory (in
`/usr/local/shinken/etc` for a quick and dirty install, `/etc/shinken`
for a clean one).

The `nagios.cfg` file is meant to be shared with Nagios. All Shinken
specific objects (like links to daemons or realms) are in the file
`shinken-specific.cfg`.


Do I need to change my existing Nagios configuration?
=====================================================

No, there is no need to change the existing configuration - unless
you want to add some new hosts and services. Once you are comfortable
with Shinken you can start to use its unique and powerful features.


Known bugs
================================

None that we know of. :)

If you find one, please post it to the bug and issue tracker :
https://github.com/naparuba/shinken/issues
