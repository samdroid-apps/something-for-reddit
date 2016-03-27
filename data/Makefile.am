style.css.out: style.css
	$(AM_V_GEN) scss style.css style.css.out

resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --sourcedir=$(builddir) --generate-dependencies $(builddir)/reddit-is-gtk.gresource.xml)
reddit-is-gtk.gresource: reddit-is-gtk.gresource.xml style.css.out $(resource_files)
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir) --sourcedir=$(builddir) $<

resourcedir = $(pkgdatadir)
resource_DATA = reddit-is-gtk.gresource

appsdir = $(datadir)/applications
apps_DATA = reddit-is-gtk.desktop

@INTLTOOL_DESKTOP_RULE@

appdatadir = $(datadir)/appdata
appdata_DATA = $(appdata_in_files:.xml.in=.xml)
appdata_in_files = reddit-is-gtk.appdata.xml.in

@INTLTOOL_XML_RULE@

please_draw_new_iconsdir = $(datadir)/pixmaps
please_draw_new_icons_DATA = reddit-is-a-dead-bird.svg reddit-is-a-dead-bird-symbolic.svg


EXTRA_DIST = \
	$(resource_files) \
	$(please_draw_new_icons_DATA) \
	reddit-is-gtk.desktop.in \
	reddit-is-gtk.appdata.xml.in \
	reddit-is-gtk.gresource.xml \
	$(NULL)

CLEANFILES = \
	reddit-is-gtk.gresource \
	reddit-is-gtk.appdata.xml \
	$(apps_DATA) \
	*.valid \
	gschemas.compiled \
	style.css.out \
	style.css.out.map \
	$(NULL)
