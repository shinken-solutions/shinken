#!/bin/sb

VER=1.3.16
wget http://dev.zenoss.org/svn/trunk/inst/externallibs/wmi-$VER.tar.bz2
tar xvf wmi-$VER.tar.bz2
cd wmi-$VER
sed -i 's!all: install!ZENHOME=../..\nall: install!' GNUmakefile
make
#cp bin/* /usr/local/bin/
#cp lib/python/* /usr/local/lib/python
