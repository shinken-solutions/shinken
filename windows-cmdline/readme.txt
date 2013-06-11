===================================
Windows console mode Shinken 
===================================

This installation script and package installs Shinken on Windows from the GitHub source files.

This script is based on Veosoft command line installation script. It includes and runs the existing VeoSoft script when run in service mode installation (command line parameter).

-----------------------------------
Configuration ...
-----------------------------------
The installation script and the installation files are to be located in a directory named windows-cmdline located under the Shinken directory extracted from the GitHub tarball.


-----------------------------------
Launching ...
-----------------------------------
It may be started specifying : 
- console or service mode for Windows
- installation directory for Shinken (default c:\shinken)
- log files directory (default c:\shinken\logs)

Usage : 
 install-shinken.cmd options
 Options are :
 -s yes/no
	yes for Windows services installation
	no for Windows console mode installation
	default is console mode

 -i dir
	dir is the installation directory
	default is C:\Shinken

 -l dir
	dir is the log files directory
	default is C:\Shinken\logs

 -c
	ask for confirmation to start installation
	default is silent installation

*** Please note that 'service mode' is to be tested and probably improved ...

-----------------------------------
Installing ...
-----------------------------------
It checks if necessary requirements (Python, Pyro, ...) and optional requirements (MongoDB, Perl, ...) are met. If mandatory requirements are not met the installation is aborted.
*** Please note that the requirements checking is is simply based on existing directories or files and not on real functionnal checking ...

It copies necessary files and then updates :
.bin directory for : 
 - renaming daemons to .py
 - removing unnecessary Nix files
 - installing Windows command files
.etc directory for :
 - installing a configuration for a simple Shinken for Windows :
	one instance for each module
	assuming active checks with check_wmi_plus and passive checks with NRPE and NSCA
	assuming a mongodb database is available
	assuming no Graphite is available
 - installing a MongoDB database pack that do not check MongoDB replication (not installed as a default in MongoDB setup ...)
 - installing a Windows pack including services and commands for check_wmi_plus plugin
.libexec directory for :
 - installing Veosoft tools to request WMI (wmic.exe) and ping (CheckWinPing.exe)
 - installing Cygwin Nagios plugin 
 - installing plugin check_wmi_plus 1.56 

-----------------------------------
Configuring ...
-----------------------------------
After installation, testing and configuration is still necessary ... despite the installed configuration is almost 'out of the box', some necessary configuration is to be made !

1/ configuring Shinken consoles for Windows (optional)
 Open a Windows command line shell 
 CD to bin installation directory (c:\Shinken\bin)
 Launch 'start_shinken console'
 
 This will configure the system position and fonts for the console windows used by the Shinken daemons. The configuration is defined in the shinken-console.reg file that may be edited and modified ...

2/ editing Shinken configuration located in etc installation directory (C:\Shinken\etc)
 Edit the 'resource.cfg' file and update this section :
	##Now Active directory and Ldap macros
	# Replace myDomain by your domain name
	# Replace myAccount by the name of an account authorized to contact remote WMI
	# Replace myPassword by the password of this account
	$DOMAIN$=myDomain
	$DOMAINUSERSHORT$=myAccount
	$DOMAINUSER$=$DOMAIN$\\$DOMAINUSERSHORT$
	$DOMAINPASSWORD$=myPassword

 Edit the 'shinken-specific-windows.cfg' file and change the WebUI auth_secret variable.

3/ testing Shinken configuration
 Open a Windows command line shell 
 CD to bin installation directory (c:\Shinken\bin)
 Launch 'start_shinken test'
 
 This will launch the Shinken arbiter with an option to check configuration.

4/ starting Shinken 
 Open a Windows command line shell 
 CD to bin installation directory (c:\Shinken\bin)
 Launch 'start_shinken'
 
 This will launch the Shinken configuration test and then it will start all the Shinken daemons in separate console windows titled with the daemon name. The console windows will be positioned according to the configuration of the system if ever or to the configuration set by the 'start_shinken console' command.
