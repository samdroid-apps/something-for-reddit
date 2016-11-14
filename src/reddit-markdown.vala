const int MAX_NESTING = 100;
const int MAX_TABLE_COLS = 100;

class SFR.RedditMarkdownShared {
    private List<Gtk.Container> insert;

    public RedditMarkdownShared (Gtk.Box box) {
        this.insert = new List<Gtk.Container> ();
        this.insert.append (box);
    }

    /* Makes a new label and adds it to the insertion place (usually the
     * bottom of the box, unless we are in a table).  Returns the label for
     * the caller to set the text, styling, etc.
     */
    public Gtk.Label append_label (string class_name) {
        var l = new Gtk.Label ("");
        l.get_style_context ().add_class (class_name);
        l.wrap = true;
        l.selectable = true;
        l.halign = Gtk.Align.START;
        l.xalign = 0;

        this.append_widget (l);
        return l;
    }

    public void append_widget (Gtk.Widget widget) {
        this.insert.last ().data.add (widget);
    }

    public void push_container (Gtk.Container container) {
        this.append_widget (container);
        this.insert.append (container);
    }

    public void pop_container () {
        this.insert.delete_link (this.insert.last ());
    }
}

class SFR.RedditMarkdownWidget : Gtk.Box {

    private Gtk.Label bottom_label;

    public RedditMarkdownWidget (string markdown) {
        Object (orientation: Gtk.Orientation.VERTICAL);
        this.get_style_context ().add_class ("mkd-box");

        stdout.printf ("%s\n", markdown);

        var shared = new SFR.RedditMarkdownShared (this);

        var callbacks = Snudown.Callbacks ();
        callbacks.paragraph = paragraph;
        callbacks.blockcode = blockcode;
        callbacks.entity = entity;
        callbacks.header = header;
        callbacks.list = list;
        callbacks.listitem = listitem;
        callbacks.blockquote = blockquote;
        callbacks.enter_blockquote = enter_blockquote;
        callbacks.autolink = autolink;
        callbacks.link = link_cb;  // Link is a special name in Vala
        callbacks.emphasis = emphasis;
        callbacks.double_emphasis = double_emphasis;
        callbacks.triple_emphasis = triple_emphasis;

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

        this.show_all ();
    }
}

void paragraph (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var l = sh.append_label ("mkd-paragraph");
    l.set_markup (text.str ().chomp ());
}
void blockcode (Snudown.Buffer ob, Snudown.Buffer text, Snudown.Buffer? lang, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var l = sh.append_label ("mkd-blockcode");
    l.label = text.str ().chomp ();
}

void enter_blockquote (Snudown.Buffer ob, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var c = new Gtk.Box (Gtk.Orientation.VERTICAL, 0);
    c.get_style_context ().add_class ("mkd-box");
    c.get_style_context ().add_class ("mkd-blockquote");
    sh.push_container (c);
}
void blockquote (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    sh.pop_container ();
}

void header (Snudown.Buffer ob, Snudown.Buffer text, int level, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var l = sh.append_label ("mkd-header");
    /* You can't use inline formatting in a header */
    l.label = text.str ();
    l.attributes = new Pango.AttrList ();
    l.attributes.insert (Pango.attr_scale_new (Pango.Scale.LARGE));
    l.attributes.insert (Pango.attr_weight_new (Pango.Weight.BOLD));
}
void list (Snudown.Buffer ob, Snudown.Buffer text, Snudown.ListFlags flags, GLib.Object user_data) {
    /*debug ("Enter list: %i", flags);*/
}
void listitem (Snudown.Buffer ob, Snudown.Buffer text, Snudown.ListFlags flags, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;

    var front = "∙ ";
    if ((bool) flags & Snudown.ListFlags.ORDERED) {
        front = "# ";
    }

    var l = sh.append_label ("mkd-li");
    l.set_markup (front + text.str ().chomp ());
}

void entity (Snudown.Buffer ob, Snudown.Buffer entity, GLib.Object user_data) {
    debug ("ENTITY START '%s' END", entity.str ());
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
void triple_emphasis (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    ob.puts ("<i><b>%s</b></i>".printf (text.str ()));
}
