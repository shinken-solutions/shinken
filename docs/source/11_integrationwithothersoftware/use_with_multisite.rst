.. _use_with_multisite:


==========================
Use Shinken with Multisite
==========================


Check_MK Multisite 
-------------------




.. image:: /_static/images/multisite.png?640x480
   :scale: 90 %


  * Homepage: http://mathias-kettner.de/check_mk.html
  * Screenshots: http://mathias-kettner.de/check_mk_multisite_screenshots.html
  * Description: "A new general purpose Nagios-plugin for retrieving data."
  * License: GPL v2

  * Shinken dedicated forum: http://www.shinken-monitoring.org/forum/index.php/board,10.0.html


Using Shinken with Multisite 
-----------------------------


Multisite communicates with Shinken through the LiveStatus module. If you used the sample configuration, everything should be ready already. :)

You can review the configuration using the following steps.



Enable Livestatus module 
~~~~~~~~~~~~~~~~~~~~~~~~~


See :ref:`enable Livestatus module <enable_livestatus_module>`.



Configure Multisite 
~~~~~~~~~~~~~~~~~~~~


Latest versions of Multisite are included into Check_MK, which must be fully installed although we will only use the web interface.

To install and configure Multisite manually, follow `instructions at MK website`_.

Best choice is to use Shinken **:ref:`install script <shinken_10min_start#method_1the_easy_way>`** (In Shinken versions >1.0). With addons installation option (''./install -a multisite'') it is fast and easy to install and configure it as Multisite's default site.

.. warning::  If you get some error installing Multisite related with unknown paths ("can not find Multisite_versionXXX") perhaps you must edit ''init.d/shinken.conf'' file and adjust MKVER variable (search for "export MKVER") with current stable available version of Check_MK as stated on MK website.




Check_MK install quick guide 
*****************************


  - Install check_mk: Detailed `instructions`_ there. Shell driven install with a lot of questions related with Check_mk install paths and integration with Apache and existing "Nagios". For Shinken some default answers must be changed to accomodate Shinken install.
  - Edit config file ''multisite.mk'', usually in ''/etc/check_mk'', to insert a new site pointing to Shinken and write Livestatus socket address as declared at :ref:`Shinken's Livestatus module <enable_livestatus_module>`. Socket may also be an unix socket ("unix:/some/other/path").
  - Restart Apache.

''/etc/check_mk/multisite.mk'':
  
::

  sites = {
  
::

  "munich": {
      "alias": "Munich"
  },
  "Shinken": {
     "alias":          "Shinken",
     "socket":         "tcp:127.0.0.1:50000",
     "url_prefix":     "http://shinken.fqdn/",
   },
}
.. note::  Replace "shinken.fqdn" with the complete URI to reach Shinken host from browser (not 127.0.0.1!). Used by PNP4Nagios's mouse-over images.

If you plan to use Multisite only as web UI no more configuration is needed. Also you can disable WATO (Web Administration TOol) by including the line **wato_enabled = False** in ''multisite.mk''.
.. _instructions at MK website: http://mathias-kettner.de/checkmk_multisite_setup.html
.. _instructions: http://mathias-kettner.de/checkmk_getting_started.html
