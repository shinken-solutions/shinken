.. _medium/snapshots:

=========================
Snapshots
=========================


Overview 
=========

Definition 
-----------

Snapshots are on demand command launch to dump a larger state of one host/service when there is a problem in a period when the administrator is not available (night). It to not enter to the notification logic, it's only to export a quick-view/snapshot of the element during a problem (like a list of processes) into a databse so the admin will be able to look at the problem with more data when he/she will came back.


Data routing of Snapshots commands
--------------------------------------

Snapshots are like event handlers. They are launched from the reactionner with the same properties (reactionner_tag) than the event handlers. It's up to the command to connect to the distant host and grab data. The scheduler is grabbing the output and create a specific brok object from it so the brokers can get them and export it to modules.


Configuration Reference
------------------------

Snapshots are command that can be called by hosts and/or services. They are disabled by default, and should be set to named hosts/services. It's a very bad idea to enable them on all hosts and services as it will add lot of load on your distant hosts :)


Exporting the data
------------------

The data is exported from the scheduler as a brok (host_snapshot_brok/service_snapshot_brok) and can be grab by broker modules to exporting to somewhere (like database, flat file, whatever you prefer).
