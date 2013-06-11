@Echo off
setlocal
Title Shinken installation script for Windows
REM installation of shinken services
REM (c) 2013 May, By VEOSOFT, Jean-françois BUTKIEWICZ
REM This script is for IT admins only. If you do not have experience or
REM knowledge fundation to install manually shinken on a windows host, please use the 
REM integrated installation of Shinken using the setup.exe program delivered by
REM VEOSOFT. This kind of installation perform the same tasks but without any request
REM using command line.
REM This script is delivered upon Alfresco GPL licence.

Echo.
cls
REM Globals
Set scriptFile=install-shinken.cmd
Set scriptName=Shinken Windows Installation
Set scriptVersion=1.4 - June 2013
REM Test mode, add -p -c (preview and count ...)
Set toolFileContentReplace=fart -r -i 
Set toolFilesCopy=xcopy /S /E /Y /Q

REM Default values
Set confirm=no
Set services=no
Set pythonDir=C:\Python27
Set installDir=C:\Shinken
Set pluginsDir=%installDir%\libexec
Set logsDir=%installDir%\logs

Echo ============================================================
Echo %scriptName%
Echo Provided by VEOSOFT for Shinken Team
Echo Adapted by Frederic MOHIER :
Echo - installation from GitHub
Echo - installation in console mode
Echo Version %scriptVersion%
Echo ============================================================

REM Parsing command line parameters
@Echo off

:checkForSwitches
	If [%1]==[] Goto command
	REM Echo Processing parameter : %1
	If '%1'=='/?' Goto syntax
	If '%1'=='-?' Goto syntax
	If '%1'=='/c' Goto pConfirm
	If '%1'=='-c' Goto pConfirm
	If '%1'=='/s' Goto pService
	If '%1'=='-s' Goto pService
	If '%1'=='/i' Goto pInstallDir
	If '%1'=='-i' Goto pInstallDir
	If '%1'=='/l' Goto pLogsDir
	If '%1'=='-l' Goto pLogsDir

	@Echo Unknown parameter : %1, ignoring.
	Goto :command

:pConfirm
	Set confirm=yes
	Shift
	Goto :checkForSwitches

:pService
	Set key=%1
	Shift
	If [%1]==[] Goto syntax
	Set value=%1
	Echo  value for '%key%' is '%value%'
	Set services=%value%
	Shift
	Goto :checkForSwitches

:pInstallDir
	Set key=%1
	Shift
	If [%1]==[] Goto syntax
	Set value=%1
	Echo  value for '%key%' is '%value%'
	Set installDir=%value%
	Shift
	Goto :checkForSwitches

:pLogsDir
	Set key=%1
	Shift
	If [%1]==[] Goto syntax
	Set value=%1
	Echo  value for '%key%' is '%value%'
	Set logsDir=%value%
	Shift
	Goto :checkForSwitches


:syntax
	Echo Usage : 
	Echo  %0 options : 
	Echo  -s yes/no
	Echo	 yes for Windows services installation
	Echo     no for Windows console mode installation
	Echo     default is console mode
	Echo 
	Echo  -i dir
	Echo     dir is the installation directory
	Echo     default is C:\Shinken
	Echo 
	Echo  -l dir
	Echo     dir is the log files directory
	Echo     default is C:\Shinken\logs
	Echo 
	Echo  -c
	Echo     ask for confirmation to start installation
	Echo     default is silent installation
	Echo ============================================================
	Exit /b 1
	

:command
	Echo %scriptName% : 
	Echo - installation dir : %installDir%
	Echo - log files dir : %logsDir%
	Echo - Windows services ? %services%
	Echo - confirm installation ? %confirm%
	Echo ============================================================

	REM Start installation
	If "%confirm%" == "no" Goto :checkDependencies
	:: Check if the user want to install or remove Shinken
	Set /P choice=Start installation ? (Y/N)
	if not *%choice:~0,1% == *Y if not *%choice:~0,1% == *y goto :endUser

:checkDependencies
	REM To be improved ! Minimum checkings ...
	Echo Checking Shinken dependencies ...
	If Not Exist "C:\Python27\Python.exe" Goto :endDependencies
	If Not Exist "C:\Python27\Lib\site-packages\pythonwin" Goto :endDependencies
	If Not Exist "C:\Python27\Lib\site-packages\pymongo" Goto :endDependencies
	If Not Exist "C:\Python27\Lib\site-packages\Pyro4" Goto :endDependencies

	If Not Exist "C:\MongoDB" Echo *** MongoDB is necessary for some functions in Shinken (store status and checks results), but not mandatory !
	If Not Exist "C:\Perl\bin\Perl.exe" Echo *** Active Perl is necessary for some functions in Shinken (check_wmi_plus and sendmail), but not mandatory !
	If Not Exist "C:\Python27\Lib\site-packages\fcrypt.py" Echo *** fcrypt Python library is necessary for Apache passwords in Shinken WebUI, but not mandatory !
	If Not Exist "C:\Python27\Lib\site-packages\OpenSSL" Echo *** OpenSSL Python library is necessary for SSL in Shinken, but not mandatory !
	Echo Shinken dependencies checked

:shinkenInstall
	If Exist %installDir% Goto :shinkenInstallDirOk
	Echo Creating Shinken installation dir : %installDir%
	MkDir %installDir%
	If Not ERRORLEVEL 1 Goto :shinkenInstallDirOk
	Echo Shinken installation dir creation failed
	Echo Installation aborted
	Exit /b 2

:shinkenInstallDirOk
	Echo Shinken installation dir exists 
	If Exist %logsDir% Goto :shinkenLogsDirOk
	Echo Creating Shinken log files dir : %logsDir%
	MkDir %logsDir%
	If Not ERRORLEVEL 1 Goto :shinkenLogsDirOk
	Echo Shinken log files dir creation failed
	Echo Installation aborted
	Exit /b 2

:shinkenLogsDirOk
	Echo Shinken log files dir exists 
	If "%services%" == "no" Goto shinkenConsole
	If "%services%" == "yes" Goto shinkenServices

:shinkenConsole
	Echo Shinken console mode installation required

	Echo Installing standard Shinken ...
	
	Echo Copying the bin folder to installation dir ...
	If Not Exist %installDir%\bin mkdir %installDir%\bin
	%toolFilesCopy% ..\bin %installDir%\bin
	Echo bin folder copied

	REM Echo Copying the contrib folder to installation dir ...
	REM If Not Exist %installDir%\contrib mkdir %installDir%\contrib
	REM %toolFilesCopy% ..\contrib %installDir%\contrib
	REM Echo contrib folder copied

	REM Ignoring contrib, db, doc, ...
	
	Echo Copying the doc folder to installation dir ...
	If Not Exist %installDir%\doc mkdir %installDir%\doc
	%toolFilesCopy%  ..\doc %installDir%\doc
	Echo Folder copied

	Echo Copying the etc folder to installation dir ...
	If Not Exist %installDir%\etc mkdir %installDir%\etc
	%toolFilesCopy%  ..\etc %installDir%\etc
	Echo Folder copied

	Echo Copying the libexec folder to installation dir ...
	If Not Exist %installDir%\libexec mkdir %installDir%\libexec
	%toolFilesCopy%  ..\libexec %installDir%\libexec
	Echo Folder copied

	Echo Copying the share folder to installation dir ...
	If Not Exist %installDir%\share mkdir %installDir%\share
	%toolFilesCopy%  ..\share %installDir%\share
	Echo Folder copied

	Echo Copying the shinken folder to installation dir ...
	If Not Exist %installDir%\shinken mkdir %installDir%\shinken
	%toolFilesCopy%  ..\shinken %installDir%\shinken
	Echo Folder copied

	Echo Copying the modules folder to installation dir ...
	If Not Exist %installDir%\modules mkdir %installDir%\modules
	%toolFilesCopy%  ..\modules %installDir%\modules
	Echo Folder copied

	Echo Updating the bin folder with windows specific files ...
	%toolFilesCopy%  bin %installDir%\bin
	Echo Removing main Unix and unused files in the folder ...
	del %installDir%\bin\*.sh /Q /F
	del %installDir%\bin\nagios /Q /F
	del %installDir%\bin\shinken /Q /F
	Echo Setting the shinken daemons from standard distro
	move /Y %installDir%\bin\shinken-arbiter %installDir%\bin\shinken-arbiter.py
	move /Y %installDir%\bin\shinken-broker %installDir%\bin\shinken-broker.py
	move /Y %installDir%\bin\shinken-poller %installDir%\bin\shinken-poller.py
	move /Y %installDir%\bin\shinken-receiver %installDir%\bin\shinken-receiver.py
	move /Y %installDir%\bin\shinken-reactionner %installDir%\bin\shinken-reactionner.py
	move /Y %installDir%\bin\shinken-scheduler %installDir%\bin\shinken-scheduler.py
	move /Y %installDir%\bin\shinken-skonf %installDir%\bin\shinken-skonf.py
	move /Y %installDir%\bin\shinken-admin %installDir%\bin\shinken-admin.py
	move /Y %installDir%\bin\shinken-discovery %installDir%\bin\shinken-discovery.py
	move /Y %installDir%\bin\shinken-hostd %installDir%\bin\shinken-hostd.py
	move /Y %installDir%\bin\shinken-packs %installDir%\bin\shinken-packs.py
	Echo Shinken daemons installed...
	Echo Updating file content ...
	%toolFileContentReplace% %installDir%\bin\*.* @@pythondir@@ %pythonDir%
	%toolFileContentReplace% %installDir%\bin\*.* @@installdir@@ %installDir%
	%toolFileContentReplace% %installDir%\bin\*.* @@pluginsdir@@ %pluginsDir%
	%toolFileContentReplace% %installDir%\bin\*.* @@logdir@@ %logsDir%
	Echo Folder updated.

	Echo Updating the etc folder with windows specific files ...
	%toolFilesCopy%  etc %installDir%\etc
	Echo Updating file content ...
	%toolFileContentReplace% %installDir%\etc\*.* @@pythondir@@ %pythonDir%
	%toolFileContentReplace% %installDir%\etc\*.* @@installdir@@ %installDir%
	%toolFileContentReplace% %installDir%\etc\*.* @@pluginsdir@@ %pluginsDir%
	%toolFileContentReplace% %installDir%\etc\*.* @@logdir@@ %logsDir%
	Echo Folder updated.
	
	Echo Updating the libexec folder with plugins ...
	%toolFilesCopy%  libexec\wmic %installDir%\libexec
	%toolFilesCopy%  libexec\notifications %installDir%\libexec
	%toolFilesCopy%  libexec\cygwin_plugins %installDir%\libexec
	%toolFilesCopy%  libexec\check_wmi_plus %installDir%\libexec
	Echo Updating file content ...
	%toolFileContentReplace% %installDir%\libexec\*.* @@pythondir@@ %pythonDir%
	%toolFileContentReplace% %installDir%\libexec\*.* @@installdir@@ %installDir%
	%toolFileContentReplace% %installDir%\libexec\*.* @@pluginsdir@@ %pluginsDir%
	%toolFileContentReplace% %installDir%\libexec\*.* @@logdir@@ %logsDir%
	Echo Folder updated.
	
	Exit /b 1
	
	
:shinkenServices
	Exit /b 1
	
	Echo Shinken services mode installation required
	Echo Checkin for InstallUtil tool ....
	If exist "%systemroot%\microsoft.net\framework\v2.0.50727\installutil.exe" Goto NEXTSTEP1
		Echo InstallUtil.exe tools cannot be found on your system.
		Echo Please check you .net framework 2.0 installation to install shinken with this script
		Exit /b 1

:NEXTSTEP1

rem copying the logconfig folder....
Echo Copying the logconfig folder...
If not exist ..\logconfig md ..\logconfig
xcopy logconfig ..\logconfig
Echo logconfig copied.

rem updating the etc folder....
Echo Updating the etc for windows folder...
xcopy etc ..\etc
rem modifying the resource.cfgtpl
copy /Y ..\etc\resource.cfgtpl ..\etc\resource.cfg

Echo etc for windows updated.

rem copying the svclogs folder....
Echo copying the svclogs folder...
If not exist ..\svclogs md ..\svclogs
xcopy svclogs ..\svclogs
Echo svclogs updated.

rem updating the bin folder....
Echo Updating the bin for windows folder...
xcopy bin ..\bin
Echo bin for windows updated.


rem Checking the third part....
ping www.veosoft.net -n 1
If "%errorlevel%"=="0" Goto thirdpart
Echo #################################################################################
Echo #################################################################################
Echo WARNING !
Echo Internet seems to be not connected, or the veosoft website is not reachable....
Echo Please check your connection. You may also download the thirdpart by your own way.
Echo Ending the installation script with services installation.
Echo .
Echo #################################################################################
Echo #################################################################################
pause
Goto installservices
:thirdpart

rem V1.3 - New Check_wmi_plus to change name collumn on check_pages
rem v1.3 - 3rdPart libexec only check_nt and DLL in the libexec
Echo Downloading the check_wmi_plus by Matthew Jurgens - Copyright (C) 2011-2013
Echo Modification of configuration files by Veosoft for Shinken team - May 2013
wget.exe http://www.veosoft.net/downloads/WindowsFiles/1.4-3rdPart/check_wmi_plus_1.56.zip check_wmi_plus.zip
Echo Downloading the nagios check_nt program
Echo Modification and compilation with cygwin by Veosoft for Shinken team - May 2013
wget.exe http://www.veosoft.net/downloads/WindowsFiles/1.4-3rdPart/libexec-windows_1.4.zip libexec-windows.zip

rem Stange thing, on some systems, the WGET will do the extraction - an windows explorer feature i think !
If not exist check_wmi_plus\check_wmi_plus.pltpl cscript dounzip.vbs check_wmi_plus
If not exist libexec-windows\check_apache.pl cscript dounzip.vbs libexec-windows

Echo merging the thirdpart into shinken libexec folder...
xcopy check_wmi_plus\*.* libexec-windows

copy /Y .\libexec-windows\check_wmi_plus.pltpl .\libexec-windows\check_wmi_plus.pl
copy /Y .\libexec-windows\check_wmi_plus.conftpl .\libexec-windows\check_wmi_plus.conf

:installservices
rem copying the libexec folder....
Echo Copying the libexec for windows folder...
If not exist ..\libexec md ..\libexec
xcopy libexec-windows ..\libexec
Echo libexec for windows copied.

Echo Updating the install root for windows folder...
xcopy *.* ..\ /Y
Echo install root for windows updated.

:modifpack
rem copying the windows pack modified....
Echo Copying the windows pack modified...
xcopy windowshost_pack\*.* ..\etc\packs\os\windows
Echo windows pack modified.

Echo Starting installation of arbiter in the main process
cd ..
If exist .\libexec\check_wmi_plus.pl cscript replace_perl_installdir.vbs .\libexec\check_wmi_plus.pl @@installdir@@ "%cd%"
If exist .\libexec\check_wmi_plus.conf cscript replace_perl_installdir.vbs .\libexec\check_wmi_plus.conf @@installdir@@ "%cd%"
cscript replace_installdir.vbs .\etc\resource.cfg @@installdir@@ "%cd%"
REM Now, change the @@installdir@@ of the conf files (xxxx-windows.ini

REM Using replace_installdir2 is to use \\ in order of \
cscript replace_installdir2.vbs .\etc\nagios-windows.cfg @@installdir@@ "%cd%"
cscript replace_installdir2.vbs .\etc\shinken-specific-windows.cfg @@installdir@@ "%cd%"

start install-arbiter.cmd
start install-broker.cmd
start install-poller.cmd
start install-receiver.cmd
start install-reactionner.cmd
start install-scheduler.cmd

Echo Installation finished.
rem Now, we are going in the parent folder to delete the windows folder and only let the deletion scripts
rd /s /q windows\bin
rd /s /q windows\etc
rd /s /q windows\libexec-windows
rd /s /q windows\logconfig
rd /s /q windows\tools
rd /s /q windows\svclogs
rd /s /q windows\windowshost_pack
rd /s /q windows\check_wmi_plus
del /f /q windows\check_wmi_plus.zip
del /f /q windows\libexec-windows.zip
del /f /q windows\createeventsource.exe
del /f /q windows\dounzip.vbs
del /f /q windows\log4net*.*
del /f /q windows\licence.rtf
del /f /q windows\replace_*.vbs
del /f /q windows\Shinken_*.*
del /f /q windows\veo*.*
del /f /q windows\wget*.*

pause

:endDependencies
	Echo Installation script aborted due to dependency checking.
	Echo Mandatory dependencies checked are : 
	Echo  Python installed in C:\Python27
	Echo  PyWin32
	Echo  Pyro
	Echo  MongoDB installed in C:\MongoDB
	Echo  PyMongo
	Echo ============================================================
	Goto end

:endUser
Echo Installation script aborted by user.
Goto end

:end
endlocal

Exit /B 0

