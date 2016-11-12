const int MAX_NESTING = 100;
const int MAX_TABLE_COLS = 100;

class SFR.RedditMarkdownShared {
    private Gtk.Box box;
    private string? bottom;

    public RedditMarkdownShared (Gtk.Box box) {
        this.box = box;
    }

    public void append_markup (string markup) {
        if (this.bottom == null) {
            //debug ("bottom is null\n");
            this.bottom = markup;
        } else {
            //debug ("adding to bottom");
            this.bottom += markup;
        }
    }

    public void flush_markup () {
        if (this.bottom == null) {
            //debug ("flush bottom is null");
            return;
        }

        var l = new Gtk.Label ("");
        l.set_markup (this.bottom);
        this.bottom = null;
        l.wrap = true;
        l.selectable = true;
        this.box.add(l);
    }

    public void append_widget (Gtk.Widget widget) {
        this.flush_markup ();
        this.box.add (widget);
    }
}

class SFR.RedditMarkdownWidget : Gtk.Box {

    private Gtk.Label bottom_label;

    public RedditMarkdownWidget (string inp_markdown) {
        Object (orientation: Gtk.Orientation.VERTICAL);

        string markdown = inp_markdown.substring (0, 2000);
        stdout.printf ("%s\n", markdown);

        var shared = new SFR.RedditMarkdownShared (this);

        var callbacks = Snudown.Callbacks ();
        callbacks.paragraph = paragraph;
        callbacks.entity = entity;
        callbacks.header = header;
        callbacks.listitem = listitem;
        callbacks.autolink = autolink;
        callbacks.link = link_cb;
        callbacks.emphasis = emphasis;
        callbacks.double_emphasis = double_emphasis;

        var md = new Snudown.Markdown<SFR.RedditMarkdownShared> (
            0,
            MAX_NESTING,
            MAX_TABLE_COLS,
            callbacks,
            shared
        );

        /* Why we use 128, who knows.  That's just what the python binding
           does, so that is what we will do. */
        var buffer = new Snudown.Buffer (128);
        md.render (buffer, (char[]) markdown.data);

        shared.flush_markup ();
        this.show_all ();
    }
}

void paragraph (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    sh.append_markup (text.str ());
}

void header (Snudown.Buffer ob, Snudown.Buffer text, int level, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var l = new Gtk.Label (text.str ());
    l.wrap = true;
    l.selectable = true;
    l.attributes = new Pango.AttrList ();
    l.attributes.insert (Pango.attr_scale_new (Pango.Scale.LARGE));
    l.attributes.insert (Pango.attr_weight_new (Pango.Weight.BOLD));
    sh.append_widget (l);
}

void listitem (Snudown.Buffer ob, Snudown.Buffer text, Snudown.ListFlags flags, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;

    var front = "* ";
    if ((bool) flags & Snudown.ListFlags.ORDERED) {
        front = "# ";
    }

    var l = new Gtk.Label ("");
    l.set_markup (front + text.str ());
    l.wrap = true;
    l.selectable = true;
    sh.append_widget (l);
}

void entity (Snudown.Buffer ob, Snudown.Buffer entity, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    debug ("ENTITY START '%s' END", entity.str ());
    /*sh.append_markup ((string) text.data);*/
}

/*
 * Inline elements (we convert them to pango markup and put it in the out buf)
 */
void autolink (Snudown.Buffer ob, Snudown.Buffer al, Snudown.AutolinkType type, GLib.Object user_data) {
    debug ("AL START '%s' END", al.str ());
    link_cb (ob, al, null, al, user_data);
}
void link_cb (Snudown.Buffer ob, Snudown.Buffer link, Snudown.Buffer? title, Snudown.Buffer content, GLib.Object user_data) {
    // FIXME: Escape link if needed
    ob.puts ("<a href='%s'>%s</a>".printf (link.str (), content.str ()));
}
void emphasis (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    ob.puts ("<i>%s</i>".printf (text.str ()));
}
void double_emphasis (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    ob.puts ("<b>%s</b>".printf (text.str ()));
}
