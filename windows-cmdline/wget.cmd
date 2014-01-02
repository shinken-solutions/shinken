@Echo OFF
SetLocal EnableDelayedExpansion
Set Var=%1
Set Var=!Var:http://=!
Set Var=!Var:/=,!
Set Var=!Var:%%20=?!
Set Var=!Var: =?!
Call :LOOP !var!
Echo.Downloading: %1 to %~p0!FN!
powershell.exe -Command (new-object System.Net.WebClient).DownloadFile('%1','%~p0!FN!')
GoTo :EOF
:LOOP
If "%1"=="" GoTo :EOF
Set FN=%1
Set FN=!FN:?= !
Shift
GoTo :LOOP