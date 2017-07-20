# Define SCL name
%{!?scl_name_prefix: %global scl_name_prefix sclo-}
%{!?scl_name_base: %global scl_name_base cassandra}
%{!?scl_pretty_name: %global scl_pretty_name Cassandra}
%{!?version_major: %global version_major 3}
%{!?version_minor: %global version_minor 5}
%{!?scl_name_version: %global scl_name_version %{version_major}%{version_minor}}
%{!?scl: %global scl %{scl_name_prefix}%{scl_name_base}%{scl_name_version}}

# Define SCL macros
%{?scl_package:%scl_package %{scl}}

%global cassandra_sitelib       %_scl_root%python_sitelib
%global cassandra_sitearch      %_scl_root%python_sitearch

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary:	Package that installs %{scl}
Name:		%{scl}
Version:	1.0
Release:	9%{?dist}
License:	GPLv2+
Group:		Applications/File
Source0:	README
Source1:	LICENSE
Source2:	configuration.xml
Requires:	scl-utils
# Requires: %%{scl_prefix}cassandra-server
BuildRequires:	scl-utils-build help2man
BuildRequires:	python-devel

%description
This is the main package for %{scl} Software Collection, which installs
necessary packages to use %{scl_pretty_name} %{version_major}.%{version_minor} server.
Software Collections allow to install more versions of the same
package by using alternative directory structure.
Install this package if you want to use %{scl_pretty_name} %{version_major}.%{version_minor}
server on your system.

%package runtime
Summary:	Package that handles %{scl} Software Collection.
Group:		Applications/File
Requires:	scl-utils
Requires(post): policycoreutils-python libselinux-utils

%description runtime
Package shipping essential scripts to work with %{scl} Software Collection.

%package build
Summary:	Package shipping basic build configuration
Group:		Applications/File
Requires:	%{name}-scldevel = %{version}-%{release}

# It is convenient to just configure Mock/Copr/Koji to install SCL_prefix-build
# package into minimal buildroot.
Requires:	scl-utils-build

%description build
Package shipping essential configuration macros to build %{scl} Software
Collection or packages depending on %{scl} Software Collection.

%package scldevel
Summary:	Package shipping development files for %{scl}
Requires:	rh-maven33-scldevel

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %{scl} Software Collection.

%prep
%setup -c -T

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat <<'EOF' | tee README
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .
# copy the configuration.xml file so %%files section sees it
cp %{SOURCE2} .

%build
# generate a helper script that will be used by help2man
cat <<'EOF' | tee h2m_helper
#!/bin/bash
[ "$1" == "--version" ] && echo "%{?scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper

# generate the man page
help2man -N --section 7 ./h2m_helper -o %{?scl_name}.7

# Generate java.conf
cat <<EOF >java.conf
JAVA_LIBDIR=/opt/rh/%{scl_name}/root/usr/share/java
JNI_LIBDIR=/opt/rh/%{scl_name}/root/usr/lib/java
JVM_ROOT=/opt/rh/%{scl_name}/root/usr/lib/jvm
EOF

%install
%{?scl_install}

# create and own dirs not covered by %%scl_install and %%scl_files
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 15
mkdir -p %{buildroot}%{_mandir}/man{1,7,8}
%else
mkdir -p %{buildroot}%{_datadir}/aclocal
%endif

# create enable scriptlet that sets correct environment for collection
cat << EOF | tee -a %{buildroot}%{?_scl_scripts}/enable
# For binaries
export PATH="%{_bindir}\${PATH:+:\${PATH}}"
# For header files
export CPATH="%{_includedir}\${CPATH:+:\${CPATH}}"
# For libraries during build
export LIBRARY_PATH="%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}"
# For libraries during linking
export LD_LIBRARY_PATH="%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}"
# For man pages; empty field makes man to consider also standard path
export MANPATH="%{_mandir}:\${MANPATH}"
# For Java Packages Tools to locate java.conf
export JAVACONFDIRS="%{_sysconfdir}/java:\${JAVACONFDIRS:-/etc/java}"
# For XMvn to locate its configuration file(s)
export XDG_CONFIG_DIRS="%{_sysconfdir}/xdg:\${XDG_CONFIG_DIRS:-/etc/xdg}"
# For systemtap
export XDG_DATA_DIRS="%{_datadir}\${XDG_DATA_DIRS:+:\${XDG_DATA_DIRS}}"
# For pkg-config
export PKG_CONFIG_PATH="%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}"
# For (possible) python modules
export PYTHONPATH="%cassandra_sitelib:%cassandra_sitearch\${PYTHONPATH:+:\${PYTHONPATH}}"
EOF

# generate rpm macros file for depended collections
cat << EOF | tee -a %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-scldevel
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{?scl_prefix}
EOF

cat <<'EOF' | tee -a %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config
# Python sitelib might be needed.
%%scl_package_override() %%{expand:
# Python related, I'm not sure that this will be actually needed.
%%%%global python_sitelib %cassandra_sitelib
%%%%global python2_sitelib %cassandra_sitelib
%%%%global python_sitearch %cassandra_sitearch
%%%%global python2_sitelib %cassandra_sitearch
}
EOF

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man7/
install -m 644 %{?scl_name}.7 %{buildroot}%{_mandir}/man7/%{?scl_name}.7

# install xmvn configuration
mkdir -p %{buildroot}%{_sysconfdir}/xdg/xmvn
install -m 644 configuration.xml %{buildroot}%{_sysconfdir}/xdg/xmvn/configuration.xml

# install java.conf
mkdir -p %{buildroot}%{_javaconfdir}
install -m 644 java.conf %{buildroot}%{_javaconfdir}/java.conf

%post runtime
# Simple copy of context from system root to SCL root.
# In case new version needs some additional rules or context definition,
# it needs to be solved in base system.
# semanage does not have -e option in RHEL-5, so we would
# have to have its own policy for collection.
semanage fcontext -a -e / %{?_scl_root} >/dev/null 2>&1 || :
semanage fcontext -a -e %{_root_sysconfdir} %{_sysconfdir} >/dev/null 2>&1 || :
semanage fcontext -a -e %{_root_localstatedir} %{_localstatedir} >/dev/null 2>&1 || :

selinuxenabled && load_policy || :
restorecon -R %{?_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_sysconfdir} >/dev/null 2>&1 || :
restorecon -R %{_localstatedir} >/dev/null 2>&1 || :

%files

%files runtime -f filesystem
%doc README LICENSE
%{?scl_files}
%{_javaconfdir}/java.conf

%files build
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl}-scldevel

%changelog
* Wed Nov 09 2016 Tomas Repik <trepik@redhat.com> - 1.0-9
- generate and install java.conf

* Wed Oct 26 2016 Tomas Repik <trepik@redhat.com> - 1.0-8
- use standard SCL macros
- add config file for xmvn

* Mon Oct 10 2016 Tomas Repik <trepik@redhat.com> - 1.0-7
- scldevel requires maven33 and java-common scldevel subpackages

* Wed Jul 27 2016 Pavel Raiskup <praiskup@redhat.com> - 1.0-6
- %%scl_java must be enabled befor %%scl_mvn

* Tue Jul 26 2016 Pavel Raiskup <praiskup@redhat.com> - 1.0-5
- add scl_java macro

* Tue Jul 26 2016 Pavel Raiskup <praiskup@redhat.com> - 1.0-4
- use scl_package_override for setting python macros
- explicitly depend on -scldevel subpackages

* Fri Jul 22 2016 Pavel Raiskup <praiskup@redhat.com> - 1.0-3
- move python_sitelib_cassandra to python_sitelib_scl

* Fri Jul 22 2016 Pavel Raiskup <praiskup@redhat.com> - 1.0-2
- try to hack python path (revert if this is not needed)

* Wed Jul 20 2016 Pavel Raiskup <praiskup@redhat.com> - 1.0-1
- initial packaging
