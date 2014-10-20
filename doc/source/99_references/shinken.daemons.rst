

daemons Package
===============

Diagrams
--------

Simple Daemon class diagram :

.. inheritance-diagram:: shinken.daemon.Daemon
                         shinken.daemons.arbiterdaemon.Arbiter shinken.satellite.BaseSatellite
                         shinken.daemons.brokerdaemon.Broker  shinken.daemons.schedulerdaemon.Shinken  shinken.satellite.Satellite
                         shinken.daemons.pollerdaemon.Poller  shinken.daemons.receiverdaemon.Receiver  shinken.daemons.reactionnerdaemon.Reactionner
   :parts: 3



Simple Interface class diagram :

.. inheritance-diagram:: shinken.daemon.Interface
                         shinken.daemons.receiverdaemon.IStats  shinken.daemons.brokerdaemon.IStats  shinken.daemons.schedulerdaemon.IChecks
                         shinken.daemons.schedulerdaemon.IBroks  shinken.daemons.schedulerdaemon.IStats  shinken.daemons.arbiterdaemon.IForArbiter
                         shinken.satellite.IForArbiter  shinken.satellite.ISchedulers  shinken.satellite.IBroks  shinken.satellite.IStats
   :parts: 3

Package
-------

:mod:`daemons` Package
----------------------

.. automodule:: shinken.daemons
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`arbiterdaemon` Module
---------------------------

.. automodule:: shinken.daemons.arbiterdaemon
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`brokerdaemon` Module
--------------------------

.. automodule:: shinken.daemons.brokerdaemon
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`pollerdaemon` Module
--------------------------

.. automodule:: shinken.daemons.pollerdaemon
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`reactionnerdaemon` Module
-------------------------------

.. automodule:: shinken.daemons.reactionnerdaemon
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`receiverdaemon` Module
----------------------------

.. automodule:: shinken.daemons.receiverdaemon
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`schedulerdaemon` Module
-----------------------------

.. automodule:: shinken.daemons.schedulerdaemon
    :members:
    :undoc-members:
    :show-inheritance:

