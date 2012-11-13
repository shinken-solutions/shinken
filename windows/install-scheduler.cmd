rem installation of shinken scheduler service using installutil....
rem (c) 2012 October, By VEOSOFT, Jean-fran�ois BUTKIEWICZ
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

set iutil="%systemroot%\microsoft.net\framework\v2.0.50727\installutil.exe"
set tplpath=@@INSTALLDIR@@

echo Setting the shinken-scheduler.py from standard distro
copy /Y .\bin\shinken-scheduler .\bin\shinken-scheduler.py
echo Shinken Scheduler installed...
echo Updating the program path references
rem replacing the @@installdir@@ by %cd%
cscript replace_installdir.vbs shinken_scheduler.exe.config %tplpath% "%cd%"
cscript replace_installdir.vbs .\etc\schedulerd-windows.ini %tplpath% "%cd%"
cscript replace_installdir.vbs .\bin\start_scheduler.cmd %tplpath% "%cd%"

echo installing the shinken scheduler service...
%iutil% Shinken_scheduler.exe
if "%errorlevel%"=="0" goto nextstep1
echo Error launched during installation of shinken scheduler.
echo Installation aborted.
exit 10

:nextstep1
exit 0