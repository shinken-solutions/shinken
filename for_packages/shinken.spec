Summary:        Python Monitoring tool
Name:           shinken
Version:        0.6.4
Release:        2%{?dist}
Source0:        http://shinken-monitoring.org/pub/%{name}-%{version}.tar.gz
License:        AGPLv3
Group:          Applications/System
URL:            http://www.shinken-monitoring.org/
Requires:       python, python-pyro, python-simplejson, python-sqlite2, logrotate, systemd-units, nmap
BuildRequires:  python-devel, systemd-units
BuildRoot:      %{_tmppath}/%{name}-%{version}-buildroot
Buildarch:      noarch
%global shinken_user shinken
%global shinken_group shinken
%global python_sitelib %(/usr/bin/python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

%description
Shinken is a new monitoring tool written in Python.
The main goal of Shinken is to allow users to have a fully flexible
architecture for their monitoring system that can easily scale to large
environments.
Shinken also provide interfaces with NDODB and Merlin database,
Livestatus connector Shinken does not include any human interfaces.

%package arbiter
Summary: Shinken Arbiter
Requires:python, python-pyro, chkconfig, logrotate, shinken

%description arbiter
Shinken arbiter daemon

%package reactionner
Summary: Shinken Reactionner
Requires:python, python-pyro, chkconfig, logrotate, shinken

%description reactionner
Shinken reactionner daemon

%package scheduler
Summary: Shinken Scheduler
Requires:python, python-pyro, chkconfig, logrotate, shinken

%description scheduler
Shinken scheduler daemon

%package poller
Summary: Shinken Poller
Requires:python, python-pyro, chkconfig, logrotate, shinken, nagios-plugins

%description poller
Shinken poller daemon

%package broker
Summary: Shinken Poller
Requires:python, python-pyro, chkconfig, logrotate, shinken

%description broker
Shinken broker daemon

%package receiver
Summary: Shinken Poller
Requires:python, python-pyro, chkconfig, logrotate, shinken

%description receiver
Shinken receiver daemon

%prep

%setup -q

# clean git files
find . -name '.gitignore' -exec rm -f {} \;
find . -name 'void_for_git' -exec rm -f {} \;

%build
/usr/bin/python -m compileall bin shinken

%install

install -d -m0755 %{buildroot}%{_sbindir}
install -d -m0755 %{buildroot}%{_mandir}/man3
install -p -m0755 bin/shinken-* %{buildroot}%{_sbindir}

install -d -m0755 %{buildroot}%{python_sitelib}/shinken
install -p shinken/*.py{,c} %{buildroot}%{python_sitelib}/shinken
cp -rf shinken/{core,daemons,objects,plugins,modules} %{buildroot}%{python_sitelib}/shinken

install -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/

install -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/objects
install -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/objects/{contacts,discovery,hosts,services}
install -p -m0644 fedora/objects/contacts/linux_admin.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/contacts/linux_admin.cfg
install -p -m0644 fedora/objects/hosts/localhost.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/hosts/localhost.cfg
install -p -m0644 fedora/objects/services/linux_disks.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/services/linux_disks.cfg



install -p -m0644 fedora/shinken-specific.cfg %{buildroot}%{_sysconfdir}/%{name}/
install -p -m0644 fedora/discovery*.cfg %{buildroot}%{_sysconfdir}/%{name}/
install -p -m0644 fedora/{commands,contactgroups,dependencies,nagios,timeperiods,shinken-specific,escalations,servicegroups,resource,templates}.cfg %{buildroot}%{_sysconfdir}/%{name}/

install -p -m0644 fedora/{brokerd,pollerd,reactionnerd,receiverd,schedulerd}.ini %{buildroot}%{_sysconfdir}/%{name}/

install -d -m0755 %{buildroot}%{_unitdir}
install -p -m0644 fedora/%{name}-arbiter.service %{buildroot}%{_unitdir}/%{name}-arbiter.service
install -p -m0644 fedora/%{name}-broker.service %{buildroot}%{_unitdir}/%{name}-broker.service
install -p -m0644 fedora/%{name}-reactionner.service %{buildroot}%{_unitdir}/%{name}-reactionner.service
install -p -m0644 fedora/%{name}-scheduler.service %{buildroot}%{_unitdir}/%{name}-scheduler.service
install -p -m0644 fedora/%{name}-receiver.service %{buildroot}%{_unitdir}/%{name}-receiver.service
install -p -m0644 fedora/%{name}-poller.service %{buildroot}%{_unitdir}/%{name}-poller.service

install -d -m0755 %{buildroot}%{_localstatedir}/log/%{name}/
install -d -m0755 %{buildroot}%{_localstatedir}/run/%{name}/
install -d -m0755 %{buildroot}%{_localstatedir}/lib/%{name}/

install -d -m0755 %{buildroot}%{_localstatedir}/log/%{name}/archives

install -d -m0755 %{buildroot}%{_libdir}/nagios/plugins
install  -m0755 libexec/*{.py,.pl,.sh} %{buildroot}%{_libdir}/nagios/plugins


install -d -m0755 %{buildroot}%{_sysconfdir}/logrotate.d
install -p -m0644 fedora/%{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

install -p -m0644 man/* %{buildroot}%{_mandir}/man3

install -d -m0755 %{buildroot}%{_sysconfdir}/default/
install -p -m0644 bin/default/shinken.in %{buildroot}%{_sysconfdir}/default/shinken

sed -i -e '1d;2i#!/usr/bin/python' %{buildroot}%{python_sitelib}/shinken/__init__.py

sed -i -e 's:#!/usr/bin/python::' %{buildroot}%{python_sitelib}/shinken/core/__init__.py
sed -i -e 's:#!/usr/bin/python::' %{buildroot}%{python_sitelib}/shinken/plugins/__init__.py


chmod +x %{buildroot}%{python_sitelib}/shinken/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/daemons/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/dummy_poller.py
chmod +x %{buildroot}%{python_sitelib}/shinken/objects/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/livestatus_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/status_dat_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/service_perfdata_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/merlindb_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/host_perfdata_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/couchdb_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/ndodb_oracle_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/shinken/modules/ndodb_mysql_broker/*.py

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
%doc README.rst COPYING Changelog THANKS db doc
%{_libdir}/nagios/plugins
%{_mandir}/man3/shinken-discovery*
%{_sbindir}/shinken-discovery
%config(noreplace) %{_sysconfdir}/logrotate.d/shinken
%config(noreplace) %{_sysconfdir}/default/shinken
%config(noreplace) %{_sysconfdir}/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/log/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/log/%{name}/archives
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/lib/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/run/%{name}

%changelog
* Sun May 29 2011 David Hannequin <david.hannequin@gmail.com> - 0.6.4-2
- Fix shinken configuration,
- Replace macro.

* Fri May 20 2011 David Hannequin <david.hannequin@gmail.com> - 0.6.4-1
- Update from upstream.

* Sun Apr 29 2011 David Hannequin <david.hannequin@gmail.com> - 0.6-1
- Fisrt release for fedora.
