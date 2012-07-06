#!/bin/sh
sudo rm -fr /usr/local/lib/python2.*/dist-packages/Shinken-*-py2.6.egg
sudo rm -fr /usr/local/lib/python2.*/dist-packages/shinken
sudo rm -fr /usr/local/bin/shinken-*
sudo rm -fr /usr/bin/shinken-*
sudo rm -fr build
sudo rm -fr Shinken.egg-info
sudo rm -fr dist
sudo rm -fr /etc/shinken
sudo rm -fr /etc/init.d/shinken*
sudo rm -fr /var/lib/shinken
sudo rm -fr /var/log/shinken
sudo rm -fr test/var/*.pid
sudo rm -fr var/*.debug
sudo rm -fr var/*.log*
sudo rm -fr var/*.pid
sudo rm -fr var/service-perfdata
sudo rm -fr var/*.dat
sudo rm -fr var/*.profile
sudo rm -fr var/*.cache
sudo rm -fr var/rw/*cmd
sudo rm -fr /tmp/retention.dat
sudo rm -fr /tmp/*debug
sudo rm -fr test/tmp/livelogs*
sudo rm -fr /etc/default/shinken
sudo rm -fr bin/default/shinken

# Then kill remaining processes
# first ask a easy kill, to let them close their sockets!
killall python2.6 2> /dev/null
killall python 2> /dev/null
killall /usr/bin/python 2> /dev/null

# I give them 2 sec to close
sleep 3

# Ok, now I'm really angry if there is still someboby alive :)
sudo killall -9 python2.6 2> /dev/null
sudo killall -9 python 2> /dev/null
sudo killall -9 /usr/bin/python 2> /dev/null

echo ""
