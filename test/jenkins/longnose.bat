ECHO RUNNING SHORT TESTS
@ECHO OFF

:: Copyright (C) 2009-2011 :
::     Gabes Jean, naparuba@gmail.com
::     Gerhard Lausser, Gerhard.Lausser@consol.de
::
:: This file is part of Shinken.
::
:: Shinken is free software: you can redistribute it and/or modify
:: it under the terms of the GNU Affero General Public License as published by
:: the Free Software Foundation, either version 3 of the License, or
:: (at your option) any later version.
::
:: Shinken is distributed in the hope that it will be useful,
:: but WITHOUT ANY WARRANTY; without even the implied warranty of
:: MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
:: GNU Affero General Public License for more details.
::
:: You should have received a copy of the GNU Affero General Public License
:: along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

REM this script is located in test/jenkins but needs to be run from test
REM find out the script's directory and then go to the dir one level above. 
CD %~dp0\..

REM clean up leftovers from a former run
DEL nosetests.xml
DEL coverage.xml
DEL .coverage

REM now run a list of test files in a loop. abort the loop
REM if a test failed.
FOR %%f IN (  ^
  test_services.py ^
  test_hosts.py ^
  test_host_missing_adress.py ^
  test_not_hostname.py ^
  test_bad_contact_call.py ^
  test_action.py ^
  test_config.py ^
  test_dependencies.py ^
  test_npcdmod.py ^
  test_problem_impact.py ^
  test_timeperiods.py ^
  test_command.py ^
  test_module_simplelog.py ^
  test_module_service_perfdata.py ^
  test_module_host_perfdata.py ^
  test_module_pickle_retention.py ^
  test_service_tpl_on_host_tpl.py ^
  test_db.py ^
  test_macroresolver.py ^
  test_complex_hostgroups.py ^
  test_resultmodulation.py ^
  test_satellites.py ^
  test_illegal_names.py ^
  test_service_generators.py ^
  test_notifway.py ^
  test_eventids.py ^
  test_obsess.py ^
  test_commands_perfdata.py ^
  test_notification_warning.py ^
  test_timeperiod_inheritance.py ^
  test_bad_timeperiods.py ^
  test_maintenance_period.py ^
  test_external_commands.py ^
  test_on_demand_event_handlers.py ^
  test_properties.py ^
  test_realms.py ^
  test_host_without_cmd.py ^
  test_escalations.py ^
  test_notifications.py ^
  test_contactdowntimes.py ^
  test_nullinheritance.py ^
  test_create_link_from_ext_cmd.py ^
  test_dispatcher.py
  test_business_correlator.py ^
  test_livestatus.py ) DO (
CALL :FUNC1 %%f
IF ERRORLEVEL 1 GOTO FAIL
)
REM now the long-running ones
FOR %%f IN (  ^
  test_maintenance_period.py ^
  test_downtimes.py ^
  test_acknowledge.py ) DO (
CALL :FUNC1 %%f
IF ERRORLEVEL 1 GOTO FAIL
)

REM combine the single coverage files
C:\Python27\Scripts\coverage xml --omit=/usr/lib
EXIT /B 0

:FAIL
ECHO one of the tests failed. i give up.
EXIT /B 1

REM here is where the tests actually run
:FUNC1 
C:\Python27\Scripts\nosetests -v -s --with-xunit --with-coverage %1
IF ERRORLEVEL 1 goto :EOF
ECHO successfully ran %1
GOTO :EOF [Return to Main]
