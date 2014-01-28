.. _use_the_discovery_with_shinken:

======================
Discovery with Shinken
======================


Simple use of the discovery tool 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


When Shinken is installed, the discovery script shinken-discovery can help you start your new monitoring tool and integrate  a large number of hosts. This does not not replace extracting data from an authoritative CMDB/IT reference for provisioning known hosts. It can be used to supplement the data from the authoritative references.

At this time, two "discovery" modules are available:
  * Network based discovery using nmap
  * VMware based discovery, using the check_esx3.pl script communicating with a vCenter installation.

It is suggested to execute both discovery modules in one pass, because one module can use data from the other.



Setup nmap discovery 
*********************


The network discovery scans your network and sets up a basic monitoring configuration for all your hosts and network services. It uses the nmap tool.

Ubuntu:
  
::

  sudo apt-get install nmap
RedHat/Centos:
  
::

  yum install nmap
Windows: Not available at this time.

You need to setup the nmap targets in the file /usr/local/shinken/etc/resource.cfg:
For nmap:
  
::

  $NMAPTARGETS$=localhost www.google.fr 192.168.0.1-254
This will scan the localhost, one of the numerous Google server and your LAN. Change it to your own LAN values of course!

.. tip::  This value can be changed without modifying this file with the -m discovery script argument



Setup the VMware part 
**********************


.. tip::  Of course, if you do not have a vCenter installation, skip this part ...

You will need the check_esx3.pl script. You can get it at http://www.op5.org/community/plugin-inventory/op5-projects/op5-plugins and install it in your standard plugin directory (should be /var/lib/plugins/nagios by default).

You need to setup vcenter acces in the file /etc/shinken/resource.cfg:
Enter your server and credential (can be an account domain)
  
::

  $VCENTER$=vcenter.mydomain.com
  $VCENTERLOGIN$=someuser
  $VCENTERPASSWORD$=somepassowrd
  


Launch it! 
***********


Now, you are ready to run the discovery tool:

This call will create hosts and services for nmap and vmware (vsphere) scripts in the /etc/shinken/object/discovery directory.
  
::

  sudo shinken-discovery -o /etc/shinken/objects/discovery -r nmap,vsphere
  
If you are lazy and do not want to edit the resource file, you can set macros with the -m arguments:
  
::

  sudo shinken-discovery -o /etc/shinken/objects/discovery -r nmap -m "NMAPTARGETS=192.168.0.1-254 localhost 192.168.0.1-254"
You can set several macros, just put them on the same -m argument, separated by a comma (,).

.. tip::  The scan can take quite a few minutes if you are scanning a large network, you can go have a coffee. The scan timeout is set to 60 minutes.



Restart Shinken 
****************


Once the scan is completed, you can restart Shinken and enjoy your new hosts and services:
  
::

  sudo /etc/init.d/shinken restart
  


More about discovery 
~~~~~~~~~~~~~~~~~~~~~

If you want to know more about the discovery process, like how to create a discovery script or define creation rules, consult the :ref:`advanced discovery <use_the_discovery_with_shinken_advanced>` documentation.

