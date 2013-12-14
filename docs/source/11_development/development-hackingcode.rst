.. _development-hackingcode:





==================================== ============================
:ref:`Prev <development-epnplugins>` :ref:`Up <part-development>`
==================================== ============================



==========================
 Hacking the Shinken Code 
==========================




Development goals 
==================


Shinken is an open source program. 

Enhancements, optimization, fixes, these are all good reasons to create a patch and send it to the development mailing list. Even if you are not sure about the quality of your patch or your ideas, submit them to the mailing list for review or comment. Having feedback is essential to any project.

This documentation will show how to add code to Shinken. Shinken is written in Python. If you are new to python please consider reading this ` introduction / beginners guide`_.



Development rules 
==================


If you wish to commit code to the Shinken repository, you must strive to follow the :ref:`Shinken development rules <programming_rules >`.



How is Shinken's code organized 
================================


The Shinken code is in the shinken directory. All important source files are :

  * bin/shinken-* : source files of daemons
  * shinken/objects/item.py : base class for nearly all important objects like hosts, services and contacts.
  * shinken/*link.py : class used by Arbiter to connect to daemons.
  * shinken/modules/*/*py : modules for daemons (like the Broker).
  * shinken/objects/schedulingitem.py : base class for host/service that defines all the algorithms for scheduling.



Datadriven programming in Shinken code 
=======================================


A very important thing in Shinken code is the data programming method : instead of hardcoding transformation for properties, it's better to have a array (dict in Python) that described all transformations we can use on these properties.

With this method, a developer only needs to add this description, and all transformations will be automatic (like configuration parsing, inheritance application, etc).

Nearly all important classes have such an array. It's named "properties" and is attached to the class, not the object itself.

Global parameters of the application (like the one for nagios.cfg file) are in the properties of the Config class. They are defined like: 'enable_notifications' : {'required':False, 'default':'1', 'pythonize': to_bool, 'class_inherit' : [(Host, None), (Service, None), (Contact, None)]},

Here, this property is:

  * not required
  * It's default value is 1
  * We use the 'to_bool' function to transform the string from the configuration file to a Python object
  * We put this value in the Host and Service class with the same name (None==keep the name). The string in place of None, this string is used to access this property from the class.

Specific properties for objects like Hosts or Services are in a properties dict(dictionary), but without the 'class_inherit' part. Instead of this, they have the "fill_brok" part. A "brok" is an inter process message. It's used to know if the property must be sent in the following brok types:

  * full_status : send a full status brok, like at daemon starting.
  * check_result : send when a check came back
  * next_schedule : send when a new check is scheduled

These classes also have another "properties" like dict : "running_properties". It's like the standard one, but for running only properties (aka no configuration based properties).



Programming with broker modules in Shinken 
===========================================


Modules are pieces of code that are executed by a daemon.

Module configuration and startup is controlled in the shinken-specific.cfg

  - The module is declared in a daemon
  - The module itself is defined and its variables set

A shinken module class must have an _init_, init and documentation.
A shinken module can use the following functions:
  * managed_broks: A specific function that will dynamically build calls for functions for specific brok.types if the functions exist.
  * manage_NAME-OF-BROK-TYPE_broks: The function that will process a specific type of brok

The brok types are created in the code and are not registered in a central repository. At this time the following brok types exist and can be processed by broker modules.

  * clean_all_my_instance_id
  * host_check_resulthost_next_schedule
  * initial
  * initial_command_status
  * initial_contactgroup_status
  * initial_contact_status
  * initial_hostgroup_status
  * initial_host_status
  * initial_poller_status
  * initial_reactionner_status
  * initial_receiver_status
  * initial_scheduler_status
  * initial_servicegroup_status
  * initial_service_status
  * initial_timeperiod_status
  * log
  * notification_raise
  * program_status
  * service_check_result
  * service_check_resultup
  * service_next_schedule
  * update
  * update_host_status
  * update_poller_status
  * update_program_status
  * update_reactionner_status
  * update_receiver_status
  * update_scheduler_status
  * update_service_status



Example of code hacking : add a parameter for the flapping history 
===================================================================


  * :ref:`Configuration part <development-hackingcode#configuration_part>`
  * :ref:`Running part <development-hackingcode#running_part>`
  * :ref:`The perfect patch <development-hackingcode#the_perfect_patch>`

In the Nagios code, the flapping state history size is hard coded (20). As in the first Shinken release. Let'S see how it works to add such a parameter in the global file and use it in the scheduling part of the code.

We will see that adding such a parameter is very (very) easy. To do this, only 5 lines need to be changed in :

  * config.py : manage the global configuration
  * schedulingitem.py : manage the scheduling algorithms of host/services



Configuration part 
-------------------


In the first one (config.py) we add an entry to the properties dict : "flap_history" : {"required":False, "default":'20", "pythonize": to_int, "class_inherit" : [(Host, None), (Service, None)]}, So this property will be an option, with 20 by default, and will be put in the Host and Service class with the name 'flap_history'.

That's all for the configuration! Yes, no more add. Just one line :)



Running part 
-------------


Now the scheduling part (schedulingitem.py). The hard code 20 was used in 2 functions : add_flapping_change and update_flapping. From this file, we are in an object named self in Python. To access the 'flap_history' of the Host or Service class of this object, we just need to do : flap_history = self.__class__.flap_history Then we change occurrences in the code : if len(self.flapping_changes) > flap_history: [...] r += i*(1.2-0.8)/flap_history + 0.8 r = r / flap_history

That's all. You can test and propose the patch in the devel list. We will thank you and after some patch proposals, you can ask for a git access, you will be a Shinken developer :)



The perfect patch 
------------------


If you can also add this property in the documentation (/doc directory)

If you followed the Python style guide. (See development rules)

If you created an automated test case for a new feature. (See development rules)

If you documented any new feature in the documentation wiki.

The patch will be __***perfect***__ :)


.. _ introduction / beginners guide: http://wiki.python.org/moin/BeginnersGuide 