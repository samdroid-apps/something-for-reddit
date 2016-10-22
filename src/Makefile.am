appdir = $(pythondir)/redditisgtk

bin_PROGRAMS = something-for-reddit

reddit-is-gtk.gresource.c: ../data/reddit-is-gtk.gresource.xml ../data/style.css.out ../data/style.dark.css.out ../data/reddit-is-gtk.gresource
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir)/../data --sourcedir=$(builddir) --generate-source $<

something_for_reddit_SOURCES = something-for-reddit.vala reddit-is-gtk.gresource.c
something_for_reddit_CPPFLAGS = $(SOMETHING_FOR_REDDIT_CFLAGS)
something_for_reddit_VALAFLAGS = --pkg gtk+-3.0 --target-glib=2.38 --gresources ../data/reddit-is-gtk.gresource.xml --pkg libsoup-2.4 --pkg webkit2gtk-4.0 --pkg json-glib-1.0

something_for_reddit_LDADD = $(SOMETHING_FOR_REDDIT_LIBS)
