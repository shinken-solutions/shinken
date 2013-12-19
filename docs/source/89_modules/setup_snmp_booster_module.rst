.. _setup_snmp_booster_module:



Shinken integrated SNMP Module 
===============================




SnmpBooster Download Install and Configure 
-------------------------------------------


  * :ref:`What is the SnmpBooster module <SnmpBooster_how_it_works>`
  * :ref:`Install and configure the SNMP acquisition module. <Setup SNMP booster module>` [You are here]
  * :ref:`Reference - SnmpBooster troubleshooting <snmpbooster_troubleshooting>`
  * :ref:`Reference - SnmpBooster design specification <snmpbooster_design_specification>`
  * :ref:`Reference - SnmpBooster configuration dictionnary <snmpbooster_dictionary>`



Downloads 
----------


The SnmpBooster module and genDevConfig are currently in public beta prior to integration within Shinken. You can consult the design specification to see the :ref:`current development status <SnmpBooster design specification >`.
  * `github.com/xkilian/genDevConfig`_
  * `github.com/titilambert/shinken/tree/snmp_booster/shinken/modules`_  (snmp_booster branch)
    * Simply right-click and download snmp_poller.py then copy it to shinken/modules/



Requirements 
-------------


The SnmpBooster module requires:

  * Python 2.6+
  * Shinken 1.2+
  * `PySNMP 4.2.1+ (Python module and its dependencies)`_
  * `ConfigObj (Python module)`_
  * `python-memcached`_
  * memcachedb or memcached package for your operating system (ex. For Ubuntu: apt-get install memcachedb) :ref:`Note <memcached_note>`

The genDevConfig profile generator depends on:
  * Perl 5.004+
  * 4 perl modules available from CPAN and network repositories. genDevConfig/INSTALL has the installation details.

**STRONGLY RECOMMENDED: Use the same version of Python and Pyro on all hosts running Shinken processes.**


Installation 
-------------


SnmpBooster:

  * Install the dependencies
  * Copy the file snmp_poller.py from the git repository to your shinken/modules directory.
  * Configuration steps are listed in the present web page.

genDevConfig:

  * Download and extract the archive to your server.
  * See genDevConfig/INSTALL on how to install and configure it.



Configuration 
--------------




How to define the SnmpBooster module in the Shinken daemons 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


You need to modify shinken-specific.cfg, which is located in $shinken/etc/shinken-specific.cfg



Arbiter daemon configuration 
*****************************


Simply declare the module:

  
::

  modules SnmpBooster</code>
  


Scheduler daemon configuration 
*******************************

  
  Simply declare the module:
  
<code>modules SnmpBooster



Poller daemon configuration 
****************************


Simply declare the module:

  
::

  modules SnmpBooster</code>
  


SnmpBooster Module declaration 
*******************************

  
  # Included in Shinken v1.2.1 shinken-specific.cfg.
  
  <code>define module {
  
::

       module_name          SnmpBooster
       module_type          snmp_poller
       datasource           /usr/local/shinken/etc/packs/network/SnmpBooster/   ; SET THE DIRECTORY FOR YOUR Defaults*.ini FILES
       memcached_host       x.x.x.x  ; SET THE IP ADDRESS OF YOUR memcached SERVER
       memcached_port       11211  ; default port for a memcached process
}

If you do not know the IP adress on which your memcache is listening, check under /etc/memcached.conf. Or do a:
  
::

  netstat -a | grep memcached</code>
  If you are running a test on the local machine you can leave memcached on 127.0.0.1 (localhost), but if your poller, scheduler or arbiter is on a different machine, set the memcached to listen on a real IP address.
  


How to define a Host and Service 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  


Step 1 
*******

  
  Create a template for your SNMP enabled devices.
  
  Sample template:
  
  
  <code>cd shinken/etc/packs/network/
  mkdir SnmpBooster
  
vi shinken/etc/packs/network/SnmpBooster/templates.cfg

  
::

  define command {
  
::

    command_name    check_snmp_booster
    command_line    check_snmp_booster -H $HOSTNAME$ -C $SNMPCOMMUNITYREAD$ -V 2c -t $ARG1$ -i $_SERVICEINST$ -T $_SERVICETRIGGERGROUP$
    module_type     snmp_poller
}

  
::

  define service {
  
::

    name                    default-snmp-template
    check_command           check_snmp_booster!$_SERVICEDSTEMPLATE$!$_SERVICEINST$!$_SERVICETRIGGERGROUP
    _inst                   None
    _triggergroup           None
    max_check_attempts      3
    check_interval          1
    retry_interval          1
    register                0
}

  
::

  define host{
  
::

    name                    SnmpBooster-host
    alias                   SnmpBooster-host template
    check_command	    check_host_alive
    max_check_attempts      3
    check_interval          1
    retry_interval          1
    use                     generic-host
    register                0
}




Step 2 
*******


Define some hosts and services. You would typically use genDevConfig or another configuration generator to create these for you.

Mandatory service arguments related to SNMP polling:
  
::

     _dstemplate		Cisco-Generic-Router  ; Name of a DSTEMPLATE defined in the SnmpBooster config.ini file
  
::

   snmpcommunityread    which is set in your resource.cfg file
  
Optional service arguments related to SNMP polling with default values: 
  
::

      _inst                   None   ; Could be numeric: 0, None or an instance mapping function like: map(interface-name,FastEthernet0_1)
  
::

    _triggergroup           None   ; Name of the triggergroup defined in the SnmpBooster config.ini file to use for setting warning and critical thresholds
   
  
Sample Shinken host and service configuration:

  
::

  # Generated by genDevConfig 3.0.0
  # Args: --showunused -c publicstring 192.168.2.63
  # Date: Thu Aug 30 17:47:59 2012
  
  #######################################################################
  # Description: Cisco IOS Software, C2960 Software (C2960-LANBASEK9-M), Version 12.2(50)SE4, RELEASE SOFTWARE (fc1) Technical Support: http://www.cisco.com/techsupport Copyright (c) 1986-2010 by Cisco Systems, Inc. Compiled Fri 26-Mar-10 09:14 by prod_rel_team
  #     Contact: 
  # System Name: SITE1-ASW-Lab04
  #    Location: 
  #######################################################################
  
  define host {
  
::

   host_name		192.168.2.63
   display_name		192.168.2.63
   _sys_location	
   address		192.168.2.63
   hostgroups		
   notes		
   parents		
   use			default-snmp-host-template
   register		1
  }
  
  define service {
  
::

   host_name		192.168.2.63
   service_description	chassis
   display_name		C2960 class chassis
   _dstemplate		Cisco-Generic-Router
   _inst		0
   use			default-snmp-template
   register		1
  }
  
  define service {
  
::

   host_name		192.168.2.63
   service_description	chassis.device-traffic
   display_name		Switch fabric statistics - Packets per Second
   _dstemplate		Device-Traffic
   use			default-snmp-template
   register		1
  }
  
  define service {
  
::

   host_name		192.168.2.63
   service_description	if.FastEthernet0_1
   display_name		FastEthernet0_1 Description: Link to Router-1 100.0 MBits/s ethernetCsmacd
   _dstemplate		standard-interface
   _inst		map(interface-name,FastEthernet0_1)
   use			default-snmp-template
   register		1
}





Here is an example configuration of the config.ini file 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  
::

  [DATASOURCE]
  
::

    OidmyOidDefinition = .1.3.6.1.45.0
    [myOidDefinition] ; Use the same name as the myOidDeiniftion, but omit the leading "Oid"
        ds_type = DERIVE
        ds_calc = 8,*  ; RPN expression : Oid, 8, *  Which means Oid * 8 = ds_calc
        ds_oid = $OidmyOidDefinition
  [DSTEMPLATE]
  
::

    [myCiscoRouter]
        ds = myOidDefinition
  [TRIGGER]
  
::

    [trigger1]
        warning = RPN expression
        critical = RPN expression
    [trigger2]
        warning = RPN expression
        critical = RPN expression
  [TRIGGERGROUP]
  
::

    [CiscoRouterTriggers]
        triggers = trigger1, trigger2
.. _python-memcached: http://pypi.python.org/pypi/python-memcached/
.. _PySNMP 4.2.1+ (Python module and its dependencies): http://pysnmp.sourceforge.net/download.html
.. _github.com/titilambert/shinken/tree/snmp_booster/shinken/modules: https://github.com/titilambert/shinken/tree/snmp_booster/shinken/modules
.. _github.com/xkilian/genDevConfig: https://github.com/xkilian/genDevConfig
.. _ConfigObj (Python module): http://www.voidspace.org.uk/python/configobj.html#downloading