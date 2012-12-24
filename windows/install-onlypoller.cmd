@echo off
rem installation of shinken services
rem (c) 2012 October, By VEOSOFT, Jean-françois BUTKIEWICZ
rem This script is for IT admins only. If you do not have experience or
rem knowledge fundation to install manually shinken on a windows host, please use the 
rem integrated installation of Shinken using the setup.exe program delivered by
rem VEOSOFT. This kind of installation perform the same tasks but without any request
rem using command line.
rem This script is delivered upon Alfresco GPL licence.
rem

echo Shinken Windows Installation
echo Provided by VEOSOFT for Shinken Team
echo V 1.2 - October 2012
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

rem copying the libexec folder....
echo Copying the libexec for windows folder...
if not exist ..\libexec md ..\libexec
xcopy libexec-windows ..\libexec /S /E /Y
echo libexec for windows copied.

rem updating the etc folder....
echo Updating the etc for windows folder...
xcopy etc ..\etc /S /E /Y
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

echo Updating the install root for windows folder...
xcopy *.* ..\ /Y
echo install root for windows updated.
echo Starting installation of arbiter in the main process
cd ..

start install-poller.cmd

echo Installation finished.
