.. _use_shinken_with:


====================
Use Shinken with ...
====================


Shinken interface 
------------------


Administrators need a means to view status data and interact with the system.

If you install Shinken using the :ref:`10 minutes installation <shinken_10min_start>` recommended method, you will have the **Shinken WebUI** installed. But it is not mandatory to use it, and you may prefer another interface. There are open-source and commercial web frontends using the **Livestatus API** or an **SQL backend** available to suit any needs.



Web interfaces 
---------------


The choice of an interface starts with the method of data exchange: Those based on **Livestatus** and those based on an **SQL backend**.

The most responsive interfaces are the native **WebUI** and those based on **Livestatus**. The most scalable and flexible are those based on **Livestatus**.

**SkonfUI** is a discovery and configuration management UI that is **not production ready** and is meant as a beta preview for developers not users. Sorry.



Direct memory access based interface 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  * :ref:`Shinken WebUI <use_with_webui>`, included in the Shinken installation. Previews the Shinken features in an attractive package. Not meant for distributed deployments or scalability.
   

.. image:: /_static/images/shinken_webui.png?480x320
   :scale: 90 %


  
  
  
  


Livestatus based interfaces (Networked API) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  * :ref:`Thruk <use_with_thruk>`


.. image:: /_static/images/thruk.png?480x320
   :scale: 90 %


  * :ref:`Multisite <use_with_multisite>`


.. image:: /_static/images/multisite.png?480x320
   :scale: 90 %


  * Complimentary module: :ref:`Nagvis <use_with_nagvis>` (Graphical representation)


.. image:: /_static/images/nagivs.jpg?480x320
   :scale: 90 %





Pickle based data export (Network) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  * Complimentary module: :ref:`Graphite <use_with_graphite>` 
  *  *Note: Integrated out-of-the-box in :ref:`Shinken WebUI <use_with_webui>`*



Other 
~~~~~~

  * Complimentary module: :ref:`PNP4Nagios <use_with_pnp>` (Graphing interface)


.. image:: /_static/images/pnp.png?480x320
   :scale: 90 %





Deprecated: Flat file export 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  * :ref:`Old CGI & VShell <use_with_old_cgi_and_vshell>` *Note: The Nagios CGI web interface is deprecated.*


.. image:: /_static/images/nagios.jpg?480x320
   :scale: 90 %





Which one is right for me? 
---------------------------


Try them out and see which one fits best; this is especially easy with the Shinken WebUI and the Livestatus based interfaces.

  * For users just starting out with small to medium installations, **Thruk** or **Shinken's WebUI** are good choices;
  * For maximum scalability, intuitive UI and a solid feature set **Multisite** is recommended. **Thruk** is perl/PHP based UI that is very feature complete which also provides some scalability.
