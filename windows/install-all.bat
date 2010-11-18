move /Y c:\shinken\windows\bin\shinken-poller c:\shinken\windows\bin\shinken-poller.py
move /Y c:\shinken\windows\bin\shinken-reactionner c:\shinken\windows\bin\shinken-reactionner.py
move /Y c:\shinken\windows\bin\shinken-scheduler c:\shinken\windows\bin\shinken-scheduler.py
move /Y c:\shinken\windows\bin\shinken-arbiter c:\shinken\windows\bin\shinken-arbiter.py
move /Y c:\shinken\windows\bin\shinken-broker c:\shinken\windows\bin\shinken-broker.py


c:\shinken\windows\instsrv.exe "Shinken-Arbiter" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Scheduler" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Poller" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Reactionner" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Broker" "c:\shinken\windows\srvany.exe"
