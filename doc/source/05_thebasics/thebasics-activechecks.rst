.. _thebasics-activechecks:




===============
 Active Checks 
===============



Introduction 
=============


Shinken is capable of monitoring hosts and services in two ways: actively and passively. Passive checks are described :ref:`elsewhere <thebasics-passivechecks>`, so we'll focus on active checks here. Active checks are the most common method for monitoring hosts and services. The main features of actives checks are as follows:

  * Active checks are initiated by the Shinken process
  * Active checks are run on a regularly scheduled basis



How Are Active Checks Performed? 
=================================




.. image:: /_static/images///official/images/activechecks.png
   :scale: 90 %



Active checks are initiated by the check logic in the Shinken daemon. When Shinken needs to check the status of a host or service it will execute a plugin and pass it information about what needs to be checked. The plugin will then check the operational state of the host or service and report the results back to the Shinken daemon. Shinken will process the results of the host or service check and take appropriate action as necessary (e.g. send notifications, run event handlers, etc).

More information on how plugins work can be found :ref:`here <thebasics-plugins>`.



When Are Active Checks Executed? 
=================================


Active check are executed:

  * At regular intervals, as defined by the "check_interval" and "retry_interval" options in your host and service definitions
  * On-demand as needed

Regularly scheduled checks occur at intervals equaling either the "check_interval" or the "retry_interval" in your host or service definitions, depending on what :ref:`type of state <thebasics-statetypes>` the host or service is in. If a host or service is in a HARD state, it will be actively checked at intervals equal to the "check_interval" option. If it is in a SOFT state, it will be checked at intervals equal to the retry_interval option.

On-demand checks are performed whenever Shinken sees a need to obtain the latest status information about a particular host or service. For example, when Shinken is determining the :ref:`reachability <thebasics-networkreachability>` of a host, it will often perform on-demand checks of parent and child hosts to accurately determine the status of a particular network segment. On-demand checks also occur in the :ref:`predictive dependency check <advancedtopics-dependencychecks>` logic in order to ensure Shinken has the most accurate status information.

