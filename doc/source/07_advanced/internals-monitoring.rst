.. _advanced/internals-monitoring:

================================
 Shinken internals monitoring
================================


Introduction
=============

Shinken is able to expose many internal metrics to a statsd server, allowing to monitor its performances and its operation. It may also be useful to troubleshoot issues.

The metrics export to statsd may be controlled through parameters explained in :ref:`advanced configuration <configuration/configmain-advanced#statsd>`.

The various metrics available in statsd are described in the sections below (the metric names do not mention the configurable prefix nor hostname).

Each metric is specified
- Its name
- Its metric type
- A description telling which information it represents
- The type it is linked to, which may be used to filter the metrics to send to statsd through the `statsd_types` global attribute.

Initial connection timings
==========================

Some services establish connections to continuously exchange data. The metrics below measure the time spent to establish them.

==================== ===== ============================================================ ====
con-init.poller      timer Connection time from broker to poller                        perf
con-init.reactionner timer Connection time from broker to reactionner                   perf
con-init.receiver    timer Connection time from broker to receiver                      perf
con-init.scheduler   timer Connection time from broker/poller/reactcionner to schedule  perf
==================== ===== ============================================================ ====

con-init.poller
  Time spent to establish initial session from the broker to the poller services.

con-init.reactionner
  Time spent to establish initial session from the broker to the reactionner services.

con-init.receiver
  Time spent to establish initial session from the broker to the receiver services.

con-init.scheduler
  Time spent to establish initial session from the broker (to get objects state), the poller and the reactionner (to get actions to execute) to the scheduler services.

Hook timings
============

The shinken services executes code in hooks on different conditions (on a particular point in the workflow, on a timer, on a particular event, ...). The hook events are forwarded to modules for them to execute actions on them. The metrics below expose the time spent to execute those hooks.

======================== ===== ============================================ ====
hook.early_configuration timer Time spent in the `early_configuration` hook perf
hook.get_new_actions     timer Time spent in the `get_new_actions` hook     perf
hook.late_configuration  timer Time spent in the `late_configuration` hook  perf
hook.load_retention      timer Time spent in the `load_retention` hook      perf
hook.read_configuration  timer Time spent in the `read_configuration` hook  perf
hook.save_retention      timer Time spent in the `save_retention` hook      perf
hook.tick                timer Time spent in the `tick` hook                perf
======================== ===== ============================================ ====

hook.early_configuration
  The `early_configuration` hook is executed in the Arbiter daemon after having read the raw configuration, and before starting the deeper parsing operation. This metric exposes the time spent by Arbiter modules to react to this hook.

hook.get_new_actions
  The `get_new_actions` hook is executed in the Scheduler daemon to get actions to execute from modules (actions may be checks, notifications or event handlers). This metric exposes the time spent by Scheduler modules to react to this hook.

hook.late_configuration
  The `late_configuration` hook is executed in the Arbiter daemon after the deeper configuration parsing, and before validating it's correct. This metric exposes the time spent by Arbiter modules to react to this hook.

hook.load_retention
  The `load_retention` hook is executed in the Scheduler and Broker daemons to load retention data using the registered retention module. This metric exposes the time spent by the Schedulers and Brokers to load their retention data.

hook.save_retention
  The `save_retention` hook is executed in the Scheduler and Broker daemons to save retention data using the registered retention module. This metric exposes the time spent by the Schedulers and Brokers to save their retention data.

hook.tick
  All daemons send `tick` event each time they finish to execute a cycle in their main loop. This metric exposes the time spent by modules to react to the `tick` event.

Http communication timings
==========================

Daemons exchange data using remote execution calls based on HTTP/REST APIs. Each of the communications between the daemons are measured (server side). Depending on the request type, various metrics are calculated.

============== ===== ============================================================ ====
http.*.aqulock timer Time spent waiting for a lock (if the operation requires it) perf
http.*.args    timer Time spent parsing the request and its parameters            perf
http.*.calling timer Time spent executing the required procedure                  perf
http.*.global  timer Total time spent to execute the remote procedure             perf
http.*.json    timer Time spent encoding the result                               perf
============== ===== ============================================================ ====

Scheduling metrics
==================

The scheduler operations are measured carefully. Each operation registered in the `recurrent_works` dictionary in the Scheduler daemon is measured its execution time, and the memory increase it generated. Those values are exposed using the metrics below.

====================================== ======= ================================================ =====
loop.*                                 timer   Time spent in the operation                      perf
loop.*.mem                             counter Memory usage evolution involved by the operation perf
core.scheduler.actions.queue           gauge   The actions queue size in the Scheduler          queue
core.scheduler.checks.havetoresolvedep gauge   The check queue size in state havetoresolvedep   queue
core.scheduler.checks.inpoller         gauge   The check queue size in state inpoller           queue
core.scheduler.checks.queue            gauge   The total check queue size in the scheduler      queue
core.scheduler.checks.scheduled        gauge   The check queue size in state scheduled          queue
core.scheduler.checks.timeout          gauge   The check queue size in state timeout            queue
core.scheduler.checks.waitconsume      gauge   The check queue size in state waitconsume        queue
core.scheduler.checks.waitdep          gauge   The check queue size in state waitdep            queue
core.scheduler.checks.zombie           gauge   The check queue size in state zombie             queue
====================================== ======= ================================================ =====

loop.*
  Time spent in a particular step in the scheduler workflow.

loop.*.mem
  The memory variation involved in a particular step in the scheduler workflow.

core.scheduler.actions.queue
  The notifications and eventhandlers queue to be consumed by the reactionners

core.scheduler.checks.havetoresolvedep
  The checks count having havetoresolvedep state in the scheduler. Those checks have dependent checks that have to be checked before taking any decision.

core.scheduler.checks.inpoller
  The checks count having inpoller state in the scheduler. Those checks have been got from by a poller, and the scheduler is waiting for its result.

core.scheduler.checks.queue
  The total queue size on the Scheduler (all states).

core.scheduler.checks.scheduled
  The checks count having scheduled state in the scheduler. Those checks have to be taken by a poller.

core.scheduler.checks.timeout
  The checks count having inpoller state in the scheduler. Those checks have been got from by a poller, and the result did not came in time.

core.scheduler.checks.waitconsume
  The checks count having waitconsume state in the scheduler. Those checks have been got from by a poller, the result came in time and has to be processed by the Scheduler.

core.scheduler.checks.waitconsume
  The checks count having waitdep state in the scheduler. Those checks have dependent checks which result is required.

core.scheduler.checks.zombie
  The checks count having zombie state in the scheduler. Those checks have been totally processed and may be deleted.

Broker specific metrics
=======================

The broker receives broks emitted by the other services to manage its internal representation of the infrastructure, and forwards broks to its modules for them to do the same. The time to manage its state. Those various operation are measured and exposed through the metrics below.

================================= ===== ================================ ====
core.broker.manage-brok           timer Time to manage a single brok     perf
core.broker.put-to-external-queue timer Time to forward broks to modules perf
core.broker.get-new-broks         timer Time to forward broks to modules perf
================================= ===== ================================ ====

core.broker.manage-brok
  When broks are received, they have to be decoded and integrated in the broker configuration to update its representation of the infrastructure. This metric measures the time spent to handle a single brok.

core.broker.put-to-external-queue
  External broker modules do not benefit from broker internal state representation, and have to decode broks to do the work on their own. This metric measures the time spent to forward all the received broks to all the external modules.

core.broker.get-new-broks
  Time to get new broks from other services.

Poller/Reactionner specific metrics
===================================

============================= ======= =========================================================== =====
core.*.manage-returns         timer   Time spent by a satellite to send results to scheduler      perf
core.*.wait-ratio             gauge   **To be documented**                                        perf
core.*.timeout                gauge   **To be documented**                                        perf
core.*.worker-fork.queue-size gauge   The checks/notifications/eventhandlers execution queue size queue
core.*.actions.in             counter The number of new actions got from scheduler                queue
core.*.actions.queue          gauge   The number actions currently queued                         queue
core.*.results.out            counter The number of results returned to scheduler                 queue
core.*.results.queue          gauge   The number results currently queued                         queue
============================= ======= =========================================================== =====

core.*.manage-returns
  Time spent by the poller or reactionners to return the execution results to the scheduler.

core.*.wait-ratio
  **To be documented**

core.*.timeout
  **To be documented**

core.*.worker-fork.queue-size
  The execution queue in the poller/reactionner.

core.*.worker-fork.queue-size
  The execution queue in the poller/reactionner.

core.*.actions.in
  The number of new actions got from scheduler.

core.*.actions.queue
 The number actions currently queued

core.*.results.out
  The number of results returned to scheduler.

core.*.results.queued
  The number results currently queued

Broks related metrics
=====================

Broks transit from the satellites to broker using a pull strategy. So broks are made available on the satellites, and the active Broker fetches them. The exception is the Arbiter that sends its broks directly to the broker. The broks queue on the satellites are monitored through the metrics below.

==================================== ======= ================================================== =====
core.broker.get-new-broks.poller     timer   Time spent to fetch broks from poller              perf
core.broker.get-new-broks.reactionnertimer   Time spent to fetch broks from reactionner         perf
core.broker.get-new-broks.receiver   timer   Time spent to fetch broks from receiver            perf
core.broker.get-new-broks.scheduler  timer   Time spent to fetch broks from scheduler           perf
core.arbiter.broks.in.broker         counter Broks received by the Arbiter from the broker      queue
core.arbiter.broks.in.poller         counter Broks received by the Arbiter from the poller      queue
core.arbiter.broks.in.reactionner    counter Broks received by the Arbiter from the reactionner queue
core.arbiter.broks.in.receiver       counter Broks received by the Arbiter from the receiver    queue
core.arbiter.broks.in.scheduler      counter Broks received by the Arbiter from the scheduler   queue
core.arbiter.broks.queue             counter The broks queue size on the Arbiter                queue
core.broker.broks.queue              counter The broks queue size on the Broker                 queue
core.poller.broks.queue              counter The broks queue size on the Poller                 queue
core.reactionner.broks.queue         counter The broks queue size on the Poller                 queue
core.receiver.broks.queue            counter The broks queue size on the Receiver               queue
core.scheduler.broks.queue           counter The broks queue size on the Receiver               queue
==================================== ======= ================================================== ======

core.broker.get-new-broks.poller
  Time spent by the Broker to download, decode and integrate broks downloaded from the Poller.

core.broker.get-new-broks.reactionner
  Time spent by the Broker to download, decode and integrate broks downloaded from the Reactionner.

core.broker.get-new-broks.receiver
  Time spent by the Broker to download, decode and integrate broks downloaded from the Receiver.

core.broker.get-new-broks.scheduler
  Time spent by the Broker to download, decode and integrate broks downloaded from the Scheduler.

core.broker.arbiter.broks.in.broker
  The broks downloaded by the Arbiter from the Scheduler.

core.arbiter.broks.in.poller
  The broks downloaded by the Arbiter from the Poller

core.arbiter.broks.in.reactionner
  The broks downloaded by the Arbiter from the Reactionner

core.arbiter.broks.in.receiver
  The broks downloaded by the Arbiter from the Receiver

core.arbiter.broks.in.scheduler
  The broks downloaded by the Arbiter from the Scheduler

core.arbiter.broks.queue
  The total broks queue size in the Arbiter

core.broker.broks.queue
  The total broks queue size in the Broker

core.poller.broks.queue
  The total broks queue size in the Poller

core.reactionner.broks.queue
  The total broks queue size in the Reactionner

core.receiver.broks.queue
  The total broks queue size in the Receiver

core.scheduler.broks.queue
  The total broks queue size in the Scheduler

External commands related metrics
=================================

The external commands may emitted by any service or module. They may also be externally received and transferred by the Arbiter or the Receiver. When an external command is emitted, it goes up to the Arbiter which is able to decide to which service it should be routed. Each service is monitorred its external command queue which are exosed by the metrics below.

======================================== ===== ===================================================== ======
core.arbiter.external-commands.queue     gauge The external commands queue length on the Arbiter     queue
core.broker.external-commands.queue      gauge The external commands queue length on the Broker      queue
core.poller.external-commands.queue      gauge The external commands queue length on the Poller      queue
core.reactionner.external-commands.queue gauge The external commands queue length on the Reactionner queue
core.receiver.external-commands.queue    gauge The external commands queue length on the Receiver    queue
core.scheduler.external-commands.queue   gauge The external commands queue length on the Scheduler   queue
======================================== ===== ===================================================== =====

core.arbiter.external-commands.queue
  The external commands queue length on the Arbiter

core.broker.external-commands.queue
  The external commands queue length on the Broker

core.poller.external-commands.queue
  The external commands queue length on the Poller

core.reactionner.external-commands.queue
  The external commands queue length on the Reactionner

core.receiver.external-commands.queue
  The external commands queue length on the Receiver

core.scheduler.external-commands.queue
  The external commands queue length on the Scheduler

Memory related metrics
======================

All services are monitored their memory usage through the metrics below.

==================== ===== ================================================ ======
core.arbiter.mem     gauge The total memory used by the Arbiter service     system
core.broker.mem      gauge The total memory used by the Broker service      system
core.poller.mem      gauge The total memory used by the Poller service      system
core.reactionner.mem gauge The total memory used by the Reactionner service system
core.receiver.mem    gauge The total memory used by the Receiver service    system
core.scheduler.mem   gauge The total memory used by the Scheduler service   system
==================== ===== ================================================ ======

core.arbiter.mem
  The total memory used by the Arbiter service

core.broker.mem
  The total memory used by the Broker service

core.poller.mem
  The total memory used by the Poller service

core.reactionner.mem
  The total memory used by the Reactionner service

core.receiver.mem
  The total memory used by the Receiver service

core.scheduler.mem
  The total memory used by the Scheduler service

Managed objects
===============

Service that hold configuration objects are monitored the objects they manage through the metrics below. Note the the Arbiter holds the whole confugiration, but the schedulers may havo only a portion of it if multible active schedulers are used.

============================ ===== =========================================================== =====
core.arbiter.commands        gauge The number of Command objects managed by the Arbiter        queue
core.arbiter.contactgroups   gauge The number of Contactgroup objects managed by the Arbiter   queue
core.arbiter.contacts        gauge The number of Contact objects managed by the Arbiter        queue
core.arbiter.hostgroups      gauge The number of Hostgroup objects managed by the Arbiter      queue
core.arbiter.hosts           gauge The number of Host objects managed by the Arbiter           queue
core.arbiter.servicegroups   gauge The number of Servicegroup objects managed by the Arbiter   queue
core.arbiter.services        gauge The number of Service objects managed by the Arbiter        queue
core.scheduler.commands      gauge The number of Command objects managed by the Scheduler      queue
core.scheduler.contactgroups gauge The number of Contactgroup objects managed by the Scheduler queue
core.scheduler.contacts      gauge The number of Contact objects managed by the Scheduler      queue
core.scheduler.hostgroups    gauge The number of Hostgroup objects managed by the Scheduler    queue
core.scheduler.hosts         gauge The number of Host objects managed by the Scheduler         queue
core.scheduler.servicegroups gauge The number of Servicegroup objects managed by the Scheduler queue
core.scheduler.services      gauge The number of Service objects managed by the Scheduler      queue
============================= ===== ========================================================== =====

core.arbiter.commands
  The number of Command objects managed by the Arbiter

core.arbiter.contactgroups
  The number of Contactgroup objects managed by the Arbiter

core.arbiter.contacts
  The number of Contact objects managed by the Arbiter

core.arbiter.hostgroups
  The number of Hostgroup objects managed by the Arbiter

core.arbiter.hosts
  The number of Host objects managed by the Arbiter

core.arbiter.servicegroups
  The number of Servicegroup objects managed by the Arbiter

core.arbiter.services
  The number of Service objects managed by the Arbiter

core.scheduler.commands
  The number of Command objects managed by the Scheduler

core.scheduler.contactgroups
  The number of Contactgroup objects managed by the Scheduler

core.scheduler.contacts
  The number of Contact objects managed by the Scheduler

core.scheduler.hostgroups
  The number of Hostgroup objects managed by the Scheduler

core.scheduler.hosts
  The number of Host objects managed by the Scheduler

core.scheduler.servicegroups
  The number of Servicegroup objects managed by the Scheduler

core.scheduler.services
  The number of Service objects managed by the Scheduler
