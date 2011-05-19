Summary:        Python Monitoring tool
Name:           shinken
Version:        0.6
Release:        1%{?dist}
Source0:        http://shinken-monitoring.org/pub/shinken-%{version}.tar.gz
License:        AGPLv3
Group:          Applications/System
URL:            http://www.shinken-monitoring.org/
Requires:       python >= 2.6, python-pyro, python-simplejson, python-sqlite2, logrotate, systemd-units, nmap
BuildRequires:  python-devel, systemd-units
BuildRoot:      %{_tmppath}/%{name}-%{version}-buildroot
# Patch to fix wrong path for shinken-broker
Patch0:         shinken-brokerd.ini.patch
# Patch to fix wrong path for shinken-poller
Patch1:         shinken-pollerd.ini.patch
# Patch to fix wrong path for shinken-reactionner
Patch2:         shinken-reactionnerd.ini.patch
# Patch to fix wrong path for shinken-receiver
Patch3:         shinken-receiverd.ini.patch
# Patch to fix wrong path for shinken-scheduler
Patch4:         shinken-schedulerd.ini.patch
# Patch to fix wrong path for shinken-discovery 
Patch5:         shinken-discovery.cfg.patch
# Patch to fix shinken configuration
Patch6:         shinken-specific.cfg.patch
# Patch to fix shinken configuration
Patch7:         shinken-servicegroups.cfg.patch
# Patch to fix shinken configuration
Patch8:         shinken-localhost.cfg.patch
Source1:        shinken.logrotate
Source2:        shinken-arbiter.service
Source3:        shinken-broker.service 
Source4:        shinken-reactionner.service 
Source5:        shinken-scheduler.service 
Source6:        shinken-receiver.service 
Source7:        shinken-poller.service 
Source8:        shinken-receiver.8shinken
Source9:        shinken-discovery.8shinken

%define shinken_user shinken
%define shinken_group shinken
%global __python /usr/bin/python
%define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

%description
Shinken is a new monitoring tool written in Python. 
The main goal of Shinken is to allow users to have a fully flexible 
architecture for their monitoring system that can easily scale to large 
environments.
Shinken also provide interfaces with NDODB and Merlin database, 
Livestatus connector Shinken does not include any human interfaces.

%package arbiter
Summary: Shinken Arbiter 
Requires:python >= 2.6, python-pyro, chkconfig, logrotate, shinken

%description arbiter
Shinken arbiter daemon

%package reactionner
Summary: Shinken Reactionner
Requires:python >= 2.6, python-pyro, chkconfig, logrotate, shinken

%description reactionner
Shinken reactionner daemon

%package scheduler
Summary: Shinken Scheduler
Requires:python >= 2.6, python-pyro, chkconfig, logrotate, shinken

%description scheduler
Shinken scheduler daemon

%package poller
Summary: Shinken Poller
Requires:python >= 2.6, python-pyro, chkconfig, logrotate, shinken, nagios-plugins

%description poller
Shinken poller daemon

%package broker
Summary: Shinken Poller
Requires:python >= 2.6, python-pyro, chkconfig, logrotate, shinken

%description broker
Shinken broker daemon

%package receiver
Summary: Shinken Poller
Requires:python >= 2.6, python-pyro, chkconfig, logrotate, shinken

%description receiver
Shinken receiver daemon

%prep

%setup -q -n %{name}-%{version}
%patch0 -p1  
%patch1 -p1  
%patch2 -p1  
%patch3 -p1  
%patch4 -p1  
%patch5 -p1  
%patch6 -p1  
%patch7 -p1  
%patch8 -p1  

# clean git files
find . -name '.gitignore' -exec rm -f {} \;
find . -name 'void_for_git' -exec rm -f {} \;

%build
%{__python} -m compileall bin shinken

%install
[ -d %{buildroot} -a "%{buildroot}" != "" ] && %{__rm} -rf %{buildroot}

%{__install} -d -m0755 %{buildroot}%{_sbindir}
%{__install} -d -m0755 %{buildroot}%{_mandir}/man3
%{__install} -p -m0755 bin/shinken-* %{buildroot}%{_sbindir}

%{__install} -d -m0755 %{buildroot}%{python_sitelib}/shinken
%{__install} -p shinken/*.py{,c} %{buildroot}%{python_sitelib}/shinken
%{__cp} -rf shinken/{core,daemons,objects,plugins,modules} %{buildroot}%{python_sitelib}/shinken

%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/

%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/objects
%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/objects/{contacts,discovery,hosts,services}
%{__install} -p -m0644 etc/objects/contacts/linux_admin.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/contacts/linux_admin.cfg
%{__install} -p -m0644 etc/objects/hosts/localhost.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/hosts/localhost.cfg
%{__install} -p -m0644 etc/objects/services/linux_disks.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/services/linux_disks.cfg



%{__install} -p -m0644 etc/shinken-specific.cfg %{buildroot}%{_sysconfdir}/%{name}/
%{__install} -p -m0644 etc/discovery*.cfg %{buildroot}%{_sysconfdir}/%{name}/
%{__install} -p -m0644 etc/{commands,contactgroups,dependencies,nagios,timeperiods,shinken-specific,escalations,servicegroups,resource,templates}.cfg %{buildroot}%{_sysconfdir}/%{name}/

%{__install} -p -m0644 etc/{brokerd,pollerd,reactionnerd,receiverd,schedulerd}.ini %{buildroot}%{_sysconfdir}/%{name}/

%{__install} -d -m0755 %{buildroot}%{_unitdir}
%{__install} -p -m0644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}-arbiter.service
%{__install} -p -m0644 %{SOURCE3} %{buildroot}%{_unitdir}/%{name}-broker.service
%{__install} -p -m0644 %{SOURCE4} %{buildroot}%{_unitdir}/%{name}-reactionner.service
%{__install} -p -m0644 %{SOURCE5} %{buildroot}%{_unitdir}/%{name}-scheduler.service
%{__install} -p -m0644 %{SOURCE6} %{buildroot}%{_unitdir}/%{name}-receiver.service
%{__install} -p -m0644 %{SOURCE7} %{buildroot}%{_unitdir}/%{name}-poller.service

%{__install} -d -m0755 %{buildroot}%{_localstatedir}/log/%{name}/
%{__install} -d -m0755 %{buildroot}%{_localstatedir}/log/%{name}/archives
%{__install} -d -m0755 %{buildroot}%{_localstatedir}/run/%{name}/
%{__install} -d -m0755 %{buildroot}%{_localstatedir}/lib/%{name}/

%{__install} -d -m0755 %{buildroot}%{_libdir}/nagios/plugins
%{__install}  -m0755 libexec/*{.py,.pl,.sh} %{buildroot}%{_libdir}/nagios/plugins


%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/logrotate.d
%{__install} -p -m0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

%{__install} -p -m0644 man/* %{buildroot}%{_mandir}/man3
%{__install} -p -m0644 %{SOURCE8} %{buildroot}%{_mandir}/man3
%{__install} -p -m0644 %{SOURCE9} %{buildroot}%{_mandir}/man3

%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/default/
%{__install} -p -m0644 bin/default/shinken.in %{buildroot}%{_sysconfdir}/default/shinken

sed -i -e '1d;2i#!/usr/bin/python' %{buildroot}%{python_sitelib}/shinken/__init__.py

chmod +x %{buildroot}%{python_sitelib}/shinken/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/__init__.py
chmod +x %{buildroot}%{python_sitelib}/shinken/daemons/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/dummy_poller.py
chmod +x %{buildroot}%{python_sitelib}/shinken/plugins/__init__.py
chmod +x %{buildroot}%{python_sitelib}/shinken/objects/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/livestatus_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/status_dat_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/service_perfdata_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/merlindb_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/host_perfdata_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/couchdb_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/ndodb_oracle_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/ndodb_mysql_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/core/__init__.py

chmod -x %{buildroot}%{python_sitelib}/shinken/{property,daemon,basemodule}.py

chmod -x %{buildroot}%{_libdir}/nagios/plugins/{getwmic.sh,nsca_client.py}

sed -i -e 's!/usr/local/shinken/libexec!%{_libdir}/nagios/plugins!' %{buildroot}%{_sysconfdir}/shinken/resource.cfg
sed -i -e 's!/usr/lib/nagios/plugins!%{_libdir}/nagios/plugins!' %{buildroot}%{_sysconfdir}/shinken/resource.cfg

sed -i -e 's!/usr/local/shinken/var/arbiterd.pid!/var/run/shinken/arbiterd.pid!' %{buildroot}%{_sysconfdir}/shinken/nagios.cfg
sed -i -e 's!command_file=/usr/local/shinken/var/rw/nagios.cmd!#command_file=/usr/local/shinken/var/rw/nagios.cmd!' %{buildroot}%{_sysconfdir}/shinken/nagios.cfg
sed -i -e 's!cfg_file=hostgroups.cfg!!' %{buildroot}%{_sysconfdir}/shinken/nagios.cfg

sed -i -e 's!,Windows_administrator!!' %{buildroot}%{_sysconfdir}/shinken/contactgroups.cfg


%clean
[ -d %{buildroot} -a "%{buildroot}" != "" ] && %{__rm} -rf %{buildroot}

%pre
# TODO : Adduser don't work 
echo Adding %{shinken_user} user ...
/usr/sbin/useradd -M -r -d %{_localstatedir}/log/%{name} -s /sbin/nologin -c "Shinken user" %{shinken_user} > /dev/null 2>&1 || :

%post arbiter
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%post broker
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%post poller
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%post reactionner
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%post scheduler
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%post receiver
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun arbiter 
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable shinken-arbiter.service > /dev/null 2>&1 || :
    /bin/systemctl stop shinken-arbiter.service > /dev/null 2>&1 || :
fi

%preun broker 
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable shinken-broker.service > /dev/null 2>&1 || :
    /bin/systemctl stop shinken-broker.service > /dev/null 2>&1 || :
fi

%preun poller 
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable shinken-poller.service > /dev/null 2>&1 || :
    /bin/systemctl stop shinken-poller.service > /dev/null 2>&1 || :
fi

%preun reactionner 
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable shinken-reactionner.service > /dev/null 2>&1 || :
    /bin/systemctl stop shinken-reactionner.service > /dev/null 2>&1 || :
fi

%preun scheduler 
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable shinken-scheduler.service > /dev/null 2>&1 || :
    /bin/systemctl stop shinken-scheduler.service > /dev/null 2>&1 || :
fi

%preun receiver 
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable shinken-receiver.service > /dev/null 2>&1 || :
    /bin/systemctl stop shinken-receiver.service > /dev/null 2>&1 || :
fi

%postun arbiter
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart shinken-arbiter.service >/dev/null 2>&1 || :
fi

%postun broker
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart shinken-broker.service >/dev/null 2>&1 || :
fi

%postun poller
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart shinken-poller.service >/dev/null 2>&1 || :
fi

%postun reactionner
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart shinken-reactionner.service >/dev/null 2>&1 || :
fi

%postun scheduler
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart shinken-scheduler.service >/dev/null 2>&1 || :
fi

%postun receiver
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart shinken-receiver.service >/dev/null 2>&1 || :
fi

%files arbiter
%defattr(-,root,root)
%{_unitdir}/%{name}-arbiter.service
%{_sbindir}/%{name}-arbiter*
%{_mandir}/man3/%{name}-arbiter*

%files reactionner
%defattr(-,root,root)
%{_unitdir}/%{name}-reactionner.service
%{_sbindir}/%{name}-reactionner*
%{_mandir}/man3/%{name}-reactionner*

%files scheduler
%defattr(-,root,root)
%{_unitdir}/%{name}-scheduler.service
%{_sbindir}/%{name}-scheduler*
%{_mandir}/man3/%{name}-scheduler*

%files poller
%defattr(-,root,root)
%{_unitdir}/%{name}-poller.service
%{_sbindir}/%{name}-poller*
%{_mandir}/man3/%{name}-poller*

%files broker
%defattr(-,root,root)
%{_unitdir}/%{name}-broker.service
%{_sbindir}/%{name}-broker*
%{_mandir}/man3/%{name}-broker*

%files receiver
%defattr(-,root,root)
%{_unitdir}/%{name}-receiver.service
%{_sbindir}/%{name}-receiver*
%{_mandir}/man3/%{name}-receiver*

%files
%defattr(-,root,root)
%{python_sitelib}/shinken
%doc README README.rst COPYING Changelog FROM_NAGIOS_TO_SHINKEN THANKS db doc
%{_mandir}/man3/shinken-discovery*
%{_sbindir}/shinken-discovery
%{_libdir}/nagios/plugins
%config(noreplace) %{_sysconfdir}/logrotate.d/shinken
%config(noreplace) %{_sysconfdir}/default/shinken
%config(noreplace) %{_sysconfdir}/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/log/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/lib/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/run/%{name}

%changelog
* Sun Apr 29 2010 David Hannequin <david.hannequin@gmail.com> - 0.6-1
- Fisrt release for fedora
