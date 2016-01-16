.. _integration/graphite:

=========================
Use Shinken with Graphite
=========================


Graphite
=========

  * Homepage: `Graphite`_
  * Screenshots:
  * presentation: http://pivotallabs.com/talks/139-metrics-metrics-everywhere
  * Description: "Graphite is an easy to use scalable time-series database and a web API that can provide raw data for client rendering or server side rendering. It is the evolution of RRDtool."
  * License: GPL v2

  * Shinken dedicated forum: http://www.shinken-monitoring.org/forum/index.php/board,9.0.html
  * Graphite dedicated forum: https://answers.launchpad.net/graphite


Install graphite
=================

The best installation guide is actually `this youtube walkthrough from Jason Dixon`_ (Obfuscurity). There is a `Chef recipe for the above demonstration`_.

See http://graphite.readthedocs.org/en/latest/install.html documentation tells what to install but not how to configure Apache and Django.

See `Installing Graphite version 0.9.8`_ example. Just update for version 0.9.10 it is the exact same installation steps. The vhost example also worked for me, while the wsgi examples did not for me.

Make sure you set the timezone properly in ''/opt/graphite/webapp/graphite/local_settings.py'', for instance:

::

  TIME_ZONE = 'Europe/Paris'</code>


Using Shinken with Graphite
============================


  The Shinken Broker module **graphite** is in charge of exporting performance data from Shinken to the Graphite databases.


Configure graphite module
--------------------------


::

  define module{
      module_name     graphite
      module_type     graphite_perfdata

      # Graphite server / port to use
      # default to localhost:2003
      #host            localhost
      #port            2003

      graphite_data_source    shinken
      ...
  }

Additional list of options for the :ref:`Graphite export module and more in-depth documentation <the_broker_modules#network_based_modules___graphite_graphing>`.


Enable it
----------

Edit ''/etc/shinken/brokers/broker-master.cfg'', and add the graphite module to its **modules** line:


::

  define broker{
       broker_name      broker-1
      [...]
       modules          livestatus,simple-log,webui2,graphite
  }


Use it
-------

With Shinken UI
~~~~~~~~~~~~~~~~


In ''/etc/shinken/modules/ui-graphite.cfg'', configure the URL to your Graphite install.
If you used a graphite_data_source in the ''graphite.cfg'', make sure to specify it here as well.

::

  define module {
      module_name    ui-graphite
      module_type    graphite-webui

      uri                     http://YOURSERVERNAME:8080/
      graphite_data_source    shinken
      ...
  }

Then edit the ''/etc/shinken/modules/webui2.cfg'' file to add *ui-graphite* to the Web UI modules list:

::

  define module {
      module_name         webui2
      module_type         webui2


      modules ui-graphite
      ...
  }

Restart Shinken to take the changes into account.

You have the possibility to use graphite template files. They are located in "templates_path", (from the graphite_webui module)
They are file containing graphite urls with shinken contextual variables.
Ex :

''${uri}render/?width=586&height=308&target=alias(legendValue(${host}.${service}.'user'%2C%22last%22)%2C%22User%22)&target=alias(legendValue(${host}.${service}.'sys'%2C%22last%22)%2C%22Sys%22)&target=alias(legendValue(${host}.${service}.'softirq'%2C%22last%22)%2C%22SoftIRQ%22)&target=alias(legendValue(${host}.${service}.'nice'%2C%22last%22)%2C%22Nice%22)&target=alias(legendValue(${host}.${service}.'irq'%2C%22last%22)%2C%22IRQ%22)&target=alias(legendValue(${host}.${service}.'iowait'%2C%22last%22)%2C%22I%2FO%20Wait%22)&target=alias(legendValue(${host}.${service}.'idle'%2C%22last%22)%2C%22Idle%22)&fgcolor=000000&bgcolor=FFFFFF)&areaMode=stacked&yMax=100''

is used for check_cpu. Split this string using & as a separator to understand it. It's quite easy. Use graphite uri api doc.

Shinken uses the templates that matches the check_command, like pnp does.

.. important::  The suggested configuration below is not final and has just been created, the
documentation needs to be updated for the correct usage of the .graph templates used in WebUI.
There are a number of the already created, see the existing packs to learn how to use them
properly.

Sorry for the inconvenience.


with Thruk
~~~~~~~~~~~

:ref:`Thruk <integration/thruk-usage>` offers a proper integration with PNP, but not with Graphite.
Still, you can use graphite with Thruk. Simply use the **action_url** for your service/host to link toward the graphite url you want. Use HOSTNAME and SERVICEDESC macros.
The action_url icon will be a link to the graph in Thruk UI.
For ex :

'' http://MYGRAPHITE/render/?lineMode=connected&width=586&height=308&_salt=1355923874.899&target=cactiStyle($HOSTNAME$.$SERVICEDESC$.*)&xFormat=%25H%3A%25M&tz=Europe/Paris&bgcolor=DDDDDD&fgcolor=111111&majorGridLineColor=black&minorGridLineColor=grey''

is what I use in my :ref:`Thruk <integration/thruk-usage>`.

A change has been pushed in thruk's github to grant Thruk the features it has for pnp to graphite. The rule above (use action_url) still applies. Graphite will be displayed when the action_url contains the keyword "render".

.. important::   The graphite template files feature is not used in Thruk. It is a "shinken UI only" feature.


Enjoy it
---------

Restart shinken-arbiter and you are done.

::

  /etc/init.d/shinken-arbiter restart</code>

.. _Installing Graphite version 0.9.8: http://agiletesting.blogspot.ca/2011/04/installing-and-configuring-graphite.html
.. _Chef recipe for the above demonstration: https://github.com/manasg/chef-graphite
.. _Graphite: http://graphite.readthedocs.org/en/0.9.10/index.html
.. _this youtube walkthrough from Jason Dixon: http://www.youtube.com/watch?v=0-g--_Be2jc&feature=player_embedded
