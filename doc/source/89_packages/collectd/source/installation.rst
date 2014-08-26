.. _collectd_installation:

============
Installation
============


Download
========

The Collectd module is available here: 
  * https://github.com/shinken-monitoring/mod-collectd

Requirements
============

The Collectd module requires:

  * Python 2.6+
  * Shinken 2.0+

Installation
============

Copy the collectd module folder from the git repository to your shinken/modules directory (set by *modules_dir* in shinken.cfg)

CLI installation
~~~~~~~~~~~~~~~~

**TODO**


Manual installation
~~~~~~~~~~~~~~~~~~~

For example, if your modules dir is '/var/lib/shinken/modules':

::

  cd /var/lib/shinken/modules
  wget https://github.com/shinken-monitoring/mod-collectd/archive/master.zip -O mod-collectd.zip
  unzip mod-collectd.zip
  
