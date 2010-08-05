# release number:
%define rel %(date '+%Y%m%d%H%M')

%define pylibdir %{_libdir}/python2.6

%global __python /usr/bin/python26

Name:           python26-pyro
URL:            http://pyro.sourceforge.net/
Summary:        PYthon Remote Objects
Version:        3.10
Release:		%{rel}
License:        MIT
Group:          Development/Python
Source:         http://downloads.sourceforge.net/pyro/Pyro-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch:	noarch
#%py_requires -d

%description
Pyro provides an object-oriented form of RPC. You can use Pyro within a
single system but also use it for IPC. For those that are familiar with
Java, Pyro resembles Java's Remote Method Invocation (RMI). It is less
similar to CORBA - which is a system- and language independent Distributed
Object Technology and has much more to offer than Pyro or RMI.

%prep
%setup -q -n Pyro-%{version}

%build
%{__python} setup.py build

%install
[ -d %{buildroot} -a "%{buildroot}" != "" ] && rm -rf %{buildroot}
echo n | %{__python} setup.py install --root=%{buildroot}

mkdir -p %{buildroot}%_bindir
install -m 0755 bin/* %{buildroot}%_bindir

%clean
[ -d %{buildroot} -a "%{buildroot}" != "" ] && rm -rf  %{buildroot}

%files
%defattr(-,root,root)
%doc docs/* README.txt
%{_bindir}/*
%{pylibdir}/*


%changelog
* Tue Aug 03 2010 Stéphane Urbanovski <s.urbanovski@ac-nancy-metz.fr>
- update to 3.10 for RHEL5
- force python 2.6 usage
* Mon Jan 12 2009 Funda Wang <fundawang@mandriva.org> 3.8.1-1mdv2009.1
+ Revision: 328584
- import python-pyro


