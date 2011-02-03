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

REM USAGE: RUNTESTS LIST_WITH_TESTS.txt [NO]COVERAGE [NO]PYLINT

@ECHO OFF
ECHO RUNNING SHORT TESTS

SET TESTLIST=%~dpnx1
SET COVERAGE=%2
SET PYLINT=%3

IF NOT (%COVERAGE%) == (COVERAGE) SET COVERAGE=NOCOVERAGE
IF NOT (%PYLINT%) == (PYLINT) SET PYLINT=NOPYLINT
IF (%PYTHONVERS%) == (%PYTHONVERS%) SET PYTHONVERS=27
IF (%PYTHONVERS%) == (271) SET PYTHONVERS=27
IF (%PYTHONVERS%) == (266) SET PYTHONVERS=26
IF (%PYTHONVERS%) == (246) SET PYTHONVERS=24
SET PYTHONBIN=C:\Python%PYTHONVERS%
SET PYTHONTOOLS=C:\Python%PYTHONVERS%\Scripts

REM This script is located in test/jenkins but needs to be run from test.
REM Find out the script's directory and then go to the dir one level above. 
CD %~dp0\..

REM Clean up leftovers from a former run
DEL nosetests.xml
IF %COVERAGE% == COVERAGE DEL coverage.xml
IF %COVERAGE% == COVERAGE DEL .coverage

REM Now run a list of test files in a loop. Abort the loop if a test failed.
REM If this is a simple functional test, abort the loop if a test failed.
REM For a run with coverage, execute them all.
FOR /F "eol=# tokens=1" %%f in (%TESTLIST%) DO (
CALL :FUNC1 %%f
IF %COVERAGE% == NOCOVERAGE IF %PYLINT% == NOPYLINT IF ERRORLEVEL 1 GOTO FAIL
)

REM Merge the single coverage files
IF %COVERAGE% == COVERAGE %PYTHONTOOLS%\coverage xml --omit=/usr/lib
REM Run Pylint
CD ..
IF %PYLINT% == PYLINT %PYTHONTOOLS%\pylint -f parseable --disable=C0111,C0103,W0201,E1101 shinken shinken\modules shinken\modules\* > pylint.txt
EXIT /B 0

:FAIL
ECHO One of the tests failed, so i give up.
EXIT /B 1

REM Here is where the tests actually run
:FUNC1 
ECHO I RUN %1
IF %COVERAGE% == NOCOVERAGE IF %PYLINT% == NOPYLINT %PYTHONTOOLS%\nosetests -v -s --with-xunit %1
IF %COVERAGE% == COVERAGE %PYTHONTOOLS%\nosetests -v -s --with-xunit --with-coverage %1
IF ERRORLEVEL 1 goto :EOF
ECHO successfully ran %1
GOTO :EOF [Return to Main]

