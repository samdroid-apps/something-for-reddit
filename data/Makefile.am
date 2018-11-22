style.dark.css.out: style.css
	$(AM_V_GEN) echo '$$dark: true;' | cat - style.css | sassc -s style.dark.css.out

style.css.out: style.css
	$(AM_V_GEN) echo '$$dark: false;' | cat - style.css | sassc -s style.css.out

resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --sourcedir=$(builddir) --generate-dependencies $(builddir)/reddit-is-gtk.gresource.xml)
reddit-is-gtk.gresource: reddit-is-gtk.gresource.xml style.css.out style.dark.css.out $(resource_files)
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

hicolor_app_iconsdir = $(datadir)/icons/hicolor/scalable/apps
hicolor_app_icons_DATA = icons/today.sam.reddit-is-gtk.svg
hicolor_app_icons_symbolicdir = $(datadir)/icons/hicolor/symbolic/apps
hicolor_app_icons_symbolic_DATA = icons/today.sam.reddit-is-gtk-symbolic.svg
hicolor_icons_symbolicdir = $(datadir)/icons/hicolor/scalable/actions
hicolor_icons_symbolic_DATA = \
	icons/reddit-mail-reply-all-symbolic.svg \
	icons/reddit-mail-reply-sender-symbolic.svg \
	icons/reddit-detach-symbolic.svg \
	icons/reddit-upvote-symbolic.svg \
	icons/reddit-novote-symbolic.svg \
	icons/reddit-downvote-symbolic.svg
hicolor_icon_files = \
	$(hicolor_app_icons_DATA) \
	$(hicolor_app_icons_symbolic_DATA) \
	$(hicolor_icons_symbolic_DATA)

gsettings_SCHEMAS = today.sam.something-for-reddit.gschema.xml


install-data-hook: update-icon-cache
uninstall-hook: update-icon-cache
update-icon-cache:
	@-if test -z "$(DESTDIR)"; then \
		echo "Updating Gtk hicolor icon cache."; \
		$(gtk_update_hicolor_icon_cache); \
	else \
		echo "*** Icon cache not updated.  After (un)install, run this:"; \
		echo "***   $(gtk_update_hicolor_icon_cache)"; \
	fi


# For uninstalled use
gschemas.compiled: $(gsettings_SCHEMAS) Makefile
	$(AM_V_GEN) $(GLIB_COMPILE_SCHEMAS) $(builddir)

@GSETTINGS_RULES@

EXTRA_DIST = \
	$(resource_files) \
	$(hicolor_icon_files) \
	reddit-is-gtk.desktop.in \
	reddit-is-gtk.appdata.xml.in \
	reddit-is-gtk.gresource.xml \
	today.sam.something-for-reddit.gschema.xml \
	style.css \
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
