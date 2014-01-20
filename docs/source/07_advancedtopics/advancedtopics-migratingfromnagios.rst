.. _advancedtopics-migratingfromnagios:



=================================
Migrating from Nagios to Shinken 
=================================




How to to import existing Nagios states 
========================================

It's possible with the *nagios_retention_file* module in fact.

**The "migration" is done in two phases :**

- First you launch shinken with both NagiosRetention and PickleRetention modules. It will load data from NagiosRetention and save them in a more "efficient" file. So add in *shinken-specififc.cfg* file both modules for your scheduler object: 

::

  modules                 NagiosRetention ,PickleRetention

- Then you remove the NagiosRetention (it's a read only module, don't fear for your nagios retention file) and restart with just PickleRetention. <code>modules                 PickleRetention

You're done.


//Source:// `Topic on forum`_

.. important::  This method has met with limited success, further testing of the NagiosRetention module is required. An issues encountered should be raised in the Shinken issue tracker on github.



How to to import Nagios reporting data 
=======================================


There is no out of the box migration path for Historical reports.

.. _Topic on forum: http://www.shinken-monitoring.org/forum/index.php/topic,233.0.html
