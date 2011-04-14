@echo off
Title Shinken installation script for Windows V0.1
echo.
cls
REM Shinken installation script for Windows
REM 
REM
REM  V 0.1
REM
REM Copyright (C) 2011 :
REM        * E. Beaulieu - Shinken_install_batch@zebux.org
REM
REM Shinken installationscript for Windows is free software: you can redistribute it and/or modify
REM it under the terms of the GNU Affero General Public License as published by
REM the Free Software Foundation, either version 3 of the License, or
REM (at your option) any later version.
REM
REM Shinken installationscript for Windows is distributed in the hope that it will be useful,
REM but WITHOUT ANY WARRANTY; without even the implied warranty of
REM MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
REM GNU Affero General Public License for more details.
REM
REM You should have received a copy of the GNU Affero General Public License
REM along with Shinken.  If not, see <http://www.gnu.org/licenses/>.
REM





:: Path initialisation
set PATH_ROOT=c:\shinken\
set PATH_BIN=c:\shinken\bin
set PATH_INSTSRV= c:\shinken\windows


:: Check if the user want to install or remove Shinken
set /p CONT=Do you want [I]ntsall or [R]emove Shinken? (I/R)
if not *%CONT:~0,1% == *I if not *%CONT:~0,1% == *i goto remove

:: Check needed programs
if exist %PATH_INSTSRV%\instsrv.exe goto main
echo You need to install  %PATH_INSTSRV%\instsrv.exe from Microsoft Website !!!
echo  http://www.microsoft.com/downloads/details.aspx?FamilyID=9D467A69-57FF-4AE7-96EE-B18C4790CFFD
pause
exit






:main
cls
color 71
echo                ษอออออออออออออออออออออออออออออออออออป
echo                บ                                   บ
echo                บ     Installation de Shinken       บ
echo                บ                                   บ
echo                บ Please do not close this Windows! บ
echo                บ                                   บ
echo                ศอออออออออออออออออออออออออออออออออออผ


:: Check path installation
if exist %PATH_ROOT% goto begin
echo The Shinken directory : %PATH_ROOT% does not exist ! Please create it and reinstall Shinken.
pause
goto end

:begin
move /Y %PATH_BIN%\shinken-poller %PATH_BIN%\shinken-poller.py
move /Y %PATH_BIN%\shinken-reactionner %PATH_BIN%\shinken-reactionner.py
move /Y %PATH_BIN%\shinken-scheduler %PATH_BIN%\shinken-scheduler.py
move /Y %PATH_BIN%\shinken-arbiter %PATH_BIN%\shinken-arbiter.py
move /Y %PATH_BIN%\shinken-broker %PATH_BIN%\shinken-broker.py
move /Y %PATH_BIN%\shinken-receiver %PATH_BIN%\shinken-receiver.py

%PATH_INSTSRV%\instsrv.exe "Shinken-Arbiter" %PATH_INSTSRV%"\srvany.exe"
%PATH_INSTSRV%\instsrv.exe "Shinken-Scheduler" %PATH_INSTSRV%"\srvany.exe"
%PATH_INSTSRV%\instsrv.exe "Shinken-Poller" %PATH_INSTSRV%"\srvany.exe"
%PATH_INSTSRV%\instsrv.exe "Shinken-Reactionner" %PATH_INSTSRV%"\srvany.exe"
%PATH_INSTSRV%\instsrv.exe "Shinken-Broker" %PATH_INSTSRV%"\srvany.exe"
%PATH_INSTSRV%\instsrv.exe "Shinken-Receiver" %PATH_INSTSRV%"\srvany.exe"

echo Windows Registry Editor Version 5.00  > %tmp%\Shinken_registry.reg
echo. >> %tmp%\Shinken_registry.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Shinken-Arbiter\Parameters] >> %tmp%\Shinken_registry.reg
echo "Application"="c:\\Python26\\python.exe"  >> %tmp%\Shinken_registry.reg
echo "AppDirectory"="c:\\shinken"  >> %tmp%\Shinken_registry.reg
echo "AppParameters"="c:\\shinken\\bin\\shinken-arbiter.py -c c:\\shinken\\etc\\nagios-windows.ini"  >> %tmp%\Shinken_registry.reg
echo.  >> %tmp%\Shinken_registry.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Shinken-Broker\Parameters] >> %tmp%\Shinken_registry.reg
echo "Application"="c:\\Python26\\python.exe" >> %tmp%\Shinken_registry.reg
echo "AppDirectory"="c:\\shinken" >> %tmp%\Shinken_registry.reg
echo "AppParameters"="c:\\shinken\\bin\\shinken-broker.py -c c:\\shinken\\etc\\brokerd-windows.ini" >> %tmp%\Shinken_registry.reg
echo.  >> %tmp%\Shinken_registry.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Shinken-Poller\Parameters] >> %tmp%\Shinken_registry.reg
echo "Application"="c:\\Python26\\python.exe" >> %tmp%\Shinken_registry.reg
echo "AppDirectory"="c:\\shinken" >> %tmp%\Shinken_registry.reg
echo "AppParameters"="c:\\shinken\\bin\\shinken-poller.py -c c:\\shinken\\etc\\pollerd-windows.ini" >> %tmp%\Shinken_registry.reg
echo.  >> %tmp%\Shinken_registry.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Shinken-Reactionner\Parameters] >> %tmp%\Shinken_registry.reg
echo "Application"="c:\\Python26\\python.exe" >> %tmp%\Shinken_registry.reg
echo "AppDirectory"="c:\\shinken" >> %tmp%\Shinken_registry.reg
echo "AppParameters"="c:\\shinken\\bin\\shinken-reactionner.py -c c:\\shinken\\etc\\reactionnerd-windows.ini" >> %tmp%\Shinken_registry.reg
echo.  >> %tmp%\Shinken_registry.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Shinken-Reactionner\Parameters] >> %tmp%\Shinken_registry.reg
echo "Application"="c:\\Python26\\python.exe" >> %tmp%\Shinken_registry.reg
echo "AppDirectory"="c:\\shinken" >> %tmp%\Shinken_registry.reg
echo "AppParameters"="c:\\shinken\\bin\\shinken-reactionner.py -c c:\\shinken\\etc\\reactionnerd-windows.ini" >> %tmp%\Shinken_registry.reg
echo.  >> %tmp%\Shinken_registry.reg
echo [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Shinken-Scheduler\Parameters] >> %tmp%\Shinken_registry.reg
echo "Application"="c:\\Python26\\python.exe" >> %tmp%\Shinken_registry.reg
echo "AppDirectory"="c:\\shinken" >> %tmp%\Shinken_registry.reg
echo "AppParameters"="c:\\shinken\\bin\\shinken-scheduler.py -c c:\\shinken\\etc\\schedulerd-windows.ini" >> %tmp%\Shinken_registry.reg
echo.  >> %tmp%\Shinken_registry.reg

start /w reg inmport %tmp%\Shinken_registry.reg

pause
goto end

:remove
::Remove shinken
color C0
Echo
echo                ษอออออออออออออออออออออออออออออออออออป
echo                บ                                   บ
echo                บ     Shinken uninstallation        บ
echo                บ                                   บ
echo                บ                  Please wait ...  บ
echo                บ                                   บ
echo                ศอออออออออออออออออออออออออออออออออออผ

%PATH_INSTSRV%\instsrv.exe "Shinken-Arbiter" remove
%PATH_INSTSRV%\instsrv.exe "Shinken-Scheduler" remove
%PATH_INSTSRV%\instsrv.exe "Shinken-Poller" remove
%PATH_INSTSRV%\instsrv.exe "Shinken-Reactionner" remove
%PATH_INSTSRV%\instsrv.exe "Shinken-Broker" remove
%PATH_INSTSRV%\instsrv.exe "Shinken-Receiver" remove

echo Please remove the Shinken directory : %PATH_ROOT%
pause
exit

:end
color
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo   Please Go to http://www.shinken-monitoring.org/wiki/shinken_10min_start for how to launch the discovery pass
pause
