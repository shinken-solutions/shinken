.. _tuning/tuning:

========================================
 Tuning Shinken For Maximum Performance
========================================


Introduction
=============

So you've finally got Shinken up and running and you want to know how you can tweak it a bit. Tuning Shinken to increase performance can be necessary when you start monitoring a large number (> 10,000) of hosts and services. Here are the common optimization paths.


Designing your installation for scalability
============================================

Planning a large scale Shinken deployments starts before installing Shinken and monitoring agents.

:ref:`Scaling Shinken for large deployments <advanced/scaling-shinken>`


Optimization Tips:
===================

Graph your shinken server performance
  In order to keep track of how well your installation handles load over time and how your configuration changes affect it, you should be graphing several important statistics. This is really, really, really useful when it comes to tuning the performance of an installation. Really. Information on how to do this can be found in :ref:`Graphing Performance Info With MRTG <tuning/mrtggraphs>` and :ref:`Internals monitoring <advanced/internals-monitoring>`.

Check service latencies to determine best value for maximum concurrent checks
  Nagios can restrict the number of maximum concurrently executing service checks to the value you specify with the :ref:`max_concurrent_checks <advanced/unused-nagios-parameters#max_concurrent_checks>` option. This is good because it gives you some control over how much load Nagios will impose on your monitoring host, but it can also slow things down. If you are seeing high latency values (> 10 or 15 seconds) for the majority of your service checks. That's not Shinken's fault _ its yours. Under ideal conditions, all service checks would have a latency of 0, meaning they were executed at the exact time that they were scheduled to be executed. However, it is normal for some checks to have small latency values. I would recommend taking the minimum number of maximum concurrent checks reported when running Shinken with the _s command line argument and doubling it. Keep increasing it until the average check latency for your services is fairly low. More information on service check scheduling can be found :ref:`Service and Host Check Scheduling <advanced/checkscheduling>` here.

Use passive checks when possible
  The overhead needed to process the results of :ref:`passive checks <thebasics/passivechecks>` is much lower than that of “normal" active checks, so make use of that piece of info if you're monitoring a slew of services. It should be noted that passive service checks are only really useful if you have some external application doing some type of monitoring or reporting, so if you're having Nagios do all the work, this won't help things.

Avoid using interpreted plugins
  One thing that will significantly reduce the load on your monitoring host is the use of compiled (C/C++, etc.) plugins rather than interpreted script (Perl, etc) plugins. While Perl scripts and such are easy to write and work well, the fact that they are compiled/interpreted at every execution instance can significantly increase the load on your monitoring host if you have a lot of service checks. If you want to use Perl plugins, consider compiling them into true executables using perlcc(1) (a utility which is part of the standard Perl distribution).

Optimize host check commands
  If you're checking host states using the **check_ping** plugin you'll find that host checks will be performed much faster if you break up the checks. Instead of specifying a max_attempts value of 1 in the host definition and having the **check_ping** plugin send 10 "ICMP" packets to the host, it would be much faster to set the max_attempts value to 10 and only send out 1 "ICMP" packet each time. This is due to the fact that Nagios can often determine the status of a host after executing the plugin once, so you want to make the first check as fast as possible. This method does have its pitfalls in some situations (i.e. hosts that are slow to respond may be assumed to be down), but you'll see faster host checks if you use it. Another option would be to use a faster plugin (i.e. **check_fping**) as the host_check_command instead of **check_ping**.

Don't use aggressive host checking
  Unless you're having problems with Shinken recognizing host recoveries, I would recommend not enabling the :ref:`use_aggressive_host_checking <advanced/unused-nagios-parameters#use_aggressive_host_checking>` option. With this option turned off host checks will execute much faster, resulting in speedier processing of service check results. However, host recoveries can be missed under certain circumstances when this it turned off. For example, if a host recovers and all of the services associated with that host stay in non-OK states (and don't "wobble" between different non-OK states), Shinken may miss the fact that the host has recovered. A few people may need to enable this option, but the majority don't and I would not recommend using it unless you find it necessary.

Optimize hardware for maximum performance
  Hardware performance shouldn't be an issue unless:

    * you're monitoring thousands of services
    * you are writing to a metric database such as RRDtool or Graphite. Disk access will be a very important factor.
    * you're doing a lot of post-processing of performance data, etc. Your system configuration and your hardware setup are going to directly affect how your operating system performs, so they'll affect how Shinken performs. The most common hardware optimization you can make is with your hard drives, RAID, do not update attributes for access-time/write-time.

  Shinken needs quite a bit of memory which is pre-allocated by the Python processes.

Move your Graphite metric databases to dedicated servers
  Use multiple carbon-relay and carbon-cache daemons to split the load on a single server.

Control how much concurrent checks are executed
  Running too much concurrent checks can have negative side effects, firstly because it implies a high context switch ratio, but also because it generates contention on internal queues. This may not only slow down the service, but also in extreme cases, result in memory leaks. It is highly discourage to set poller's or reactionner's `max_q_size` to *0*. If the checks are too slow to execute, either follow the tips above, or add some more poller or reactionners, depending on the contention. On heavily loaded architectures, fine tuning `max_workers`, `processes_by_worker`, and `q_factor` or `max_q_size` may have significant effects.

Rate limit broks and results
  With big environments where pollers and reactionners manage many conurrent checks, notifications and event handlers, a huge number of results may be returned at once, which may result in memory blast in the scheduler because it has to deseriajize enormous data structures, and make the whole scheduler machine crash. The same effect may be noted on the broker that may fetch huge broks lists. In such environments it is highly advised to rate limit poller and reactionners results using the `results_batch` service parameter, and on the broker using the `broks_batch`.

Memory watchdog (harakiri)
  If the services memory consumption goes to high, it may crash the whole machine. As explained in chapter above, this may happen in big environments if no control is made on the shinken services, or if the tuning is not well enough. To avoid crashing the whole machine, it is often preferable to automatically restart the service passed a given memory consumption. This may be activated by setting the `harakiri_threshold` parameters on the relevant shinken services. Note that `harakiri` is only active if `graceful_enabled` is set to `1` in daemon's ini file.
