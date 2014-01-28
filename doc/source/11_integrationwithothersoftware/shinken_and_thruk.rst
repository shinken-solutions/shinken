.. _shinken_and_thruk:

=====
Thruk
=====

Shinken installation 
~~~~~~~~~~~~~~~~~~~~~


Create a new user shinken:

  
::

  adduser shinken
  
.. important::  Be sure to create a home directory for shinken user. If not, you will not be able to start the shinken arbiter.

Next step retrieve the last version of shinken and uncompress it:

  
::

  tar xfv shinken-0.5.1.tar.gz
  
Get into this directory and install it on your system:

  
::

  sudo python setup.py install --install-scripts=/usr/bin
  
You will get new binaries into /usr/bin (files shinken-*) and some new directory (/etc/shinken, /var/lib/shinken).

Now, to unleash the daemons (ah ah ah!), you can use the script in init.d, or create your own script like:

  
::

  root@Enclume:/etc/init.d# more shinken.sh 
  #!/bin/bash
  cd /etc/init.d
  
  for script in shinken-scheduler shinken-poller shinken-reactionner shinken-broker shinken-arbiter 
  do
    ./$script $1
  done
  
Start your deamon:

  
::

  /etc/init.d/shinken.sh start
  
Now check that the shinken processes are up and running:

  
::

  patrice@Enclume:~/tmp/shinken-0.4$ ps -u shinken
  PID TTY          TIME CMD
  4358 ?        00:00:09 shinken-schedul
  4367 ?        00:00:10 shinken-poller
  4372 ?        00:00:00 shinken-poller
  4380 ?        00:00:09 shinken-reactio
  4385 ?        00:00:00 shinken-reactio
  4949 ?        00:00:13 shinken-broker
  4989 ?        00:00:00 shinken-poller
  4990 ?        00:00:00 shinken-poller
  4993 ?        00:00:00 shinken-poller
  4996 ?        00:00:18 shinken-broker
  4997 ?        00:00:00 shinken-broker
  5001 ?        00:00:00 shinken-reactio
  5004 ?        00:00:00 shinken-poller
  5018 ?        00:00:10 shinken-arbiter
  


Configure Thruk 
~~~~~~~~~~~~~~~~


Get a fresh copy of Thruk (http://www.thruk.org/download.html) then uncompress your version and get into the root directory.

Now, create a new file named **thruk_local.conf**. Bellow, the content of this file:

  
::

  ~/tmp/Thruk-0.74$ cat thruk_local.conf
  ######################################
  # Backend Configuration, enter your backends here
  <Component Thruk::Backend>
    <peer>
        name   = Shinken
        type   = livestatus
        <options>
            peer    = 127.0.0.1:50000
       </options>
    </peer>
  #    <peer>
  #        name   = External Icinga
  #        type   = livestatus
  #        <options>
  #            peer    = 172.16.0.2:9999
  #       </options>
  #    </peer>
  </Component>
  
Now launch the Thruk daemon:

  
::

  ~/tmp/Thruk-0.74/script$ ./thruk_server.pl
  You can connect to your server at http://enclume:3000
  
.. important::  This article doesn't describe a true Thruk installation with Apache connection. Please refer `Thruk documentation`_ to get a cleaner installation.

Now, run your favorite internet browser with http://localhost:3000 and enjoy your Shinken installation !



.. image:: /_static/images//shinken_with_thruk.png
   :scale: 90 %


.. _Thruk documentation: http://www.thruk.org/documentation.html
