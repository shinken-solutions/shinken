objects Package
===============

Diagrams
--------

Simple Item class diagram :

.. inheritance-diagram:: shinken.objects.item.Item  shinken.objects.module.Module  shinken.objects.pack.Pack
                         shinken.objects.serviceextinfo.ServiceExtInfo  shinken.objects.hostescalation.Hostescalation
                         shinken.objects.resultmodulation.Resultmodulation  shinken.objects.contact.Contact
                         shinken.objects.serviceescalation.Serviceescalation  shinken.objects.checkmodulation.CheckModulation
                         shinken.objects.config.Config  shinken.objects.host.Host  shinken.objects.command.Command
                         shinken.objects.timeperiod.Timeperiod  shinken.objects.schedulingitem.SchedulingItem
                         shinken.objects.notificationway.NotificationWay  shinken.objects.service.Service
                         shinken.objects.escalation.Escalation  shinken.objects.discoveryrun.Discoveryrun
                         shinken.objects.macromodulation.MacroModulation
                         shinken.objects.servicedependency.Servicedependency  shinken.objects.hostdependency.Hostdependency
                         shinken.satellitelink.SatelliteLink  shinken.schedulerlink.SchedulerLink  shinken.arbiterlink.ArbiterLink  shinken.brokerlink.BrokerLink  shinken.receiverlink.ReceiverLink  shinken.pollerlink.PollerLink
                         shinken.reactionnerlink.ReactionnerLink shinken.objects.matchingitem.MatchingItem
                         shinken.objects.hostextinfo.HostExtInfo  shinken.objects.trigger.Trigger
                         shinken.objects.itemgroup.Itemgroup  shinken.objects.contactgroup.Contactgroup  shinken.objects.hostgroup.Hostgroup
                         shinken.objects.servicegroup.Servicegroup  shinken.objects.realm.Realm
                         shinken.objects.businessimpactmodulation.Businessimpactmodulation shinken.objects.discoveryrule.Discoveryrule
   :parts: 3


Simple Items class diagram :

.. inheritance-diagram:: shinken.objects.item.Items  shinken.objects.module.Modules  shinken.objects.pack.Packs
                         shinken.objects.serviceextinfo.ServicesExtInfo  shinken.objects.hostescalation.Hostescalations
                         shinken.objects.contact.Contacts  shinken.objects.discoveryrun.Discoveryruns
                         shinken.objects.serviceescalation.Serviceescalations  shinken.objects.checkmodulation.CheckModulations
                         shinken.objects.host.Hosts  shinken.objects.command.Commands  shinken.objects.timeperiod.Timeperiods
                         shinken.objects.resultmodulation.Resultmodulations  shinken.objects.notificationway.NotificationWays
                         shinken.objects.service.Services  shinken.objects.macromodulation.MacroModulations
                         shinken.objects.servicedependency.Servicedependencies  shinken.objects.hostdependency.Hostdependencies
                         shinken.objects.escalation.Escalations  shinken.objects.hostextinfo.HostsExtInfo
                         shinken.objects.trigger.Triggers  shinken.objects.itemgroup.Itemgroups  shinken.objects.contactgroup.Contactgroups
                         shinken.objects.hostgroup.Hostgroups  shinken.objects.servicegroup.Servicegroups
                         shinken.objects.discoveryrule.Discoveryrules  shinken.objects.realm.Realms
                         shinken.objects.businessimpactmodulation.Businessimpactmodulations  shinken.satellitelink.SatelliteLinks
                         shinken.schedulerlink.SchedulerLinks  shinken.arbiterlink.ArbiterLinks
                         shinken.brokerlink.BrokerLinks  shinken.receiverlink.ReceiverLinks  shinken.pollerlink.PollerLinks
                         shinken.reactionnerlink.ReactionnerLinks
   :parts: 3


Simple DummyCommand class diagram :

.. inheritance-diagram:: shinken.objects.command.DummyCommand
   :parts: 3

Package
-------

:mod:`objects` Package
----------------------

.. automodule:: shinken.objects
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`businessimpactmodulation` Module
--------------------------------------

.. automodule:: shinken.objects.businessimpactmodulation
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`checkmodulation` Module
-----------------------------

.. automodule:: shinken.objects.checkmodulation
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`command` Module
---------------------

.. automodule:: shinken.objects.command
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`config` Module
--------------------

.. automodule:: shinken.objects.config
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`contact` Module
---------------------

.. automodule:: shinken.objects.contact
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`contactgroup` Module
--------------------------

.. automodule:: shinken.objects.contactgroup
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`discoveryrule` Module
---------------------------

.. automodule:: shinken.objects.discoveryrule
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`discoveryrun` Module
--------------------------

.. automodule:: shinken.objects.discoveryrun
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`escalation` Module
------------------------

.. automodule:: shinken.objects.escalation
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`host` Module
------------------

.. automodule:: shinken.objects.host
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`hostdependency` Module
----------------------------

.. automodule:: shinken.objects.hostdependency
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`hostescalation` Module
----------------------------

.. automodule:: shinken.objects.hostescalation
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`hostextinfo` Module
-------------------------

.. automodule:: shinken.objects.hostextinfo
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`hostgroup` Module
-----------------------

.. automodule:: shinken.objects.hostgroup
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`item` Module
------------------

.. automodule:: shinken.objects.item
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`itemgroup` Module
-----------------------

.. automodule:: shinken.objects.itemgroup
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`macromodulation` Module
-----------------------------

.. automodule:: shinken.objects.macromodulation
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`matchingitem` Module
--------------------------

.. automodule:: shinken.objects.matchingitem
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`module` Module
--------------------

.. automodule:: shinken.objects.module
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`notificationway` Module
-----------------------------

.. automodule:: shinken.objects.notificationway
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`pack` Module
------------------

.. automodule:: shinken.objects.pack
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`realm` Module
-------------------

.. automodule:: shinken.objects.realm
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`resultmodulation` Module
------------------------------

.. automodule:: shinken.objects.resultmodulation
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`schedulingitem` Module
----------------------------

.. automodule:: shinken.objects.schedulingitem
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`service` Module
---------------------

.. automodule:: shinken.objects.service
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`servicedependency` Module
-------------------------------

.. automodule:: shinken.objects.servicedependency
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`serviceescalation` Module
-------------------------------

.. automodule:: shinken.objects.serviceescalation
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`serviceextinfo` Module
----------------------------

.. automodule:: shinken.objects.serviceextinfo
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`servicegroup` Module
--------------------------

.. automodule:: shinken.objects.servicegroup
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`timeperiod` Module
------------------------

.. automodule:: shinken.objects.timeperiod
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`trigger` Module
---------------------

.. automodule:: shinken.objects.trigger
    :members:
    :undoc-members:
    :show-inheritance:

