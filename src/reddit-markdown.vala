const int MAX_NESTING = 100;
const int MAX_TABLE_COLS = 100;
const Snudown.Extensions EXTENSIONS =
    Snudown.Extensions.NO_INTRA_EMPHASIS
    | Snudown.Extensions.TABLES
    | Snudown.Extensions.AUTOLINK
    | Snudown.Extensions.STRIKETHROUGH
    | Snudown.Extensions.SUPERSCRIPT;

class SFR.RedditMarkdownShared {
    private List<Gtk.Container> insert;
    private List<int> list_numbering;

    public RedditMarkdownShared (Gtk.Box box) {
        this.insert = new List<Gtk.Container> ();
        this.insert.append (box);
    }

    /* Makes a new label and adds it to the insertion place.  Returns the
     * label for the caller to set the text, styling, etc.
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

    public void push_container (Gtk.Container container, bool wrap = false) {
        if (wrap) {
            var sw = new Gtk.ScrolledWindow (null, null);
            sw.vscrollbar_policy = Gtk.PolicyType.NEVER;
            sw.add (container);
            this.append_widget (sw);
        } else {
            this.append_widget (container);
        }
        this.insert.append (container);
    }

    public void pop_container () {
        this.insert.delete_link (this.insert.last ());
    }

    /* Gets the SFR.MarkdownTable that we are in.  If we are not inside a
     * table (added using push_container), this method will result in a
     * crash due to an assert
     */
    public SFR.MarkdownTable get_table () {
        Gtk.Container container = this.insert.last ().data;
        assert (container.get_type () == typeof (SFR.MarkdownTable));
        return (SFR.MarkdownTable) container;
    }

    public void push_list_numbering () {
        this.list_numbering.append (0);
    }
    public void pop_list_numbering () {
        this.list_numbering.delete_link (this.list_numbering.last ());
    }
    /* Returns an index starting from 1 */
    public int get_list_item_number () {
        unowned List<int> last = this.list_numbering.last ();
        last.data++;
        return last.data;
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
        callbacks.normal_text = normal_text;
        callbacks.paragraph = paragraph;
        callbacks.blockcode = blockcode;
        callbacks.entity = entity;
        callbacks.header = header;
        callbacks.list = list;
        callbacks.enter_list = enter_list;
        callbacks.listitem = listitem;
        callbacks.enter_listitem = enter_listitem;
        callbacks.blockquote = blockquote;
        callbacks.enter_blockquote = enter_blockquote;
        callbacks.hrule = hrule;
        callbacks.autolink = autolink;
        callbacks.link = link_cb;  // Link is a special name in Vala
        callbacks.emphasis = emphasis;
        callbacks.double_emphasis = double_emphasis;
        callbacks.triple_emphasis = triple_emphasis;
        callbacks.strikethrough = strikethrough;
        callbacks.superscript = superscript;
        callbacks.codespan = codespan;
        /* Table callbacks */
        callbacks.enter_table = enter_table;
        callbacks.table = table;
        callbacks.enter_table_row = enter_table_row;
        callbacks.table_cell = table_cell;
        callbacks.table_row = table_row;

        var md = new Snudown.Markdown<SFR.RedditMarkdownShared> (
            EXTENSIONS, MAX_NESTING, MAX_TABLE_COLS,
            callbacks, shared
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
    l.get_style_context ().add_class ("mkd-header-%i".printf (level));
}

void enter_list (Snudown.Buffer ob, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    sh.push_list_numbering ();
}
void list (Snudown.Buffer ob, Snudown.Buffer text, Snudown.ListFlags flags, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    sh.pop_list_numbering ();
}

void enter_listitem (Snudown.Buffer ob, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var c = new SFR.MarkdownListItemBox ();
    sh.push_container (c);
}
class SFR.MarkdownListItemBox : Gtk.Box {
    Gtk.Box subbox;

    public MarkdownListItemBox () {
        Object (orientation: Gtk.Orientation.VERTICAL);
        this.get_style_context ().add_class ("mkd-listitem");
    }

    public override void add (Gtk.Widget child) {
        /* Snudown inserts the sublist items before the list item content,
           which is not desirable for us.  Therefore we need to re-order the
           items as they come in */
        if (child.get_type () == typeof (SFR.MarkdownListItemBox)) {
            /* Also a list item */
            if (this.subbox == null) {
                this.subbox = new Gtk.Box (Gtk.Orientation.VERTICAL, 0);
                this.subbox.get_style_context ().add_class ("mkd-listitem-sub");
                this.pack_end (this.subbox);
            }
            this.subbox.add (child);
        } else {
            this.pack_start (child);
        }
    }
}
void listitem (Snudown.Buffer ob, Snudown.Buffer text, Snudown.ListFlags flags, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;

    var n = sh.get_list_item_number ();
    var front = "∙ ";
    if ((bool) flags & Snudown.ListFlags.ORDERED) {
        front = "%i∙ ".printf (n);
    }

    var l = sh.append_label ("mkd-li");
    l.set_markup (front + text.str ().chomp ());

    sh.pop_container ();
}

void hrule (Snudown.Buffer ob, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var w = new Gtk.Separator (Gtk.Orientation.HORIZONTAL);
    sh.append_widget (w);
}

/*
 * Inline elements (we convert them to pango markup and put it in the out buf)
 */
void entity (Snudown.Buffer ob, Snudown.Buffer entity, GLib.Object user_data) {
    ob.puts (entity.str ());
}
void autolink (Snudown.Buffer ob, Snudown.Buffer al, Snudown.AutolinkType type, GLib.Object user_data) {
    link_cb (ob, al, null, al, user_data);
}
void link_cb (Snudown.Buffer ob, Snudown.Buffer link, Snudown.Buffer? title, Snudown.Buffer content, GLib.Object user_data) {
    // FIXME: Escape link if needed
    ob.puts ("<a href='%s'>%s</a>".printf (link.str (), content.str ()));
}
void normal_text (Snudown.Buffer ob, Snudown.Buffer text_buf, GLib.Object user_data) {
    int i = 0;
    var text = text_buf.str ();
    while (i < text.length) {
        /* Skip the newline and trailing spaces */
        if (text[i] == '\n') {
            if (i - 2 > 0 && text[i-2] == ' ' && text[i-1] == ' ') {
                /* Double space to add a newline */
                ob.putc ('\n');
            } else if (i - 1 > 0 && text[i-1] != ' ') {
                /* Add a space if the previous character was not a space */
                ob.putc (' ');
            }

            i++;
            while (i < text.length && text[i] == ' ') {
                i++;
            }
        }

        if (i < text.length) {
            if (text[i] == '&')  ob.puts ("&amp;");
            else  ob.putc (text[i]);
            i++;
        }
    }
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
void strikethrough (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    ob.puts ("<s>%s</s>".printf (text.str ()));
}
void superscript (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    ob.puts ("<sup>%s</sup>".printf (text.str ()));
}
void codespan (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    ob.puts ("<tt>%s</tt>".printf (text.str ()));
}

/* Table support */
class SFR.MarkdownTable : Gtk.Grid {
    int row;
    int n_cols;
    int col;

    public MarkdownTable () {
        this.get_style_context ().add_class ("mkd-table");
        this.halign = Gtk.Align.START;

        this.row = -1;
        this.col = -1;
        this.n_cols = 0;
    }

    public void advance_row () {
        if (this.row >= 0)  this.fill_row ();
        this.row++;
        this.col = -1;
    }

    public void add_cell (Gtk.Widget cell) {
        this.col++;
        this.attach (cell, this.col, this.row, 1, 1);
        if (this.n_cols < this.col) this.n_cols = this.col;
    }

    public void fill_row () {
        while (this.col < this.n_cols) {
            this.col++;
            Snudown.TableFlags flags = 0;
            if (this.row == 0)  flags = Snudown.TableFlags.HEADER;
            this.attach (
                new SFR.MarkdownTableCell (flags),
                this.col, this.row, 1, 1
            );
        }
    }
}
void enter_table (Snudown.Buffer ob, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    var c = new SFR.MarkdownTable ();
    sh.push_container (c, true);
}
void table (Snudown.Buffer ob, Snudown.Buffer header, Snudown.Buffer body, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    sh.get_table ().fill_row ();
    sh.pop_container ();
}
void enter_table_row (Snudown.Buffer ob, Snudown.TableFlags flags, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;
    sh.get_table ().advance_row ();
}
void table_row (Snudown.Buffer ob, Snudown.Buffer text, GLib.Object user_data) {
    /* No op */
    return;
}
class SFR.MarkdownTableCell : Gtk.Box {
    /* I would use a Gtk.Bin, but that doesn't render a CSS node, hence we will
       use a box */
    public MarkdownTableCell (Snudown.TableFlags flags) {
        Object (orientation: Gtk.Orientation.VERTICAL);
        this.get_style_context ().add_class ("mkd-table-cell");
        if ((bool) (flags & Snudown.TableFlags.HEADER)) {
            this.get_style_context ().add_class ("mkd-table-cell-header");
        }
    }
}
void table_cell (Snudown.Buffer ob, Snudown.Buffer text, Snudown.TableFlags flags, GLib.Object user_data) {
    SFR.RedditMarkdownShared sh = (SFR.RedditMarkdownShared) user_data;

    var cell = new SFR.MarkdownTableCell (flags);
    var l = new Gtk.Label ("");
    l.wrap = true;
    l.selectable = true;
    l.set_markup (text.str ());
    cell.add (l);

    if ((bool) (flags & Snudown.TableFlags.ALIGN_L)) {
        l.halign = Gtk.Align.START;
        l.xalign = 0;
    } else if ((bool) (flags & Snudown.TableFlags.ALIGN_R)) {
        l.halign = Gtk.Align.END;
        l.xalign = 1;
    }

    sh.get_table ().add_cell (cell);
}
