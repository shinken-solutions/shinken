.. _advanced/triggers:

========
Triggers
========

.. warning::  This is currently in Beta. DO NOT use in production. 


Define and use triggers
************************

A trigger object is something that can be called after a "change" on an object. It's a bit like Zabbix trigger, and should be used only if you need it. In most cases, direct check is easier to setup :)

Here is an example that will raise a critical check if the CPU is too loaded:

.. note:: If your trigger is made to edit output add the trigger_broker_raise_enabled parameter into the service definition.
          If not, Shinken will generate 2 broks (1 before and 1 after the trigger). This can lead to bad data in broker module (Graphite)

::
  
  define service{
        use                             local-service         ; Name of service template to use
        host_name                       localhost
        service_description             Current Load trigger
        check_command                   check_local_load!5.0,4.0,3.0!10.0,6.0,4.0
        trigger_name                    simple_cpu
        trigger_broker_raise_enabled    1
        }
  
  
Then define your trigger in etc/trigger.d/yourtrigger.trig. here the file is simple_cpu.trig

::

  
  try:

    load = perf(self, 'load1')
    print "Founded load", load
    if load >= 10:
        critical(self, 'CRITICAL | load=%d' % load)
    elif load >= 5:
        warning(self, 'WARNING | load=%d' % load)
    else:
        ok(self, 'OK | load=%d' % load)
  except:
  
    unknown(self, 'UNKNOWN | load=%d' % load)
  
  
Finally, add the triggers_dir=trigger.d statement to your shinken.cfg

