.. _triggers:

========
Triggers
========

.. warning::  This is currently in Beta. DO NOT use in production. 

.. note:: Not up to date. See the bottom part for something recent 

A trigger object is something that can be called after a "change" on an object. It's a bit like Zabbix trigger, and should be used only if you need it. In most cases, direct check is easier to setup :)

It's defined like:

Here is an example that will raise a critical check if the CPU is too loaded:



Simple rule 
************


::
  
  define trigger{
   trigger_name    One_Cpu_too_high
   matching_rule   perf(self, 'cpu') >= 95
   hit_action      critical(self, 'Cpu is too loaded')
  }




Rule with an OR 
****************


Another one that will look if at least one CPU is too loaded (> 90% load) or the overall CPU is too loaded too (total > 60%):

::

  define trigger{
   trigger_name    One_or_more_cpu_too_high
   matching_rule   max([perf(self, 'cpu*')]) > 90 | avg([perf(self, 'cpu*')]) > 60
   hit_action      critical(self, 'Cpu is too loaded')
  }




Advanced correlation: active/passive cluster check 
***************************************************


It can be used for advanced correlation too:

If you want to do an active/passive check without a bp_rule here an example. This service will be the "cluster" service that show the overall state. It will have 2 custom macros: "master", the master server and "slave" the slave one.


::

  define trigger{
   trigger_name    Bad_active_passive
   matching_rule   (service(self.customs['master']).state == 'CRITICAL' & service(self.customs['slave']).state == 'CRITICAL') | (service(self.customs['master']).state == service(self.customs['slave']).state)
   hit_action      critical(self, 'Cluster got a problem')
  }


And if you want you can define a degraded one you can define another trigger for this same "cluster" service:

::
  
  define trigger{
   trigger_name    Degraded_service
   matching_rule   service(self.customs['master']).state == 'CRITICAL' & service(self.customs['slave']).state == 'OK'
   hit_action      warning(self, 'Cluster runs on slave!')
  }




Statefull rules 
****************


Here an example with statefull rules.

I will read a regexp like PORTSCAN FROM (\S+) TO \S+:(\d+) on a service, and create an "event" that got a 60min lifetime. It will be add on services on all hosts for example.


::
  
  define trigger{
   trigger_name    Log_post_scan
   matching_rule   regexp(self.output, 'PORTSCAN FROM (?P<source>\S+) TO (?P<dest>\S+):(?P<port>\d+)')
   hit_action      create_event('HORIZONTAL SCAN FROM SOURCE IP %s' % source, 60)
  }


And a aggregated one will raise the alert if need:


::
  
  define trigger{
   trigger_name    Raise_too_much_scans
   matching_rule   sources=get_events_count_group_by('HORIZONTAL SCAN FROM SOURCE IP (?P<source>\S+)'))
   hit_action      [critical(self, 'The IP %s scan too much ips' % source) for (source, nb) in sources.iteritems() if nb > 10]
  }




Compute KPI 
************


You maybe want to compute a "KPI" (key point indicator) from various sources. You can also do it with triggers.

Let take an example, You got a cluster of N webservers. Each is returning in a check the number of active connections, but you want the overall. You just need to define a new service that will take it's data from the N others.


::
  
  define trigger{
   trigger_name    Count_active_connections
   matching_rule   True;total_connections=sum(perfs('web-srv*/Http', 'active_connections'))
   hit_action      set_perfdata(self, 'total_connections=%d' % total_connections)
  }





Define and use triggers 
************************

.. note :: More or less up to date

Use the trigger_name directive to link a trigger to a service or host. Example :

::
  
  define service{
        use                             local-service         ; Name of service template to use
        host_name                       localhost
        service_description             Current Load trigger
        check_command                   check_local_load!5.0,4.0,3.0!10.0,6.0,4.0
        trigger_name                    simple_cpu
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
