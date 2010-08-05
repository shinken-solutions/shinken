# release number:
%define rel %(date '+%Y%m%d%H%M')

Summary:		Nagios(R) compatible monitoring tool
Name:			shinken
Version:		0.2
Release:		%{rel}
Source0:		http://ftp.monitoring-fr.org/JEAN/shinken-%{version}.tgz
Source1:		%{name}-configs.tar.bz2
License:		AGPL
Group:			Applications/System
URL:			http://www.shinken-monitoring.org/
Requires:		python26, python26-pyro < 4.0, chkconfig
BuildRequires:	python26
BuildRoot:		%{_tmppath}/%{name}-%{version}-buildroot
BuildArch:		noarch


# Shinken process user and group
%define shinken_user shinken
%define shinken_group shinken

# Default SysV service
%define sysv_service shinken-all

# Shinken require python 2.6
%global __python /usr/bin/python26

%define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")



%description
Shinken is a new, Nagios(R) compatible monitoring tool, written in Python. The main goal of Shinken is to allow users to have a fully flexible architecture for their monitoring system that can easily scale to large environments.

Shinken is backwards-compatible with the Nagios(R) configuration standard and plugins.
Shinken also provide interfaces with NDODB and Merlin database, Livestatus connector
Shinken does not include any human interfaces.

Nagios is a registered trademark owned by Nagios Enterprises.

%description -l fr
Shinken est un nouvel outil de supervision compatible avec Nagios(R) et écrit en Python. L'objectif de Shinken de vous permettre de construire une architecture de supervision flexible et capable de s'adapter de large environnements.

Shinken est compatible avec les fichiers de configuration de Nagios(R) ainsi que les plugins.
Shinken fournit les connecteurs pour les bases NDODB et Merlin, ainsi qu'une interface Livestatus.
Shinken ne fourni pas d'interfaces graphiques.

Nagios est une marque déposée de Nagios Enterprises.

%prep

#%setup -n %{name}-%{version}
%setup -q -n %{name}


%setup -q -n %{name}
%{__tar} xjf %{SOURCE1}

%build

# Force python 2.6 
%{__sed} -i 's/\/env python$/\/env python26/' bin/*.py

# build .pyc files
%{__python} -m compileall bin shinken

%install
[ -d %{buildroot} -a "%{buildroot}" != "" ] && %{__rm} -rf %{buildroot}

# Exec
%{__install} -d -m0755 %{buildroot}%{_sbindir}
%{__install} -p -m0755 bin/shinken-*.py{,c} %{buildroot}%{_sbindir}

# libs
%{__install} -d -m0755 %{buildroot}%{python_sitelib}/shinken
%{__install} -p -m0644 shinken/*.py{,c} %{buildroot}%{python_sitelib}/shinken


# configs files
%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/%{name}/
%{__install} -p -m0755 configs/*.ini %{buildroot}%{_sysconfdir}/%{name}/
%{__install} -p -m0644 etc/shinken-specific.cfg %{buildroot}%{_sysconfdir}/%{name}/

# SysV init
%{__install} -d -m0755 %{buildroot}%{_initrddir}
%{__install} -p -m0755 bin/init.d/shinken-* %{buildroot}%{_initrddir}/

# Log dir
%{__install} -d -m0775 %{buildroot}%{_localstatedir}/log/%{name}/

# pid files
%{__install} -d -m0775 %{buildroot}%{_localstatedir}/run/%{name}/

# workdir
%{__install} -d -m0775 %{buildroot}%{_localstatedir}/lib/%{name}/


%clean
[ -d %{buildroot} -a "%{buildroot}" != "" ] && %{__rm} -rf %{buildroot}


#====[ pre installation scripts:
%pre
# Add user/group:
echo Adding %{shinken_user} user ...
/usr/sbin/useradd -M -o -r -d %{_localstatedir}/log/%{name} -s /sbin/nologin -c "Shinken user" %{shinken_user} > /dev/null 2>&1 || :


#====[ post installation scripts:
%post
# Add initscript to system V start :
/sbin/chkconfig --add %{sysv_service}
/sbin/chkconfig %{sysv_service} on


#====[ pre uninstall scripts 
%preun
if [ $1 -eq 0 ]; then
	# Stop and remove initscript :
	/sbin/service %{sysv_service} stop &>/dev/null || :
	/sbin/chkconfig --del %{sysv_service}
fi

%postun

%files
%defattr(-,root,root)
%doc README COPYING Changelog FROM_NAGIOS_TO_SHINKEN THANKS db doc

%{_initrddir}/shinken-*
%{_sbindir}/shinken-*
%{python_sitelib}/shinken

%config(noreplace) %{_sysconfdir}/%{name}/*.ini
%config(noreplace) %{_sysconfdir}/%{name}/*.cfg


%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/log/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/lib/%{name}
%attr(-,%{shinken_user} ,%{shinken_group}) %dir %{_localstatedir}/run/%{name}

%changelog
* Thu Aug  5 2010 Stéphane Urbanovski <s.urbanovski@ac-nancy-metz.fr> - 0.2
- Initial package