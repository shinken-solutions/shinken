rem installation of shinken reactionner service using installutil....
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

echo Setting the shinken-reactionner.py from standard distro
copy /Y .\bin\shinken-reactionner .\bin\shinken-reactionner.py
echo Shinken Reactionner installed...
echo Updating the program path references
rem replacing the @@installdir@@ by %cd%
cscript replace_installdir.vbs shinken_reactionner.exe.config %tplpath% "%cd%"
cscript replace_installdir.vbs .\etc\reactionnerd-windows.ini %tplpath% "%cd%"
cscript replace_installdir.vbs .\bin\start_reactionner.cmd %tplpath% "%cd%"

echo installing the shinken reactionner service...
%iutil% Shinken_reactionner.exe
if "%errorlevel%"=="0" goto nextstep1
echo Error launched during installation of shinken reactionner.
echo Installation aborted.
exit 10

:nextstep1
exit 0
