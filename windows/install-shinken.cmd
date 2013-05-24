@echo off
rem installation of shinken services
rem (c) 2013 May, By VEOSOFT, Jean-françois BUTKIEWICZ
rem This script is for IT admins only. If you do not have experience or
rem knowledge fundation to install manually shinken on a windows host, please use the 
rem integrated installation of Shinken using the setup.exe program delivered by
rem VEOSOFT. This kind of installation perform the same tasks but without any request
rem using command line.
rem This script is delivered upon Alfresco GPL licence.
rem

echo Shinken Windows Installation
echo Provided by VEOSOFT for Shinken Team
echo V 1.3 - May 2013
echo ====================================
echo Checkin for InstallUtil tool ....

if exist "%systemroot%\microsoft.net\framework\v2.0.50727\installutil.exe" goto NEXTSTEP1
	echo InstallUtil.exe tools cannot be found on your system.
	echo Please check you .net framework 2.0 installation to install shinken with this script
	exit 1

:NEXTSTEP1

rem copying the logconfig folder....
echo Copying the logconfig folder...
if not exist ..\logconfig md ..\logconfig
xcopy logconfig ..\logconfig /S /E /Y
echo logconfig copied.

rem updating the etc folder....
echo Updating the etc for windows folder...
xcopy etc ..\etc /S /E /Y
rem modifying the resource.cfgtpl
copy /Y ..\etc\resource.cfgtpl ..\etc\resource.cfg

echo etc for windows updated.

rem copying the svclogs folder....
echo copying the svclogs folder...
if not exist ..\svclogs md ..\svclogs
xcopy svclogs ..\svclogs /S /E /Y
echo svclogs updated.

rem updating the bin folder....
echo Updating the bin for windows folder...
xcopy bin ..\bin /S /E /Y
echo bin for windows updated.


rem Checking the third part....
ping www.veosoft.net -n 1
if "%errorlevel%"=="0" goto thirdpart
echo #################################################################################
echo #################################################################################
echo WARNING !
echo Internet seems to be not connected, or the veosoft website is not reachable....
echo Please check your connection. You may also download the thirdpart by your own way.
echo Ending the installation script with services installation.
echo .
echo #################################################################################
echo #################################################################################
pause
goto installservices
:thirdpart

rem V1.3 - New Check_wmi_plus to change name collumn on check_pages
rem v1.3 - 3rdPart libexec only check_nt and DLL in the libexec
echo Downloading the check_wmi_plus by Matthew Jurgens - Copyright (C) 2011-2013
echo Modification of configuration files by Veosoft for Shinken team - May 2013
wget.exe http://www.veosoft.net/downloads/WindowsFiles/1.4-3rdPart/check_wmi_plus_1.56.zip check_wmi_plus.zip
echo Downloading the nagios check_nt program
echo Modification and compilation with cygwin by Veosoft for Shinken team - May 2013
wget.exe http://www.veosoft.net/downloads/WindowsFiles/1.4-3rdPart/libexec-windows_1.4.zip libexec-windows.zip

rem Stange thing, on some systems, the WGET will do the extraction - an windows explorer feature i think !
if not exist check_wmi_plus\check_wmi_plus.pltpl cscript dounzip.vbs check_wmi_plus
if not exist libexec-windows\check_apache.pl cscript dounzip.vbs libexec-windows

echo merging the thirdpart into shinken libexec folder...
xcopy check_wmi_plus\*.* libexec-windows /S /E /Y

copy /Y .\libexec-windows\check_wmi_plus.pltpl .\libexec-windows\check_wmi_plus.pl
copy /Y .\libexec-windows\check_wmi_plus.conftpl .\libexec-windows\check_wmi_plus.conf

:installservices
rem copying the libexec folder....
echo Copying the libexec for windows folder...
if not exist ..\libexec md ..\libexec
xcopy libexec-windows ..\libexec /S /E /Y
echo libexec for windows copied.

echo Updating the install root for windows folder...
xcopy *.* ..\ /Y
echo install root for windows updated.

:modifpack
rem copying the windows pack modified....
echo Copying the windows pack modified...
xcopy windowshost_pack\*.* ..\etc\packs\os\windows /S /E /Y
echo windows pack modified.

echo Starting installation of arbiter in the main process
cd ..
if exist .\libexec\check_wmi_plus.pl cscript replace_perl_installdir.vbs .\libexec\check_wmi_plus.pl @@installdir@@ "%cd%"
if exist .\libexec\check_wmi_plus.conf cscript replace_perl_installdir.vbs .\libexec\check_wmi_plus.conf @@installdir@@ "%cd%"
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

echo Installation finished.
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