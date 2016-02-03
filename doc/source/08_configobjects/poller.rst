.. _configobjects/poller:

==================
Poller Definition
==================


Description
============

The Poller object is a way to the Arbiter daemons to talk with a scheduler and give it hosts to manage. They are in charge of launching plugins as requested by schedulers. When the check is finished they return the result to the schedulers. There can be many pollers.

The Poller definition is optional. If no poller is defined, Shinken will "create" one for the user. There will be no high availability for it (no spare), and will use the default port in the server where the deamon is launched.


Definition Format
==================

Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.

=================== ========================
define poller{
poller_name         *poller_name*
address             *dns name of ip address*
port                *port*
spare               *[0,1]*
realm               *realm name*
manage_sub_realms   *[0,1]*
poller_tags         *poller_tags*
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

  define poller{
      poller_name          Europe-poller
      address              node1.mydomain
      port                 7771
      spare                0

      # Optional parameters
      manage_sub_realms    0
      poller_tags          DMZ, Another-DMZ
      modules              module1,module2
      realm                Europe
      min_workers          0    ; Starts with N processes (0 = 1 per CPU)
      max_workers          0    ; No more than N processes (0 = 1 per CPU)
      processes_by_worker  256  ; Each worker manages N checks
      polling_interval     1    ; Get jobs from schedulers each N seconds
  }


Variable Descriptions
======================

poller_name
  This variable is used to identify the *short name* of the poller which the data is associated with.

address
  This directive is used to define the address from where the main arbiter can reach this poller. This can be a DNS name or a IP address.

port
  This directive is used to define the TCP port used bu the daemon. The default value is *7771*.

spare
  This variable is used to define if the poller must be managed as a spare one (will take the conf only if a master failed). The default value is *0* (master).

realm
  This variable is used to define the :ref:`realm <configobjects/realm>` where the poller will be put. If none is selected, it will be assigned to the default one.

manage_sub_realms
  This variable is used to define if the poller will take jobs from scheduler from the sub-realms of it's realm. The default value is *0*.

poller_tags
  This variable is used to define the checks the poller can take. If no poller_tags is defined, poller will take all untagged checks. If at least one tag is defined, it will take only the checks that are also tagged like it.
  By default, there is no poller_tag, so poller can take all untagged checks (default).

modules
  This variable is used to define all modules that the scheduler will load.

min_workers
  This variable controls the minimum number of worker processes to start. Workers are responsible for launching checks, notifications and event handlers. Each worker manages `processes_by_worker` processes (currently this variable has no effect). If set to *0*, this will default to one process per processor core.

min_workers
  This variable controls the maximum number of worker processes to start. Workers are responsible for launching checks, notifications and event handlers. Each worker manages `processes_by_worker` processes (currently, the maximum number). If set to *0*, this will default to one process per processor core.

processes_by_worker
  This variable controls how many concurrent checks, notifications, event handlers... are managed by a single worker.

max_q_size
  This variable controls the maximum number of checks a poller can enqueue. If set to *0*, the queue is unlimited. If set to an integer value, this will define the maximum number a poller may ask to the scheduler. By default, it set to *0*, and `q_factor` is used. If `max_q_size` is defined, it has precedence.

q_factor
  This variable controls the maximum number of checks a poller can enqueue. The maximum number of items is calculated with the formula `max_workers * processes_by_worker * q_factor`. So `max_q_size` is a fixed value, `q_factor` is dynamic. It defaults to `3`.

results_batch
  This variable controls results return rate limiting. If set to *0* (default), there is no limit, and all available results are returned to scheduler at once. If set an integer value, the results are returned batched by `results_batch`.

harakiri_threshold
  This parameter activates a memory watchdog that automatically restarts the service if the used memory raises the threshold. The default unit is the *kB*, but it may be defined with an explicit unit specifier: **M = MB**, **G = GB**. Note that `harakiri` is only active if `graceful_enabled` is set to `1` in daemon's ini file.
