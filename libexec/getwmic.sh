wget http://dev.zenoss.org/svn/trunk/inst/externallibs/wmi-1.3.14.tar.bz2 
tar xvf wmi-1.3.14.tar.bz2 
cd wmi-1.3.14/ 
sed -i 's/all: install/ZENHOME=..\/..\nall: install/' GNUmakefile
make 
#cp bin/* /usr/local/bin/ 
#cp lib/python/* /usr/local/lib/python 
