ACLOCAL_AMFLAGS = -I m4
NULL =

bin_SCRIPTS = reddit-is-gtk

SUBDIRS = src data

EXTRA_DIST = \
	$(NULL)

CLEANFILES = \
	$(bin_SCRIPTS)
	$(NULL)

MAINTAINERCLEANFILES = \
	$(srcdir)/INSTALL \
	$(srcdir)/aclocal.m4 \
	$(srcdir)/autoscan.log \
	$(srcdir)/compile \
	$(srcdir)/config.guess \
	$(srcdir)/config.h.in \
	$(srcdir)/config.sub \
	$(srcdir)/configure.scan \
	$(srcdir)/depcomp \
	$(srcdir)/install-sh \
	$(srcdir)/ltmain.sh \
	$(srcdir)/missing \
	$(srcdir)/mkinstalldirs \
	$(NULL)

GITIGNOREFILES = \
	m4 \
	$(NULL)

reddit-is-gtk: reddit-is-gtk.in Makefile
	$(AM_V_GEN)sed						\
		-e s!\@srcdir\@!$(abs_top_srcdir)!	\
		-e s!\@prefix\@!$(prefix)!		\
		-e s!\@datadir\@!$(datadir)!		\
		-e s!\@pkgdatadir\@!$(pkgdatadir)!	\
		-e s!\@libexecdir\@!$(libexecdir)!	\
		-e s!\@libdir\@!$(libdir)!		\
		-e s!\@pkglibdir\@!$(pkglibdir)!	\
		-e s!\@localedir\@!$(localedir)!	\
		-e s!\@pythondir\@!$(pythondir)!	\
		-e s!\@pyexecdir\@!$(pyexecdir)!	\
		-e s!\@PACKAGE\@!$(PACKAGE)!		\
		-e s!\@VERSION\@!$(VERSION)!		\
		< $< > $@
	chmod a+x $@

all-local: reddit-is-gtk

-include $(top_srcdir)/git.mk

