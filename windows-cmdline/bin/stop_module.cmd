@echo off
Rem ----------------------------------------------------------------------------
Rem stop_module.cmd
Rem ----------------------------------------------------------------------------
Rem stop a Shinken module for Windows
Rem ----------------------------------------------------------------------------
Rem (c) 2013 - IPM France
Rem ----------------------------------------------------------------------------

Rem Parameters
SET python_exe=@@pythonDir@@\python.exe

Rem Commande line parameters
SET module=%1
SET test=

if "%1" == "" SET /P module=Identifiant du module ?
if "%module%" == "" goto syntax

Echo ***************************************************************************
Echo Stopping Shinken module : %module%
Echo ***************************************************************************
TASKKILL /T /F /FI "WINDOWTITLE eq Shinken %module%"
Goto End

:pythonNotInstalled
echo ***************************************************************************
echo Python is not installed. Shinken can not be started !
echo ***************************************************************************
goto End

:Syntax
Echo ***************************************************************************
Echo Syntax :
Echo  stop_module module_name
Echo   stop the module named 'module_name'
Echo ***************************************************************************
Echo  Current parameters :
Echo   module : %module%
Echo ***************************************************************************
goto End

:End
