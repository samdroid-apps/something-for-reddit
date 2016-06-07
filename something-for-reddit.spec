%global gobject_introspection_version 1.35.9
%global gtk3_version 3.13.2
%global soup_version 2.4

Name:          something-for-reddit
Summary:       Waste time with a nice GUI
Version:       0.2
Release:       1%{?dist}
BuildArch:     noarch

License:       GPLv3+
URL:           http://wiki.gnome.org/Apps/Music
Source0:       https://download.gnome.org/sources/%{name}/3.20/%{name}-%{version}.tar.xz

BuildRequires: /usr/bin/appstream-util
BuildRequires: desktop-file-utils
BuildRequires: intltool
BuildRequires: itstool
BuildRequires: gnome-common
BuildRequires: pkgconfig(gio-2.0)
BuildRequires: pkgconfig(gobject-introspection-1.0) >= %{gobject_introspection_version}
BuildRequires: pkgconfig(gtk+-3.0) >= %{gtk3_version}
BuildRequires: pkgconfig(libsoup-2.4) >= %{soup_version}
# FIXME:  Build fails without python2 versions on COPR
BuildRequires: python-arrow
BuildRequires: python-markdown
BuildRequires: python3-devel
BuildRequires: python3-arrow
BuildRequires: python3-markdown
BuildRequires: ruby-gemssass

Requires:      libsoup
Requires:      gobject-introspection >= %{gobject_introspection_version}
Requires:      gtk3 >= %{gtk3_version}
Requires:      python3-gobject
Requires:      python3-arrow
Requires:      python3-markdown

%description
Reddit client with Gtk+


%prep
. gnome-autogen.sh


%build
make %{?_smp_mflags}


%install
%make_install


%check
appstream-util validate-relax --nonet %{buildroot}/%{_datadir}/appdata/reddit-is-gtk.appdata.xml
desktop-file-validate %{buildroot}/%{_datadir}/applications/reddit-is-gtk.desktop


%files
%doc NEWS
%license COPYING
%{_bindir}/%{name}
%{_datadir}/%{name}
%{_datadir}/pixmaps/
%{_datadir}/appdata/reddit-is-gtk.appdata.xml
%{_datadir}/applications/reddit-is-gtk.desktop
%{python3_sitelib}/redditisgtk
