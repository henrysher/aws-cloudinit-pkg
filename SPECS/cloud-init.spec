%define _buildid .20

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%bcond_with systemd
%bcond_with selinux
# The Amazon Linux AMI build of cloud-init does not log using syslog by default
# because we found that rate-limiting caused some loss of log data.
%bcond_with rsyslog # without

Name:           cloud-init
Version:        0.7.2
Release: 7%{?_buildid}%{?dist}
Summary:        Cloud instance init scripts

Group:          System Environment/Base
License:        GPLv3
URL:            http://launchpad.net/cloud-init
Source0:        https://launchpad.net/cloud-init/trunk/%{version}/+download/%{name}-%{version}.tar.gz
Source1:        cloud-init-amazon.cfg
Source2:        cloud-init-README.fedora

# Deal with Fedora/Ubuntu path differences
Patch0:         cloud-init-0.7.2-fedora.patch

# "puppet" service was renamed to "puppetagent" in F19 as it was ported to
# systemd
# https://bugzilla.redhat.com/show_bug.cgi?id=1008250
Patch1:         cloud-init-0.7.2-puppetagent.patch

# Send text to stdout instead of /dev/console, then tell systemd to send
# stdout to journal+console.  Code that sends directly to syslog remains
# unchanged.
# https://bugzilla.redhat.com/show_bug.cgi?id=977952
# https://bugs.launchpad.net/bugs/1228434
Patch2:         cloud-init-0.7.2-nodevconsole.patch

# Fix restorecon failure when SELinux is disabled
# https://bugzilla.redhat.com/show_bug.cgi?id=967002
# https://bugs.launchpad.net/bugs/1228441
Patch3:         cloud-init-0.7.2-selinux-enabled.patch

# Fix rsyslog log filtering
# https://code.launchpad.net/~gholms/cloud-init/rsyslog-programname/+merge/186906
Patch4:         cloud-init-0.7.2-rsyslog-programname.patch

Source10:       defaults-amazon.cfg

Patch10001:     0001-Add-an-Amazon-distro-module.patch
Patch10002:     0002-Correct-usage-of-os.uname.patch
Patch10003:     0003-Decode-userdata-if-it-is-base64-encoded.patch
Patch10004:     0004-Add-pipe_cat-and-close_stdin-options-for-subp.patch
Patch10005:     0005-repo_upgrade-handling-security-levels.patch
Patch10006:     0006-Add-amazon-to-redhat-OS-family.patch
Patch10007:     0007-Amazon-Linux-AMI-doesn-t-use-systemd.patch
Patch10008:     0008-Add-a-genrepo-module-to-populate-yum.repos.d.patch
Patch10009:     0009-Use-a-shell-for-user-supplied-scripts.patch
Patch10010:     0010-Make-the-power-state-change-module-more-forgiving.patch
Patch10011:     0011-Add-repo_additions-compatibility.patch
Patch10012:     0012-Use-instance-identity-doc-for-region-and-instance-id.patch
Patch10013:     0013-Expand-the-migrator-module-to-handle-more-legacy.patch
Patch10014:     0014-Improve-service-handling.patch
Patch10015:     0015-Don-t-use-cheetah-for-formatting-log-entries.patch
Patch10016:     0016-Have-rsyslog-filter-on-syslogtag-startswith-CLOUDINI.patch
Patch10017:     0017-Suppress-backports-UserWarning-in-url_helper.patch
Patch10018:     0018-Catch-UrlError-when-includeing-URLs.patch
Patch10019:     0019-Prefer-file-to-syslog-and-improve-format.patch
Patch10020:     0020-Determine-services-domain-dynamically.patch
Patch10021:     0021-Remove-prettytable-dependency.patch
Patch10022:     0022-Use-legacy-sudoers-file.patch

BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
%if %{with systemd}
BuildRequires:  systemd-units
%endif
Requires:       e2fsprogs
Requires:       iproute
%if %{with selinux}
Requires:       libselinux-python
%endif
Requires:       net-tools
Requires:       procps
Requires:       python-argparse
Requires:       python-boto
Requires:       python-cheetah
Requires:       python-configobj
Requires:       python-requests
Requires:       PyYAML
%if %{with rsyslog}
Requires:       rsyslog
%endif
Requires:       shadow-utils
%if %{with systemd}
Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units
%else
Requires(post):   chkconfig
Requires(preun):  chkconfig
Requires(postun): initscripts
# For triggerun hacks for 0.5
Requires(postun): upstart
Requires(postun): /sbin/initctl
Requires(postun): /sbin/service
%endif
Requires(post): mktemp

Provides:       cloud-init(genrepo)

%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.


%prep
%setup -q -n %{name}-%{version}
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

# Amazon patches
%patch10001 -p1
%patch10002 -p1
%patch10003 -p1
%patch10004 -p1
%patch10005 -p1
%patch10006 -p1
%patch10007 -p1
%patch10008 -p1
%patch10009 -p1
%patch10010 -p1
%patch10011 -p1
%patch10012 -p1
%patch10013 -p1
%patch10014 -p1
%patch10015 -p1
%patch10016 -p1
%patch10017 -p1
%patch10018 -p1
%patch10019 -p1
%patch10020 -p1
%patch10021 -p1
%patch10022 -p1

cp -p %{SOURCE2} README.fedora


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Remove other cloud sources
for source in \
    $(ls $RPM_BUILD_ROOT%{python_sitelib}/cloudinit/sources/DataSource* \
      | grep -iv 'DataSourceEc2\|DataSourceNone')
do
    rm -f $source
done
# The rightscale user-data source is incorrectly implemented as a module...
rm -f $RPM_BUILD_ROOT%{python_sitelib}/cloudinit/config/cc_rightscale*

# Don't ship the tests
rm -r $RPM_BUILD_ROOT%{python_sitelib}/tests

mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/cloud

# We supply our own config file since our software differs from Ubuntu's.
cp -p %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg
cp -p %{SOURCE10} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg.d/defaults.cfg

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf

%if %{with systemd}
# Install the systemd bits
mkdir -p        $RPM_BUILD_ROOT/%{_unitdir}
cp -p systemd/* $RPM_BUILD_ROOT/%{_unitdir}
%else
# Install the init scripts
mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
install -p -m 755 sysvinit/* $RPM_BUILD_ROOT/%{_initrddir}/
%endif

# Add sudo entry for ec2-user in /etc/sudoers.d
# cloud-init will do this itself, but if we don't keep this file, an upgrade
# from 0.5 would remove sudo permissions from the ec2-user
install -m 750 -d $RPM_BUILD_ROOT%{_sysconfdir}/sudoers.d
echo "ec2-user ALL = NOPASSWD: ALL" > %{buildroot}%{_sysconfdir}/sudoers.d/cloud-init

# Create a compatibility wrapper for cloud-init-cfg
cat <<'EOF' > $RPM_BUILD_ROOT/%{_bindir}/cloud-init-cfg
#!/bin/sh
%{_bindir}/cloud-init single --name "$@"
EOF
chmod +x $RPM_BUILD_ROOT/%{_bindir}/cloud-init-cfg

%clean
rm -rf $RPM_BUILD_ROOT


%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    # Enabled by default per "runs once then goes away" exception
%if %{with systemd}
    /bin/systemctl enable cloud-config.service     >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-final.service      >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init.service       >/dev/null 2>&1 || :
    /bin/systemctl enable cloud-init-local.service >/dev/null 2>&1 || :
%else
    for svc in init-local init config final; do
        chkconfig --add cloud-$svc
        chkconfig cloud-$svc on
    done
%endif
fi

%triggerun -- cloud-init < 0.7
# Older versions had different service script names and start priorities
for svc in init init-user-scripts; do
    chkconfig --del cloud-$svc
done

%triggerpostun -- cloud-init < 0.7
for svc in init-local init config final; do
    chkconfig --add cloud-$svc
    chkconfig cloud-$svc on
done
# If cloud-init has already run, we should try to migrate semaphores
if [ -f %{_sharedstatedir}/cloud/data/cache/obj.pkl ]
then
    tmpfile=$(mktemp)
    # Only run the migrator module, nothing else
    echo 'cloud_init_modules: [ migrator ]' > ${tmpfile}
    %{_bindir}/cloud-init --file ${tmpfile} init >/dev/null 2>&1 ||:
    rm -f ${tmpfile}
fi
%if %{without systemd}
# Only create this job if rc is running, so that we are likely to get a started
# event from cloud-init.
if /sbin/initctl status rc | grep start/running >/dev/null 2>&1
then
    UPGRADE_JOB="%{_sysconfdir}/init/cloud-init-upgraded.conf"
    cat <<EOF > "$UPGRADE_JOB"
start on started cloud-init
task
# This file should only exist just after an upgrade from cloud-init 0.5,
# and only if cloud-init was running at the time. We do this to ensure that
# cloud-init completes a run if it happens to upgrade itself.
script
    /sbin/service cloud-init-local start ||:
    /sbin/service cloud-init start ||:
    /sbin/service cloud-config start ||:
    /sbin/service cloud-final start ||:
end script
pre-start exec rm -f "$UPGRADE_JOB"
EOF
fi
%endif

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
%if %{with systemd}
    /bin/systemctl --no-reload disable cloud-config.service >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-final.service  >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init.service   >/dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cloud-init-local.service >/dev/null 2>&1 || :
%else
    for svc in init-local init config final; do
        chkconfig --del cloud-$svc
    done
    # One-shot services -> no need to stop
%endif
fi

%postun
%if %{with systemd}
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif
# One-shot services -> no need to restart


%files
%doc ChangeLog LICENSE TODO README.fedora
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg
%dir               %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%doc               %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir               %{_sysconfdir}/cloud/templates
%config(noreplace) %{_sysconfdir}/cloud/templates/*.tmpl
%if %{with systemd}
%{_unitdir}/cloud-config.service
%{_unitdir}/cloud-config.target
%{_unitdir}/cloud-final.service
%{_unitdir}/cloud-init-local.service
%{_unitdir}/cloud-init.service
%else
%{_initddir}/cloud-config
%{_initddir}/cloud-final
%{_initddir}/cloud-init
%{_initddir}/cloud-init-local
%endif
%{python_sitelib}/*.egg-info
%dir %{python_sitelib}/cloudinit
%{python_sitelib}/cloudinit/*.py*
%dir %{python_sitelib}/cloudinit/config
%{python_sitelib}/cloudinit/config/*.py*
%dir %{python_sitelib}/cloudinit/distros
%{python_sitelib}/cloudinit/distros/*.py*
%dir %{python_sitelib}/cloudinit/distros/parsers
%{python_sitelib}/cloudinit/distros/parsers/*.py*
%dir %{python_sitelib}/cloudinit/filters
%{python_sitelib}/cloudinit/filters/*.py*
%dir %{python_sitelib}/cloudinit/handlers
%{python_sitelib}/cloudinit/handlers/*.py*
%dir %{python_sitelib}/cloudinit/mergers
%{python_sitelib}/cloudinit/mergers/*.py*
%dir %{python_sitelib}/cloudinit/sources
%{python_sitelib}/cloudinit/sources/__init__.py*
%{python_sitelib}/cloudinit/sources/DataSourceEc2.py*
%{python_sitelib}/cloudinit/sources/DataSourceNone.py*
%{_libexecdir}/%{name}
%{_bindir}/cloud-init*
%doc %{_datadir}/doc/%{name}
%dir %{_sharedstatedir}/cloud

%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf

%config %attr(0440,root,root) %{_sysconfdir}/sudoers.d/cloud-init

%changelog
* Mon Apr 7 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Exclude only kernel from upgrades, not kernel*

* Fri Apr 4 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Complete cloud-init run if cloud-init upgrades itself from 0.5
- don't Require rsyslog

* Wed Apr 2 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Use set-defaults to block remaining modules on upgrade, migrate user-scripts, and use legacy sudoers file

* Thu Mar 27 2014 Tom Kirchner <tjk@amazon.com>
- Default to preserving hostname

* Thu Mar 20 2014 Ethan Faust <efaust@amazon.com>
- Remove prettytable dependency

* Wed Mar 19 2014 Ethan Faust <efaust@amazon.com>
- Add fallback repo endpoint of amazonaws.com

* Mon Mar 17 2014 Ethan Faust <efaust@amazon.com>
- Determine services domain dynamically

* Wed Mar 12 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Complete improvements to migrator module
- Also migrate semaphores when upgrading from < 0.7

* Tue Mar 11 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Use file logging instead of syslog
- Use triggers to migrate to new sysv names

* Thu Mar 6 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Fail softer on exceptions fetching #include data
- Refresh Amazon patchset
- Various fixes for logging

* Wed Mar 5 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Disable selinux support for now, and remove Require on policycoreutils and dmidecode

* Thu Feb 27 2014 Andrew Jorgensen <ajorgens@amazon.com>
- Update Amazon patches

* Fri Feb 21 2014 Andrew Jorgensen <ajorgens@amazon.com>
- First pass at rebase onto 0.7.x

* Mon Feb 3 2014 Andrew Jorgensen <ajorgens@amazon.com>
- import source package F20/cloud-init-0.7.2-7.fc20

* Tue Sep 24 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-7
- Dropped xfsprogs dependency [RH:974329]

* Tue Sep 24 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-6
- Added yum-add-repo module

* Fri Sep 20 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-5
- Fixed puppet agent service name [RH:1008250]
- Let systemd handle console output [RH:977952 LP:1228434]
- Fixed restorecon failure when selinux is disabled [RH:967002 LP:1228441]
- Fixed rsyslog log filtering
- Added missing modules [RH:966888]

* Wed Sep 4 2013 Andrew Jorgensen <ajorgens@amazon.com>
- import source package F19/cloud-init-0.7.2-1.fc19

* Tue Aug 20 2013 Andrew Jorgensen <ajorgens@amazon.com>
- import source package RHEL6/cloud-init-0.7.1-2.el6
- setup complete for package cloud-init

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jun 15 2013 Matthew Miller <mattdm@fedoraproject.org> - 0.7.2-3
- switch ec2-user to "fedora" --  see bugzilla #971439. To use another
  name, use #cloud-config option "users:" in userdata in cloud metadata
  service
- add that user to systemd-journal group

* Fri May 17 2013 Steven Hardy <shardy@redhat.com> - 0.7.2
- Update to the 0.7.2 release

* Thu May 02 2013 Steven Hardy <shardy@redhat.com> - 0.7.2-0.1.bzr809
- Rebased against upstream rev 809, fixes several F18 related issues
- Added dependency on python-requests

* Sat Apr  6 2013 Orion Poplawski <orion@cora.nwra.com> - 0.7.1-4
- Don't ship tests

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Dec 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.1-2
- Added default_user to cloud.cfg (this is required for ssh keys to work)

* Wed Nov 21 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.1-1
- Rebased against version 0.7.1
- Fixed broken sudoers file generation
- Fixed "resize_root: noblock" [LP:1080985]

* Tue Oct  9 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-1
- Rebased against version 0.7.0
- Fixed / filesystem resizing

* Sat Sep 22 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.3.bzr659
- Added dmidecode dependency for DataSourceAltCloud

* Sat Sep 22 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.2.bzr659
- Rebased against upstream rev 659
- Fixed hostname persistence
- Fixed ssh key printing
- Fixed sudoers file permissions

* Mon Sep 17 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.1.bzr650
- Rebased against upstream rev 650
- Added support for useradd --selinux-user

* Thu Sep 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.5.bzr532
- Use a FQDN (instance-data.) for instance data URL fallback [RH:850916 LP:1040200]
- Shut off systemd timeouts [RH:836269]
- Send output to the console [RH:854654]

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.3-0.4.bzr532
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jun 27 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.3.bzr532
- Add support for installing yum packages

* Sat Mar 31 2012 Andy Grimm <agrimm@gmail.com> - 0.6.3-0.2.bzr532
- Fixed incorrect interpretation of relative path for
  AuthorizedKeysFile (BZ #735521)

* Mon Mar  5 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.1.bzr532
- Rebased against upstream rev 532
- Fixed runparts() incompatibility with Fedora

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.2-0.8.bzr457
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Oct  5 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.7.bzr457
- Disabled SSH key-deleting on startup

* Wed Sep 28 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.6.bzr457
- Consolidated selinux file context patches
- Fixed cloud-init.service dependencies
- Updated sshkeytypes patch
- Dealt with differences from Ubuntu's sshd

* Sat Sep 24 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.5.bzr457
- Rebased against upstream rev 457
- Added missing dependencies

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.4.bzr450
- Added more macros to the spec file

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.3.bzr450
- Fixed logfile permission checking
- Fixed SSH key generation
- Fixed a bad method call in FQDN-guessing [LP:857891]
- Updated localefile patch
- Disabled the grub_dpkg module
- Fixed failures due to empty script dirs [LP:857926]

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.2.bzr450
- Updated tzsysconfig patch

* Wed Sep 21 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.1.bzr450
- Initial packaging
