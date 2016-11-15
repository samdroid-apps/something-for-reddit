appdir = $(pythondir)/redditisgtk

bin_PROGRAMS = something-for-reddit something-for-reddit-markdown-tester

reddit-is-gtk.gresource.c: ../data/reddit-is-gtk.gresource.xml ../data/style.css.out ../data/style.dark.css.out
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir)/../data --sourcedir=$(builddir) --generate-source $<

shared_sources = \
    account.vala \
    application-model.vala \
    reddit-markdown.vala \
    sign-in-view.vala \
    app-view-manager.vala \
    left-header.vala \
    left-view.vala \
    listing.vala \
    meta-model.vala \
    reddit-is-gtk.gresource.c
something_for_reddit_SOURCES = \
    $(shared_sources) \
    something-for-reddit.vala
something_for_reddit_markdown_tester_SOURCES = \
    $(shared_sources) \
    something-for-reddit-markdown-tester.vala


something_for_reddit_CPPFLAGS = $(SOMETHING_FOR_REDDIT_CFLAGS)
something_for_reddit_VALAFLAGS = \
    --target-glib=2.38 \
    --gresources ../data/reddit-is-gtk.gresource.xml \
    --vapidir . \
    --pkg gtk+-3.0 \
    --pkg snudown \
    --pkg libsoup-2.4 \
    --pkg webkit2gtk-4.0 \
    --pkg json-glib-1.0 \
    --includedir snudown/src
something_for_reddit_markdown_tester_CPPFLAGS = $(something_for_reddit_CPPFLAGS)
something_for_reddit_markdown_tester_VALAFLAGS = $(something_for_reddit_VALAFLAGS)

snudown/build/lib.linux-x86_64-2.7/snudown.so: snudown/src/markdown.h snudown/src/markdown.c
	sh -c "cd snudown; python2.7 setup.py build"
snudown.so: snudown/build/lib.linux-x86_64-2.7/snudown.so
	cp snudown/build/lib.linux-x86_64-2.7/snudown.so snudown.so
install-exec-local: snudown.so
	install snudown.so $(libdir)/snudown.so

something_for_reddit_LDADD = $(SOMETHING_FOR_REDDIT_LIBS) snudown.so
something_for_reddit_markdown_tester_LDADD = $(something_for_reddit_LDADD)
