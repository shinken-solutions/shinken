#!/bin/sh
sudo rm -fr /usr/local/lib/python2.6/dist-packages/Shinken-0.1.99-py2.6.egg
sudo rm  -fr /usr/local/bin/shinken-*
sudo rm  -fr /usr/bin/shinken-*
sudo rm -fr build
sudo rm -fr Shinken.egg-info
sudo rm -fr dist
sudo rm -fr /etc/shinken
sudo rm -fr /var/lib/shinken
sudo rm -fr var/*.debug
sudo rm -fr var/*.log
sudo rm -fr var/service-perfdata
sudo rm -fr var/*.dat
sudo rm -fr var/*.profile
sudo rm -fr var/*.cache
sudo rm -fr var/rw/*cmd
sudo rm -fr /tmp/retention.dat

#Then kill remaining processes
killall -9 python2.6
killall -9 python