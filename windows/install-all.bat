move /Y c:\shinken\bin\shinken-poller c:\shinken\bin\shinken-poller.py
move /Y c:\shinken\bin\shinken-reactionner c:\shinken\bin\shinken-reactionner.py
move /Y c:\shinken\bin\shinken-scheduler c:\shinken\bin\shinken-scheduler.py
move /Y c:\shinken\bin\shinken-arbiter c:\shinken\bin\shinken-arbiter.py
move /Y c:\shinken\bin\shinken-broker c:\shinken\bin\shinken-broker.py


c:\shinken\windows\instsrv.exe "Shinken-Arbiter" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Scheduler" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Poller" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Reactionner" "c:\shinken\windows\srvany.exe"

c:\shinken\windows\instsrv.exe "Shinken-Broker" "c:\shinken\windows\srvany.exe"
