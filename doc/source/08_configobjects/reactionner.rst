.. _configobjects/reactionner:

=======================
Reactionner Definition
=======================


Description
============

The Reactionner daemon is in charge of notifications and launching event_handlers. There can be more than one Reactionner.


Definition Format
==================

Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.

=================== ========================
define reactionner{
reactionner_name    *reactionner_name*
address             *dns name of ip address*
port                *port*
spare               *[0,1]*
realm               *realm name*
manage_sub_realms   *[0,1]*
modules             *modules*
min_workers         *workers*
max_workers         *workers*
processes_by_worker *processes*
max_q_size          *items*
q_factor            *factor*
results_batch       *count*
harakiri_threshold  *memory*
}
=================== ========================


Example Definition:
====================

::

  define reactionner{
      reactionner_name      Main-reactionner
      address               node1.mydomain
      port                  7769
      spare                 0
      realm                 All

      # Optional parameters
      manage_sub_realms     0   ; Does it take jobs from schedulers of sub-Realms?
      min_workers           1   ; Starts with N processes (0 = 1 per CPU)
      max_workers           15  ; No more than N processes (0 = 1 per CPU)
      polling_interval      1   ; Get jobs from schedulers each 1 second
      timeout               3   ; Ping timeout
      data_timeout          120 ; Data send timeout
      max_check_attempts    3   ; If ping fails N or more, then the node is dead
      check_interval        60  ; Ping node every minutes
      reactionner_tags      tag1
      modules               module1,module2
  }


Variable Descriptions
======================

reactionner_name
  This variable is used to identify the *short name* of the reactionner which the data is associated with.

address
  This directive is used to define the address from where the main arbiter can reach this reactionner. This can be a DNS name or a IP address.

port
  This directive is used to define the TCP port used bu the daemon. The default value is *7772*.

spare
  This variable is used to define if the reactionner must be managed as a spare one (will take the conf only if a master failed). The default value is *0* (master).

realm
  This variable is used to define the :ref:`realm <configobjects/realm>` where the reactionner will be put. If none is selected, it will be assigned to the default one.

manage_sub_realms
  This variable is used to define if the poller will take jobs from scheduler from the sub-realms of it's realm. The default value is *1*.

modules
  This variable is used to define all modules that the reactionner will load.

reactionner_tags
  This variable is used to define the checks the reactionner can take. If no reactionner_tags is defined, reactionner  will take all untagged notifications and event handlers. If at least one tag is defined, it will take only the checks that are also tagged like it.

By default, there is no reactionner_tag, so reactionner can take all untagged notification/event handlers (default).

min_workers
  This variable controls the minimum number of worker processes to start. Workers are responsible for launching checks, notifications and event handlers. Each worker manages `processes_by_worker` processes (currently this variable has no effect). If set to *0*, this will default to one process per processor core.

min_workers
  This variable controls the maximum number of worker processes to start. Workers are responsible for launching checks, notifications and event handlers. Each worker manages `processes_by_worker` processes (currently, the maximum number). If set to *0*, this will default to one process per processor core.

processes_by_worker
  This variable controls how many concurrent checks, notifications, event handlers... are managed by a single worker.

max_q_size
  This variable controls the maximum number of checks notifications or event handlers a reactionner can enqueue. If set to *0*, the queue is unlimited. If set to an integer value, this will define the maximum number a reactionner may ask to the scheduler. By default, it set to *0*, and `q_factor` is used. If `max_q_size` is defined, it has precedence.

q_factor
  This variable controls the maximum number of notifications or event handlers a reactionner can enqueue. The maximum number of items is calculated with the formula `max_workers * processes_by_worker * q_factor`. So `max_q_size` is a fixed value, `q_factor` is dynamic. It defaults to `3`.

results_batch
  This variable controls results return rate limiting. If set to *0* (default), there is no limit, and all available results are returned to scheduler at once. If set an integer value, the results are returned batched by `results_batch`.

harakiri_threshold
  This parameter activates a memory watchdog that automatically restarts the service if the used memory raises the threshold. The default unit is the *kB*, but it may be defined with an explicit unit specifier: **M = MB**, **G = GB**. Note that `harakiri` is only active if `graceful_enabled` is set to `1` in daemon's ini file.
