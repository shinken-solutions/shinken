%global with_python3 1

Name:           python-pyro
Version:        4.3
Release:        2%{?dist}
Summary:        PYthon Remote Objects

Group:          Development/Languages
License:        MIT
URL:            http://www.xs4all.nl/~irmen/pyro4/index.html
Source0:        http://www.xs4all.nl/~irmen/pyro4/download/Pyro4-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
%if 0%{?with_python3}
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: /usr/bin/2to3
%endif # if with_python3

%description
Pyro provides an object-oriented form of RPC. You can use Pyro within a
single system but also use it for IPC. For those that are familiar with
Java, Pyro resembles Java's Remote Method Invocation (RMI). It is less
similar to CORBA - which is a system- and language independent Distributed
Object Technology and has much more to offer than Pyro or RMI.

%if 0%{?with_python3}
%package -n python3-pyro
Summary:        Python Remote Objects
Group:          Development/Languages
%description -n python3-pyro
Pyro provides an object-oriented form of RPC. You can use Pyro within a
single system but also use it for IPC. For those that are familiar with
Java, Pyro resembles Java's Remote Method Invocation (RMI). It is less
similar to CORBA - which is a system- and language independent Distributed
Object Technology and has much more to offer than Pyro or RMI.
%endif # with_python3

%prep
%setup -q -n Pyro4-%{version}
%if 0%{?with_python3}
rm -rf %{py3dir}
cp -a . %{py3dir}
%endif # with_python3

%build
%{__python} setup.py build
%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py build
popd
%endif # with_python3

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
find examples -type f -exec sed -i 's/\r//' {} \;
sed -i 's/\r//' README.txt LICENSE

%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
find examples -type f -exec sed -i 's/\r//' {} \;
sed -i 's/\r//' README.txt LICENSE
popd
%endif # with_python3

%files
%defattr(-,root,root,-)
%doc docs/* examples README.txt LICENSE
%{python_sitelib}/Pyro4
%{python_sitelib}/Pyro4-*.egg-info

%if 0%{?with_python3}
%files -n python3-pyro
%defattr(-,root,root,-)
%doc docs/* examples README.txt LICENSE
%{python3_sitelib}/Pyro4
%{python3_sitelib}/Pyro4-*.egg-info
%endif

%changelog
* Wed Mar 13 2011 David Hannequin <david.hannequin@gmail.com> 4.3-2
- Python 3 support (thanks Haïkel Guémar)

* Sat Mar 9 2011 David Hannequin <david.hannequin@gmail.com> 4.3-1
- Update from upstream

* Sun Jan 16 2011 David Hannequin <david.hannequin@gmail.com> 4.2-1
- Update from upstream

* Tue Oct 12 2010 David Hannequin <david.hannequin@gmail.com> 4.0-3
- package for Fedora 13

* Mon Oct 11 2010 David Hannequin <david.hannequin@gmail.com> 4.0-2
- Delete clean section
- Add license file

* Tue Aug 03 2010 David Hannequin <david.hannequin@gmail.com> 4.0-1
- First release to Fedora
