AC_PREREQ(2.63)
AC_INIT([something-for-reddit],
        [0.2],
        [https://github.com/samdroid-apps/something-for-reddit/issues],
        [something-for-reddit],
        [https://github.com/samdroid-apps/something-for-reddit])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_SRCDIR([Makefile.am])
AC_CONFIG_HEADERS(config.h)
AM_INIT_AUTOMAKE([1.11 foreign subdir-objects tar-ustar no-dist-gzip dist-xz -Wno-portability])
AM_MAINTAINER_MODE([enable])
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])

PKG_PROG_PKG_CONFIG([0.22])

GETTEXT_PACKAGE=reddit-is-gtk
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE",
                   [The prefix for our gettext translation domains.])
IT_PROG_INTLTOOL(0.26)

dnl ***********************************************************************
dnl GLib resource compilation
dnl ***********************************************************************
GLIB_GSETTINGS
GLIB_COMPILE_RESOURCES=`$PKG_CONFIG --variable glib_compile_resources gio-2.0`
AC_SUBST(GLIB_COMPILE_RESOURCES)


dnl ***********************************************************************
dnl Check for required programs
dnl ***********************************************************************
AC_PROG_CC
AC_PROG_INSTALL
AC_PROG_SED
AC_PATH_PROG([GLIB_GENMARSHAL],[glib-genmarshal])
AC_PATH_PROG([GLIB_MKENUMS],[glib-mkenums])
AC_PATH_PROG([GLIB_COMPILE_RESOURCES],[glib-compile-resources])
PKG_PROG_PKG_CONFIG([0.22])
GLIB_GSETTINGS
GOBJECT_INTROSPECTION_CHECK([1.42.0])

AM_PROG_VALAC([0.32])

AX_COMPILER_FLAGS


dnl ***********************************************************************
dnl Ensure C11 is Supported
dnl ***********************************************************************
AX_CHECK_COMPILE_FLAG([-std=gnu11],
                      [CFLAGS="$CFLAGS -std=gnu11"],
                      [AC_MSG_ERROR([C compiler cannot compile GNU C11 code])])



dnl ***********************************************************************
dnl Check for required packages
dnl ***********************************************************************
PKG_CHECK_MODULES(SOMETHING_FOR_REDDIT, [gio-2.0 >= 2.42
                                         libsoup-2.4 >= 2.4
                                         webkit2gtk-4.0 >= 2.0
                                         json-glib-1.0 >= 1.0
                                         gtk+-3.0 >= 3.20])


dnl ***********************************************************************
dnl Initialize Libtool
dnl ***********************************************************************
LT_PREREQ([2.2])
LT_INIT


AC_CONFIG_FILES([
  Makefile
  data/Makefile
  src/Makefile
  po/Makefile.in
])
AC_OUTPUT
