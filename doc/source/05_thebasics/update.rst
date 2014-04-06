.. _thebasics/update:

===============
Update Shinken 
===============

Whatever the way you used to install the previous version of Shinken, you should use the same to update. Otherwise juste start from scratch a new Shinken install.

As mentioned in the :ref:`installation page <gettingstarted/installations/shinken-installation>`, 1.X and 2.0 have big differences.

.. warning:: Don't forget to backup your shinken configuration before updating!

Update can be done by following (more or less) those steps :

 * Create the new paths for Shinken (if you don't want new paths then you will have to edit Shinken configuration)

::

  mkdir /etc/shinken /var/lib/shinken/ /var/run/shinken /var/log/shinken
  chown shinken:shinken /etc/shinken /var/lib/shinken/ /var/run/shinken /var/log/shinken


* Install Shinken by following the installation instructions

* Copy your previous Shinken configuration to the new path

::

  cp -pr /usr/local/shinken/etc/<your_config_dir> /etc/shinken/


* Copy the modules directory to the new one

::

  cp -pr /usr/local/shinken/shinken/modules /var/lib/shinken/


* Edit the Shinken configuration to match you need. Basically you will need to remove the default shinken configuration of daemons and put the previous one. Shinken-specific is now split into several files.
  Be carful with the ini ones, you may **merge** them if you modified them. Careful to put the right *cfg_dir* statement in the shinken.cfg.


.. important::  Modules directories have changed a lot in Shinken 2.0. If you copy paste the previous one it will work  **BUT** you may have trouble if you use Shinken CLI.
   
