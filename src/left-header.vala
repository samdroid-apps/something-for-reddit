[GtkTemplate (ui="/today/sam/reddit-is-gtk/left-header.ui")]
class SFR.LeftHeader : Gtk.HeaderBar {
    private SFR.AppWindowModel model;

    [GtkChild]
    Gtk.Button refresh;
    [GtkChild]
    Gtk.Entry entry;

    public LeftHeader (SFR.AppWindowModel model) {
        this.model = model;

        this.model.bind_property (
            "left-uri", this.entry, "text",
            BindingFlags.DEFAULT | BindingFlags.SYNC_CREATE
        );
        this.model.bind_property (
            "left-loading", this.refresh, "sensitive",
            BindingFlags.DEFAULT | BindingFlags.SYNC_CREATE
                                 | BindingFlags.INVERT_BOOLEAN
        );
    }

    [GtkCallback]
    public void entry_activate_cb (Gtk.Entry entry) {
        debug ("SFR.LeftHeader.entry_activate_cb");
        this.model.load_left_uri (this.entry.text);
    }

    [GtkCallback]
    public void refresh_clicked_cb (Gtk.Button button) {
        this.entry.text = this.model.left_uri;
        this.model.load_left_uri (this.model.left_uri);
        // TODO
    }
}
