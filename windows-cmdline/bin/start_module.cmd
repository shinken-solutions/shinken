@echo off
Rem ----------------------------------------------------------------------------
Rem start_module.cmd
Rem ----------------------------------------------------------------------------
Rem start a Shinken module for Windows
Rem ----------------------------------------------------------------------------
Rem (c) 2013 - IPM France
Rem ----------------------------------------------------------------------------

Rem Parameters
SET python_exe=c:\python27\python.exe

Rem Commande line parameters
SET module=%1
SET test=

if "%1" == "" SET /P module=Identifiant du module ?
if "%module%" == "test" SET test=-v
if "%module%" == "test" SET module=arbiter
if "%module%" == "" goto syntax

Rem Check if Python is installed
if not exist %python_exe% goto pythonNotInstalled

Rem Set Shinken command line parameters
SET parameters=-c C:\Shinken\etc\%module%d-windows.ini
if "%module%" == "arbiter" SET parameters=-c C:\Shinken\etc\nagios-windows.cfg -c C:\Shinken\etc\shinken-specific-windows.cfg

if "%test%" == "-v" Goto checkShinken

Echo ***************************************************************************
Echo Starting Shinken module '%module%' ...
start /SEPARATE "Shinken %module%" %python_exe% C:\Shinken\bin\shinken-%module%.py %test% %parameters%
If ERRORLEVEL 1 Goto startError
Echo Shinken module '%module%' started.
Echo ***************************************************************************
Goto End

:checkShinken
SET module=arbiter
SET parameters=-c C:\Shinken\etc\nagios-windows.cfg -c C:\Shinken\etc\shinken-specific-windows.cfg
Echo ***************************************************************************
Echo Starting Shinken configuration check ...
%python_exe% C:\Shinken\bin\shinken-%module%.py %test% %parameters%
If ERRORLEVEL 1 Goto startError
Echo Shinken module '%module%' started.
Echo ***************************************************************************
Goto End

:startError
Echo Shinken module '%module%' not started, return code : %ERRORLEVEL%
Echo ***************************************************************************
Goto End

:pythonNotInstalled
echo ***************************************************************************
echo Python is not installed. Shinken can not be started !
echo ***************************************************************************
goto End

:Syntax
Echo ***************************************************************************
Echo Syntax :
Echo  start_module module_name
Echo   start the module named 'module_name'
Echo
Echo  start_module test
Echo   start the arbiter module for testing current configuration
Echo ***************************************************************************
Echo  Current parameters :
Echo   module : %module%
Echo   test : %test%
Echo ***************************************************************************
goto End

:End
