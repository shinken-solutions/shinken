.. _use_with_thruk:



======================
Use Shinken with Thruk
======================

Thruk
-----




.. image:: /_static/images/thruk.png?640x480
   :scale: 90 %


  * Homepage: http://www.thruk.org/
  * Screenshots: http://www.thruk.org/images/screenshots/screenshots.html
  * Description: "Thruk is an independent multibackend monitoring webinterface which currently supports Nagios, Icinga and Shinken as backend using the Livestatus addon. It is designed to be a "dropin" replacement. The target is to cover 100% of the original features plus additional enhancements for large installations."
  * License: GPL v2

  * Shinken dedicated forum: http://www.shinken-monitoring.org/forum/index.php/board,7.0.html


.. _use_with_thruk#install_thrukd:


Install Thruk 
--------------


See `Thruk installation`_ documentation.

Note: if you're using SELinux, also run:

::

  chcon -t httpd_sys_script_exec_t /usr/share/thruk/fcgid_env.sh
  chcon -t httpd_sys_script_exec_t /usr/share/thruk/script/thruk_fastcgi.pl
  chcon -R -t httpd_sys_content_rw_t /var/lib/thruk/
  chcon -R -t httpd_sys_content_rw_t /var/cache/thruk/
  chcon -R -t httpd_log_t /var/log/thruk/
  setsebool -P httpd_can_network_connect on


.. _use_with_thruk#using_shinken_with_thruk:


Using Shinken with Thruk 
-------------------------


Thruk communicates with Shinken through the LiveStatus module. If you used the sample configuration, everything should be ready already. :)

You can review the configuration using the two following steps.


Enable Livestatus module 
~~~~~~~~~~~~~~~~~~~~~~~~~


See :ref:`enable Livestatus module <enable_livestatus_module>`.



Declare Shinken peer in Thruk 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Edit ''/etc/thruk/thruk_local.conf'' and declare the Shinken peer:

::

    enable_shinken_features = 1
    <Component Thruk::Backend>
        <peer>
            name   = External Shinken
            type   = livestatus
            <options>
                peer    = 127.0.0.01:50000
            </options>
            # Uncomment the following lines if you want to configure shinken through Thruk
            #<configtool>
            #    core_type      = shinken
            #    core_conf      = /etc/shinken/shinken.cfg
            #    obj_check_cmd  = service shinken check
            #    obj_reload_cmd = service shinken restart
            #</configtool>
        </peer>
    </Component>

Or use the backend wizard which starts automatically upon first installation.

Don't forget to change the 127.0.0.1 with the IP/name of your broker if it is installed on an different host, or if you are using a distributed architecture with multiple brokers!


Credit Shinken in the webpages title :-) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  Edit ''/etc/thruk/thruk.conf'':

::

  title_prefix = Shinken+Thruk-




Configure users 
~~~~~~~~~~~~~~~~


Passwords are stored in ''/etc/thruk/htpasswd'' and may be modified using the ''htpasswd'' command from Apache:

::

  htpasswd /etc/thruk/htpasswd your_login


User permissions: modify ''templates.cfg:generic-contact'':

::

      # I couldn't manage to get Thruk-level permissions to work, let's use Shinken admins privileges
      can_submit_commands             0

and define some users as admins in the Shinken configuration:
  
::

  define contact {

    # ...

    use             generic-contact
    is_admin        1

    # ...
  }


Allow Thruk to modify its configuration file:

::

  chgrp apache /etc/thruk/cgi.cfg
  chmod g+w /etc/thruk/cgi.cfg


Set permissions for your users in Config Tool > User Settings > authorized_for_...


Using PNP4Nagios with Thruk 
----------------------------


See :ref:`PNP4Nagios <use_with_pnp>`.

.. _Thruk installation: http://www.thruk.org/documentation.html#_installation
