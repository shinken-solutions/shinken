.. _use_with_pnp:

.. _use_with_pnp#using_shinken_with_pnp4nagios:


===========================
Use Shinken with PNP4Nagios
===========================

PNP4Nagios 
-----------



.. image:: /_static/images/pnp.png?640x480
   :scale: 90 %


  * Homepage: http://docs.pnp4nagios.org/pnp-0.6/start
  * Screenshots: http://docs.pnp4nagios.org/pnp-0.6/gallery/start
  * Description: "PNP is an addon to Nagios which analyzes performance data provided by plugins and stores them automatically into RRD-databases (Round Robin Databases, see `RRD Tool`_)."
  * License: GPL v2

  * Shinken dedicated forum: http://www.shinken-monitoring.org/forum/index.php/board,9.0.html


.. _use_with_pnp#install_pnp4nagios_automatically:


Install PNP4Nagios automatically 
---------------------------------


You can use the Shinken install script to install everything automatically (if your distro is supported):
  
::

  
  ./install -a pnp4nagios


By default PNP4Nagios is installed in ''/usr/local/pnp4nagios''.
If you prefer another location, edit ''PNPPREFIX'' in ''install.d/shinken.conf''.



Install PNP4Nagios manually 
----------------------------


See `PHP4Nagios installation`_ documentation.

In a nutshell:
  
::

  ./configure --with-nagios-user=shinken --with-nagios-group=shinken
  make all
make fullinstall

Don't forget to make PNP4Nagios' npcd daemon to start at boot, and launch it:
  
::

  chkconfig --add npcd # On RedHat-like
  update-rc.d npcd defaults # On Debian-like
/etc/init.d/npcd start



Configure npcdmod 
~~~~~~~~~~~~~~~~~~


The module **npcdmod** is in charge to export performance data from Shinken to PNP.

  
::

  define module{
  
::

       module_name       NPCDMOD
       module_type       npcdmod
       config_file       <PATH_TO_NPCD.CFG>
}

Don't forget to replace "<PATH_TO_NPCD.CFG>" with your own value; By default something like ''/usr/local/pnp4nagios/etc/npcd.cfg''.



Enable it 
~~~~~~~~~~


Edit ''/etc/shinken/shinken-specific.cfg'' and find the object **Broker** to add above defined "NPCDMOD" to its **modules** line:

  
::

  define broker{
  
::

       broker_name      broker-1
  [...]
  
::

       modules          Simple-log,NPCDMOD
}

Edit ''/etc/shinken/shinken-specific.cfg'' and find the object **WebUI** to add above defined "PNP_UI" to its **modules** line:

  
::

  define broker{
  
::

       module_name      WebUI
  [...]
  
::

       modules          Apache_passwd,ActiveDir_UI,Cfg_password,PNP_UI
}

Then restart broker :
  
::

  # /etc/init.d/shinken-broker restart</code>
  


Share users with Thruk 
-----------------------

  
  Edit ''/etc/httpd/conf.d/pnp4nagios.conf'' (RedHat path) and replace AuthName and AuthUserFile with:
  <code>
  AuthName "Thruk Monitoring"
  AuthUserFile /etc/thruk/htpasswd


Then restart Apache:
  
::

  
  service httpd restart




Set the action_url option 
--------------------------


In order to get the graphs displayed in :ref:`Thruk <use_with_thruk>`, you need to set the **action_url** option in :ref:`host <host>` and :ref:`service <service>` definitions, and it must include the string "/pnp4nagios/" (`Thruk doc`_).

If you want the link and the graph for all hosts and services, you could set the option directly in the default templates, in ''templates.cfg'':
  
::

  define host{
  
::

        name                            generic-host
  [...]
  
::

        process_perf_data               1
  [...]
  
::

        #action_url                     http://<PNP4NAGIOS_HOST>/pnp4nagios/graph?host=$HOSTNAME$
        # If not an absolute URI, it must be relative to /cgi-bin/thruk/, not /thruk/!
        action_url                      ../../pnp4nagios/graph?host=$HOSTNAME$
  [...]
  define service{
  
::

        name                            generic-service
  [...]
  
::

        process_perf_data               1
  [...]
  
::

        #action_url                      http://<PNP4NAGIOS_HOST>/pnp4nagios/graph?host=$HOSTNAME$&srv=$SERVICEDESC$
        # If not an absolute URI, it must be relative to /cgi-bin/thruk/, not /thruk/!
        action_url                      ../../pnp4nagios/graph?host=$HOSTNAME$&srv=$SERVICEDESC$
  
  
Don't forget to replace "<PNP4NAGIOS_HOST>" with the server IP/name running PNP4Nagios (Don't replace $HOSTNAME$ and $SERVICEDESC$!)

Make sure to also have **process_perf_data** set to **1** for both hosts and services.



Link back to Thruk 
-------------------


Ask PNP4Nagios to link to ''/thruk/cgi-bin'' rather than ''/nagios/cgi-bin'':
  
::

  
  sed -i -e 's,/nagios/cgi-bin,/thruk/cgi-bin,' /opt/pnp4nagios/etc/config_local.php




Enjoy it 
---------


Restart shinken-arbiter and you are done.
  
::

  /etc/init.d/shinken-arbiter restart</code>

.. _PHP4Nagios installation: http://docs.pnp4nagios.org/pnp-0.6/install 
.. _Thruk doc: http://www.thruk.org/documentation.html#_pnp4nagios_graphs
.. _RRD Tool: http://www.rrdtool.org/
