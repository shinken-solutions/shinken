.. _configure_check_wmi_plus_onwindows:



=========================================
check_wmi_plus.pl for shinken on windows 
=========================================




The premier WMI check program, `check_wmi_plus.pl`_,  can now be used on the windows platform in association with the shinken WMIC.EXE. 


WMIC.EXE is not the native wmic of the windows system. It is a standalone program created to have the same input/output as the linux WMIC. This permits check_wmi_plus to use WMIC on windows with the same options as the linux program. WMIC.EXE (binaries and sources) are included with Shinken (1.2.2 and newer).

WMIC.EXE and associated Shinken programs under Windows, use the .NET framework 2.0.



Pre-requisites for using check_wmi_plus.pl 
-------------------------------------------


Check_wmi_plus.pl needs a perl interpreter to work, we recommend activePerl. At this time, strawberry perl cannot be used as a non interactive program. The Shinken poller starts programs in a non interactive mode, which means no Strawberrt perl. 

   - `Download activeperl`_ and select the 5.16.x Windows x64 version
   - Download and install PERL Number::Format using CPAN
   - Download and install PERL Config::Inifiles using CPAN
   - Download and install PERL DataTime using CPAN
   - Download and install .NET 2.0 framework from Microsoft (If it is not already installed). On Windows 2008 R2, install 3.5 (SP1) Framework. It includes the 2.0 version.

.. important::  PERL Dependencies for check_wmi_plus.pl (needed by check_wmi_plus and not installed by default. Please lookup the CPAN documentation if you don"t know how to install PERL modules)
   

After having installed all dependencies, you can now proceed to install check_wmi_plus.pl

  - Download and install `check_wmi_plus.pl`_
Make sure to change the references into the check_wmi_plus.conf file and the initial variables into the check_wmi_plus.pl (take a look to match the install folder and the WMIC.exe path)


Shinken configuration to use check_wmi_plus 
--------------------------------------------


At first you must configure monitoring parameters in the Shinken etc/resource.cfg file : 

$DOMAIN$=domain

$DOMAINUSERSHORT$=shinken_user

$DOMAINUSER$=$DOMAIN$\\$DOMAINUSERSHORT$

$DOMAINPASSWORD$=superpassword

$LDAPBASE$=dc=eu,dc=society,dc=com


These options are set by default, but the poller will also use a « hidden » *$DOMAINUSERSHORT$* parameter set in the Shinken templates.cfg. Just set this parameter in the resource.cfg file to overload the template and make use of a single configuration file.

These options are used by the check_wmi_plus plugin as credentials for WMI local or remote access. If you intend to monitor hosts that are not controlled by a domain controller (simple workgroup members) it is necessary to overload the *$DOMAINUSER$* parameter : 

$DOMAIN$=domain

$DOMAINUSERSHORT$=shinken_user

$DOMAINUSER$=$DOMAINUSERSHORT$

$DOMAINPASSWORD$=superpassword

$LDAPBASE$=dc=eu,dc=society,dc=com


**You need to set the appropriate values for your environment, the above values (domain, shinken_user and superpassword) are simply examples. :-)**

To test the settings, just add a host to be monitored by setting a new host in a cfg file named with the name of the host for example etc\hosts\clishinken.cfg  based on the windows template:

define host{
use              	windows
contact_groups		admins
host_name 		clishinken
address 		clishinken
icon_set		server
}

Restart the Shinken windows services. The WebUI now checks a new windows host : clishinken !
In this configuration, the remote WMI is executed using the credentials set into the resource.cfg file. It"s working but is not really secure.

.. warning::  warning
   
   If you look in the local configuration you will see check_wmi_plus. For Windows, it's not allowed to use credentials for a local WMI request. As a workaround, WMIC.EXE will use the local credentials if the target host is set to localhost and the user is set to local. Check the etc\commands-windows.cfg to see how it works. You will see something like this :
   
   define command {
     
::

    command_name    check_local_disks
       command_line    $PLUGINSDIR$/check_wmi_plus.pl -H localhost -u "local" -p "local" -m checkdrivesize -a '.' -w 90 -c 95 -o 0 -3 0
   }
   


Secure method to use check_wmi_plus on windows 
-----------------------------------------------


There is a new option to use check_wmi_plus with shinken : Use the poller configuration service credentials.

For most sysadmins, putting an unencrypted password in a config file is not a best practice. IT secuirty will be compromised if someone can read the configuration file. The rights of this user on servers are also very high (WMI requests need more configuration to be security compliant on windows server, including DCOM configuration or admin rights…) You can find a good idea of how to configure the remote wmi on windows here:

`www.op5.com/how-to/agentless-monitoring-windows-wmi/`_

To set a “bypass" credential, only set the $DOMAINUSERSHORT$ to #### (4 sharp symbols without spaces)
If the WMIC see this specific user,it just will use the caller credentials - in all cases the poller service user.
By default, the Shinken services are set to localsystem. 

Stop the services (manually or using the bin\stop_allservices.cmd script).

Open the services.msc (or the server manager, and then the services part)



.. image:: /_static/images//services-std.jpg?500
   :scale: 90 %



double-click on the Shinken poller service



.. image:: /_static/images///poller1.jpg?500
   :scale: 90 %



go to the log On tab



.. image:: /_static/images///poller2.jpg?500
   :scale: 90 %



check the “This account" radio button and set the Shinken user account (the same as you set the resource.cfg file)



.. image:: /_static/images///poller3.jpg?500
   :scale: 90 %



As you can see, you never see the password… 
Click on the Apply button (the first time you set an account to logon as a service, you will see a message box to announce the fact that the account is granted to logon as a service).
Change the resource.cfg file to set the #### as the domainusershort and put a wrong password to be sure to remove the old credentials. Save the resource.cfg file.

Restart the services (manually or using the bin\start_allservices.cmd) 



.. image:: /_static/images///services-ext.jpg?500
   :scale: 90 %



The poller will now launch the WMI request under its own service account…

.. important::  Setting the remote WMI configuration on windows is not as easy as it seems.
   
   The domains admins or other IT admins may set GPO or other tools to change the configuration of the system - including the right to enable or disable remote WMI. Please be patient, and change options one by one if your wmi tests are not working.

.. _www.op5.com/how-to/agentless-monitoring-windows-wmi/: http://www.op5.com/how-to/agentless-monitoring-windows-wmi/
.. _Download activeperl: http://www.activestate.com/activeperl/downloads
.. _check_wmi_plus.pl: http://www.edcint.co.nz/checkwmiplus/