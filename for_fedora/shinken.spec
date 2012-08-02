Summary:        Python Monitoring tool
Name:           shinken
Version:        0.8.1
Release:        1%{?dist}
URL:            http://%{name}-monitoring.org
Source0:        http://%{name}-monitoring.org/pub/%{name}-%{version}.tar.gz
Source1:        shinken-admin.8shinken
License:        AGPLv3+

Requires:       python
Requires:       python-pyro
Requires:       python-simplejson
Requires:       python-sqlite2
Requires:       systemd-units
Requires:       nmap
BuildRequires:  python-devel
BuildRequires:  systemd-units
BuildRoot:      %{_tmppath}/%{name}-%{version}-buildroot
Buildarch:      noarch

%global shinken_user nagios
%global shinken_group nagios
%global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")


%description
Shinken is a new monitoring tool written in Python.
The main goal of Shinken is to allow users to have a fully flexible
architecture for their monitoring system that can easily scale to large
environments.
Shinken also provide interfaces with NDODB and Merlin database,
Livestatus connector Shinken does not include any human interfaces.

%package arbiter
Summary: Shinken Arbiter
Requires: %{name} = %{version}-%{release}

%description arbiter
Shinken arbiter daemon

%package reactionner
Summary: Shinken Reactionner
Requires: %{name} = %{version}-%{release}

%description reactionner
Shinken reactionner daemon

%package scheduler
Summary: Shinken Scheduler
Requires: %{name} = %{version}-%{release}

%description scheduler
Shinken scheduler daemon

%package poller
Summary: Shinken Poller
Requires: %{name} = %{version}-%{release}

%description poller
Shinken poller daemon

%package broker
Summary: Shinken Poller
Requires: %{name} = %{version}-%{release}
Requires: mysql-connector-python
Requires: python-redis
Requires: python-memcached

%description broker
Shinken broker daemon

%package receiver
Summary: Shinken Poller
Requires: %{name} = %{version}-%{release}

%description receiver
Shinken receiver daemon

%prep

%setup -q

# clean git files
find . -name '.gitignore' -exec rm -f {} \;

# Check confuguration files
sed -i -e 's!plugins-path=/usr/lib/nagios/plugins!plugins-path=%{_libdir}/nagios/plugins!' setup.{cfg,py}
sed -i -e 's!./$SCRIPT!python ./$SCRIPT!' test/quick_tests.sh

chmod +rx %{name}/webui/plugins/impacts/impacts.py

%build

CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build

%install

%{__python} setup.py install -O1 --skip-build --root %{buildroot} --install-scripts=/usr/sbin/

install -d -m0755 %{buildroot}%{_sbindir}
install -p -m0755 bin/shinken-{arbiter,admin,discovery,broker,poller,reactionner,receiver,scheduler} %{buildroot}%{_sbindir}

install -d -m0755 %{buildroot}%{python_sitelib}/%{name}
install -p %{name}/*.py %{buildroot}%{python_sitelib}/%{name}
cp -rf %{name}/{clients,core,misc,modules,objects,plugins,webui} %{buildroot}%{python_sitelib}/%{name}

install -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/
rm -rf %{buildroot}%{_sysconfdir}/%{name}/*

install -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/objects
install -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/objects/{contacts,discovery,hosts,services}

install -p -m0644 for_fedora/etc/objects/contacts/nagiosadmin.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/contacts/nagiosadmin.cfg
install -p -m0644 for_fedora/etc/objects/hosts/localhost.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/hosts/localhost.cfg
install -p -m0644 for_fedora/etc/objects/services/linux_disks.cfg %{buildroot}%{_sysconfdir}/%{name}/objects/services/linux_disks.cfg
install -p -m0644 for_fedora/etc/htpasswd.users %{buildroot}%{_sysconfdir}/%{name}/htpasswd.users
install -p -m0644 for_fedora/etc/%{name}-specific.cfg %{buildroot}%{_sysconfdir}/%{name}/
install -p -m0644 for_fedora/etc/discovery*.cfg %{buildroot}%{_sysconfdir}/%{name}/
install -p -m0644 for_fedora/etc/{commands,contactgroups,nagios,timeperiods,%{name}-specific,escalations,servicegroups,resource,templates}.cfg %{buildroot}%{_sysconfdir}/%{name}/
install -p -m0644 for_fedora/etc/{brokerd,pollerd,reactionnerd,receiverd,schedulerd}.ini %{buildroot}%{_sysconfdir}/%{name}/

install -d -m0755 %{buildroot}%{_unitdir}
install -p -m0644 for_fedora/systemd/%{name}-arbiter.service %{buildroot}%{_unitdir}/%{name}-arbiter.service
install -p -m0644 for_fedora/systemd/%{name}-broker.service %{buildroot}%{_unitdir}/%{name}-broker.service
install -p -m0644 for_fedora/systemd/%{name}-reactionner.service %{buildroot}%{_unitdir}/%{name}-reactionner.service
install -p -m0644 for_fedora/systemd/%{name}-scheduler.service %{buildroot}%{_unitdir}/%{name}-scheduler.service
install -p -m0644 for_fedora/systemd/%{name}-receiver.service %{buildroot}%{_unitdir}/%{name}-receiver.service
install -p -m0644 for_fedora/systemd/%{name}-poller.service %{buildroot}%{_unitdir}/%{name}-poller.service

install -d -m0755 %{buildroot}%{_sysconfdir}/logrotate.d
install -p -m0644 for_fedora/%{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/shinken

install -d -m0755 %{buildroot}%{_sysconfdir}/tmpfiles.d
install -m0644  for_fedora/%{name}-tmpfiles.conf %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf

install -d -m0755 %{buildroot}%{_localstatedir}/log/%{name}
install -d -m0755 %{buildroot}%{_localstatedir}/log/%{name}/archives
install -d -m0755 %{buildroot}%{_localstatedir}/lib/%{name}

install -d -m0755 %{buildroot}%{_libdir}/%{name}/plugins
install  -m0755 libexec/*{.py,.pl} %{buildroot}%{_libdir}/%{name}/plugins

install -d -m0755 %{buildroot}%{_mandir}/man3
install -p -m0644 doc/man/* %{buildroot}%{_mandir}/man3
install -p -m0644 %{SOURCE1} %{buildroot}%{_mandir}/man3

sed -i -e '1d;2i#!/usr/bin/python' %{buildroot}%{python_sitelib}/%{name}/__init__.py
sed -i -e 's:#!/usr/bin/python::' %{buildroot}%{python_sitelib}/%{name}/core/__init__.py
sed -i -e 's:#!/usr/bin/python::' %{buildroot}%{python_sitelib}/%{name}/plugins/__init__.py

sed -i -e '1d;2i#!/usr/bin/python' %{buildroot}%{_libdir}/%{name}/plugins/nsca_client.py

chmod +x %{buildroot}%{python_sitelib}/%{name}/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/daemons/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/dummy_poller.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/objects/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/livestatus_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/status_dat_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/service_perfdata_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/merlindb_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/host_perfdata_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/couchdb_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/ndodb_oracle_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/ndodb_mysql_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/login/login.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/webui_broker/*.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/action/action.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/bottle.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/clients/livestatus.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/thrift_broker/thrift_command_query.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/eltdetail/eltdetail.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/threedimpacts/threedimpacts.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/thrift_broker/thrift_query.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/livestatus_broker/mapping.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/thrift_broker/thrift_broker.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/depgraph/depgraph.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/thrift_broker/thrift_status.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/misc/regenerator.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/thrift_broker/thrift_response.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/problems/problems.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/thrift_broker/__init__.py


chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/glpidb_broker/__init__.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/modules/glpidb_broker/glpidb_broker.py
chmod +x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/dashboard/dashboard.py

chmod -x %{buildroot}%{python_sitelib}/%{name}/{property,daemon,basemodule}.py
chmod -x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/eltdetail/htdocs/js/domtab.js
chmod -x %{buildroot}%{python_sitelib}/%{name}/webui/bottle.py
chmod -x %{buildroot}%{python_sitelib}/%{name}/modules/livestatus_broker/mapping.py
chmod -x %{buildroot}%{python_sitelib}/%{name}/webui/plugins/system/htdocs/css/system.css

sed -i -e 's!/usr/local/shinken/libexec!%{_libdir}/nagios/plugins!' %{buildroot}%{_sysconfdir}/%{name}/resource.cfg
sed -i -e 's!/usr/lib/nagios/plugins!%{_libdir}/nagios/plugins!' %{buildroot}%{_sysconfdir}/%{name}/resource.cfg

sed -i -e 's!/usr/local/shinken/var/arbiterd.pid!/var/run/shinken/arbiterd.pid!' %{buildroot}%{_sysconfdir}/%{name}/nagios.cfg
sed -i -e 's!command_file=/usr/local/shinken/var/rw/nagios.cmd!command_file=/var/log/shinken/nagios.cmd!' %{buildroot}%{_sysconfdir}/%{name}/nagios.cfg
sed -i -e 's!cfg_file=hostgroups.cfg!!' %{buildroot}%{_sysconfdir}/%{name}/nagios.cfg

sed -i -e 's!,Windows_administrator!!' %{buildroot}%{_sysconfdir}/%{name}/contactgroups.cfg

sed -i -e 's!/usr/local/shinken/src/!/usr/sbin/!' FROM_NAGIOS_TO_SHINKEN
sed -i -e 's!/usr/local/nagios/etc/!/etc/shinken/!' FROM_NAGIOS_TO_SHINKEN
sed -i -e 's!/usr/local/shinken/src/etc/!/etc/shinken/!' FROM_NAGIOS_TO_SHINKEN
sed -i -e 's!(you can also be even more lazy and call the bin/launch_all.sh script).!!' FROM_NAGIOS_TO_SHINKEN

rm -rf %{buildroot}%{_localstatedir}/{log,run,lib}/%{name}/void_for_git
rm %{buildroot}/usr/lib/%{name}/plugins/check.sh
rm %{buildroot}%{_sysconfdir}/default/shinken
rm -rf %{buildroot}%{_sysconfdir}/init.d/shinken*
rm -rf %{buildroot}%{_libdir}/%{name}/plugins/*.{pyc,pyo}

rm -rf %{buildroot}%{_sbindir}/shinken-{arbiter,discovery,broker,poller,reactionner,receiver,scheduler}.py

chmod -Rf 0644  %{buildroot}%{python_sitelib}/%{name}/webui/plugins/impacts/impacts.py


%clean

%pre
echo Adding %{shinken_group} group ...
getent group %{shinken_group} >/dev/null || groupadd -r %{shinken_group}
echo Adding %{shinken_user} user ...
getent passwd %{shinken_user} >/dev/null || useradd -r -g %{shinken_group} -d %{_localstatedir}/spool/nagios -s /sbin/nologin %{shinken_user}
exit 0


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
    /bin/systemctl --no-reload disable %{name}-arbiter.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}-arbiter.service > /dev/null 2>&1 || :
fi

%preun broker
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}-broker.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}-broker.service > /dev/null 2>&1 || :
fi

%preun poller
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}-poller.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}-poller.service > /dev/null 2>&1 || :
fi

%preun reactionner
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}-reactionner.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}-reactionner.service > /dev/null 2>&1 || :
fi

%preun scheduler
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}-scheduler.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}-scheduler.service > /dev/null 2>&1 || :
fi

%preun receiver
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}-receiver.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}-receiver.service > /dev/null 2>&1 || :
fi

%postun arbiter
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}-arbiter.service >/dev/null 2>&1 || :
fi

%postun broker
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}-broker.service >/dev/null 2>&1 || :
fi

%postun poller
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}-poller.service >/dev/null 2>&1 || :
fi

%postun reactionner
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}-reactionner.service >/dev/null 2>&1 || :
fi

%postun scheduler
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}-scheduler.service >/dev/null 2>&1 || :
fi

%postun receiver
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}-receiver.service >/dev/null 2>&1 || :
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
%{python_sitelib}/%{name}
%{python_sitelib}/Shinken-0.8-py2.7.egg-info
%doc README.rst COPYING Changelog THANKS db doc FROM_NAGIOS_TO_SHINKEN
%{_libdir}/%{name}/plugins
%{_mandir}/man3/%{name}-discovery*
%{_mandir}/man3/%{name}-admin*
%{_sbindir}/%{name}-discovery
%{_sbindir}/%{name}-admin
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/log/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/lib/%{name}

%changelog
* Mon Oct 24 2011 David Hannequin <david.hannequin@gmail.com> - 0.8.1-1
- Update from upstream,

* Mon May 30 2011 David Hannequin <david.hannequin@gmail.com> - 0.6.5-1
- Update from upstream,
- Add require python-redis,
- Add require python-memcached.

* Mon May 30 2011 David Hannequin <david.hannequin@gmail.com> - 0.6.4-3
- Fix path in default shinken file,
- Fix path in setup.cfg,
- Add file FROM_NAGIOS_TO_SHINKEN.

* Sun May 29 2011 David Hannequin <david.hannequin@gmail.com> - 0.6.4-2
- Fix shinken configuration,
- Replace macro,
- Update from upstreamr.

* Fri May 20 2011 David Hannequin <david.hannequin@gmail.com> - 0.6.4-1
- Update from upstream.

* Sun Apr 29 2011 David Hannequin <david.hannequin@gmail.com> - 0.6-1
- Fisrt release for fedora.
