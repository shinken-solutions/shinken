.. _redhat_thruk_pnp4nagios_howto:



====================================================
Shinken on RedHat 6 with Thruk and PNP4Nagios HOWTO 
====================================================


We'll install Shinken with the Thruk web user interface and the PNP4Nagios graphs. We'll also configure SNMP, NRPE and SSH access to the monitored hosts.

Packages will be installed in /opt unless they are already packaged.



Shinken 
========


Prepare sources:

::

  mkdir /opt/shinken-dl/
  wget http://www.shinken-monitoring.org/pub/shinken-1.4.tar.gz
  tar xzf shinken-1.4.tar.gz


Installation:

::

  cd /opt/shinken-dl/shinken-1.4/
  TARGET=/opt/shinken SKUSER=shinken SKGROUP=shinken ./install -i
  ./install -p nagios-plugins
  ./install -p manubulon  # snmp checks
  ./install -p check_netint  # network/trafic checks


Mandatory configuration:
  * In ``/opt/shinken/etc/shinken-specific.cfg``, define ``auth_secret`` with a random password
  * Fix path to the ``mail`` command: 

::

  sed -i -e 's,/usr/bin/mail,mail,' /opt/shinken/etc/commands.cfg


Optional configuration:
  * Change in ``/opt/shinken/etc/nagios.cfg``:
  * Avoid flapping due to having the same timeout for service checks (UNKNOWN) and for check_https (CRITICAL): 

::

  service_check_timeout=60

..

  * Support long event handlers:

::

  event_handler_timeout=300


..

  * Change in templates.cfg:
  * If you need hosts that can't be ping'd, comment out in ``generic-host``:

::

      #check_command                  check_host_alive
  
  
* Notifications may be sent even if the host is out of its notification hours, but you can force host>service inheritance by commenting this in ``generic-service``:

::

      #notification_period             24x7  

..

* Same for check periods:

::

      #check_period             24x7

..
  
* Notifications are sent every hour by default, you can change that to every day:

::

      notification_interval           1440
  
..

* Add 'u,f' to :ref:`service notifications <notificationway>` in ``notificationway:service_notification_options``
* If you need a global event handler (workaround `issue 717`_), modify ``generic-service``:

::

          event_handler_enabled           1
          event_handler                   test_log_service
  
  


Mail 
=====


In case you need to configure the Shinken mail sender:

::

    echo "shinken   shinken-notifications@mydomain.tld" >> /etc/postfix/canonical
    postmap /etc/postfix/canonical
    cat <<'EOF' >> /etc/postfix/main.cf
    sender_canonical_maps = hash:/etc/postfix/canonical
    EOF
  
  
Shinken also sends mail to none@localhost which is the contact for user 'guest'.
This triggers bounces, so you can auto-trash these mails:

::

    echo 'none: /dev/null' >> /etc/aliases && newaliases
  
  


Thruk 
======


Follow :ref:`use_with_thruk <use_with_thruk>`:
  * Installation from RPM (http://www.thruk.org/download.html):

::

  rpm -ivh http://www.thruk.org/files/pkg/v1.76-3/rhel6/x86_64/thruk-1.76-3.rhel6.x86_64.rpm

* :ref:`SELinux configuration <use_with_thruk#install_thrukd>` (or disable it with ``setenforce Permissive``)
* :ref:`Using Shinken with Thruk <use_with_thruk#using_shinken_with_thruk>`

Thruk is available at: http://YOUR_SHINKEN_IP/thruk/



PNP4Nagios 
===========


Follow :ref:`use_with_pnp <use_with_pnp>`:
  * Go to the Shinken sources and set the installation path in ``/opt/shinken-dl/shinken-1.4/install.d/shinken.conf``:

::
  
  PNPPREFIX=/opt/pnp4nagios

* :ref:`Install PNP4Nagios automatically <use_with_pnp#install_pnp4nagios_automatically>`
* :ref:`Using Shinken with PNP4Nagios <use_with_pnp#using_shinken_with_pnp4nagios>`

PNP4Nagios is now linked from Thruk though ``action_url``, and more generally available at http://YOUR_SHINKEN_IP/pnp4nagios/



Monitored hosts 
================




SNMP 
-----


Let's enable SNMP on our monitored hosts.

  
::

  
  # Install SNMP server:
  yum install net-snmp
  
  # Read-only access:
  echo "rocommunity public" > /etc/snmp/snmpd.conf
  
  # Don't log each SNMP request:
  [ -e /etc/sysconfig/snmpd ]         && echo 'OPTIONS="-LS0-4d -Lf /dev/null -p /var/run/snmpd.pid"'  >> /etc/sysconfig/snmpd  # RHEL6
  [ -e /etc/sysconfig/snmpd.options ] && echo 'OPTIONS="-LSwd -Lf /dev/null -p /var/run/snmpd.pid -a"' >> /etc/sysconfig/snmpd.options  # RHEL5
  
  # Launch SNMP server on startup:
  chkconfig snmpd on
  service snmpd restart




NRPE 
-----


Let's enable NRPE on our monitored hosts (port 5666).

  
::

  
  # Activate the EPEL6 repository - install:
  http://download.fedoraproject.org/pub/epel/6/i386/repoview/epel-release.html
  
  # Install NRPE server:
  yum install nrpe
  
  # Allow access from Shinken poller:
  sed -i -e 's/^allowed_hosts=.*/allowed_hosts=127.0.0.1,YOUR_SHINKEN_IP/' /etc/nagios/nrpe.cfg
  
  # Launch NRPE server on startup:
  chkconfig nrpe on
  service nrpe start


Enable and configure remote checks in ``/etc/nagios/nrpe.cfg``.



SSH 
----


Let's give Shinken access to our monitored hosts, e.g. to execute event handlers or run NRPE through SSH:

On the Shinken Server, generate a SSH key ``/home/shinken/.ssh/id_rsa``:

::

  sudo -u shinken ssh-keygen</code>
  
On each monitored host:

* Create a ''monitaction'' user with limited rights, accessed by Shinken:<code>

::

  useradd -r monitaction -m
  mkdir -pm 700 ~monitaction/.ssh/
  echo "ssh-rsa AAAAB3...EKtMx/9o0ApJl shinken@rh6" > ~monitaction/.ssh/authorized_keys  # from /home/shinken/.ssh/id_rsa.pub
  chown -R monitaction: ~monitaction/.ssh/
  mkdir -pm 750 /etc/sudoers.d/
  touch /etc/sudoers.d/local
  chmod 440 /etc/sudoers.d/local

* Edit ''/etc/sudoers.d/local'' to give it privileges, e.g.:

::
  
  Defaults !requiretty
  monitaction ALL= NOPASSWD: /sbin/service jbossas7 *
  monitaction ALL= NOPASSWD: /sbin/service thunderhead *
  monitaction ALL= NOPASSWD: /sbin/service httpd *


Test from the Shinken server:

::

  ssh -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null 192.168.X.X -l monitaction -t sudo /sbin/service httpd reload


Of course, open firewall access from the Shinken server to the monitored host's SSH.



Extra: Graphite 
================


If you're interested in Graphite, you can start from this basis:

  * :ref:`network_based_modules_-_graphite_graphing <the_broker_modules#network_based_modules_-_graphite_graphing>`
  * :ref:`use_with_graphite <use_with_graphite>`

Additional configuration:

::

      echo "/opt/graphite/bin/carbon-cache.py start" >> /etc/rc.local
      chgrp apache /opt/graphite/storage/
      chmod g+w /opt/graphite/storage/
      sudo -u apache /opt/graphite/bin/python /opt/graphite/webapp/graphite/manage.py runserver  # TODO: access from Apache
      # Remove the numerous dummy network graphs creating by mistake by Graphite:
      echo "rm -f /opt/graphite/storage/whisper/*/shinken/NetworkUsage/*_13????????_.wsp" >> /etc/cron.daily/graphite-cleanup
      chmod 755 /etc/cron.daily/graphite-cleanup
  

.. _issue 717: https://github.com/naparuba/shinken/issues/717
