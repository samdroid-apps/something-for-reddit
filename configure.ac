AC_PREREQ(2.63)
# VERSION:
AC_INIT([something-for-reddit],
        [0.2.2],
        [https://github.com/samdroid-apps/something-for-reddit/issues],
        [something-for-reddit],
        [https://github.com/samdroid-apps/something-for-reddit])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_SRCDIR([Makefile.am])
AC_CONFIG_HEADERS(config.h)
AM_INIT_AUTOMAKE([1.11 tar-ustar dist-xz no-dist-gzip -Wno-portability subdir-objects])
AM_MAINTAINER_MODE([enable])
m4_ifdef([AM_SILENT_RULES],[AM_SILENT_RULES([yes])])

AM_PATH_PYTHON([3.3])

AC_PROG_CC
AM_PROG_CC_C_O
# LT_INIT([disable-static])

PKG_PROG_PKG_CONFIG([0.22])

GETTEXT_PACKAGE=reddit-is-gtk
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE",
                   [The prefix for our gettext translation domains.])
IT_PROG_INTLTOOL(0.26)

# I don't know how to get this working on Nix
# TODO: uncomment the following once build works
# AX_PYTHON_MODULE([arrow], [For date humanization])
# AX_PYTHON_MODULE([markdown], [For reddit markdown])

GLIB_GSETTINGS
# TODO: get this working on Nix
# GOBJECT_INTROSPECTION_REQUIRE([1.35.9])
PKG_CHECK_MODULES([GTK], [gtk+-3.0 >= 3.13.2])
PKG_CHECK_MODULES([LIBSOUP], [libsoup-2.4 >= 2.4])
# TODO: get this working on Nix
# AX_PATH_PROG([sass], [For compiling style sheets])

GLIB_COMPILE_RESOURCES=`$PKG_CONFIG --variable glib_compile_resources gio-2.0`
AC_SUBST(GLIB_COMPILE_RESOURCES)

AC_CONFIG_FILES([
  Makefile
  data/Makefile
  redditisgtk/Makefile
  po/Makefile.in
])
AC_OUTPUT
