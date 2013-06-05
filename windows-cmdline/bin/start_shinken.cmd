@echo off
REM ----------------------------------------------------------------------------
REM start_shinken.cmd
REM ----------------------------------------------------------------------------
REM Start all Shinken modules for Windows
REM ----------------------------------------------------------------------------
REM Script usage : 
REM 1/ start_shinken.cmd console, uses the shinken-console.reg file to configure
REM shinken consoles (set position and text colour for each console window)
REM 2/ start_shinken.cmd test, starts Shinken arbiter module in test mode to check
REM the configuration
REM 3/ start_shinken.cmd, starts all Shinken modules
REM ----------------------------------------------------------------------------
REM (c) 2013 - IPM France
REM ----------------------------------------------------------------------------

If "%1%" == "console" Goto Console

:Test
Echo ***************************************************************************
Echo Testing Shinken configuration ...
Echo ***************************************************************************
call .\start_module.cmd test
If ERRORLEVEL 1 Goto startError
Echo Shinken configuration ok.
Echo ***************************************************************************
If "%1%" == "test" Goto End
Echo Starting Shinken modules ...

:startShinken
call .\start_module.cmd arbiter
call .\start_module.cmd broker
call .\start_module.cmd poller
call .\start_module.cmd reactionner
call .\start_module.cmd receiver
call .\start_module.cmd scheduler
Rem call .\start_module.cmd skonf
Echo Shinken modules started.
Echo ***************************************************************************
Goto End

:startError
Echo Shinken configuration not ok (%ERRORLEVEL%) ! No modules were started.
Echo ***************************************************************************
Goto End

:Console
Echo ***************************************************************************
Echo Setting Shinken console position and configuration ...
Echo ***************************************************************************
REG IMPORT .\shinken-console.reg
If ERRORLEVEL 1 Goto consoleError
Echo Shinken console configured.
Echo ***************************************************************************
Goto End

:consoleError
Echo Shinken console not configured (%ERRORLEVEL%) !
Echo ***************************************************************************
Goto End

:End
