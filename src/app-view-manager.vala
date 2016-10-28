/*
 * This is the model for one window of the application, it manages
 * fetching the content for the left and right panes
 */
class SFR.AppWindowModel : Object {
    private SFR.ApplicationModel application_model;

    public AppWindowModel (SFR.ApplicationModel application_model) {
        this.application_model = application_model;
    }

    public string left_uri { get; set; }
    public bool left_loading { get; set; default = false; }
    public SFR.Listing? left_listing { get; set; default = null; }
    public SFR.MetaModel left_meta {
        get; set; default = new SFR.MetaModelNone ();
    }

    /* Load an actual uri from the command line or "go to" box */
    public async void load_uri (string unclean_uri) {
        var uri = clean_uri (unclean_uri);
        this.load_left_uri (uri);
    }


    public async void load_left_uri (string uri) {
        this.left_uri = uri;

        if (!this.left_meta.applies_for_path (this.left_uri)) {
            this.left_meta = get_meta_model_for_path (
                this.left_uri, this.application_model
            );
        }
        this.left_loading = true;

        var aa = this.application_model.active_account;
        this.left_listing = yield aa.get_listing (this.left_uri);

        this.left_loading = false;
    }
}

const string[] CLEAN_URI_PREFIX = {
    "http://",
    "file://",
    "https://",
    "www.",
    "reddit.com"
};
string clean_uri (string raw_uri) {
    string uri = raw_uri;
    foreach (string prefix in CLEAN_URI_PREFIX) {
        if (uri.has_prefix (prefix)) {
            uri = uri.substring (prefix.length);
            debug (uri);
        }
    }
    return uri;
}

class SFR.AppWindowManager : Object {
    private Gtk.ApplicationWindow window;
    private SFR.AppWindowModel model;

    private Gtk.Paned content_paned;
    private Gtk.Paned header_paned;

    private SFR.LeftHeader left_header;
    private Gtk.HeaderBar right_header;

    public AppWindowManager (Gtk.ApplicationWindow window,
                             SFR.AppWindowModel model) {
        this.model = model;
        this.window = window;

        this.content_paned = new Gtk.Paned (Gtk.Orientation.HORIZONTAL);
        this.window.add (content_paned);
        this.content_paned.show ();

        var left_view = new SFR.LeftView (this.model);
        this.content_paned.add1 (left_view);
        left_view.show ();

        this.setup_header ();
        this.setup_paned_sync ();
    }

    private void setup_header () {
        this.header_paned = new Gtk.Paned (Gtk.Orientation.HORIZONTAL);
        this.window.set_titlebar (header_paned);
        this.header_paned.show ();

        var layout = Gtk.Settings.get_default ().gtk_decoration_layout;
        var left_layout = layout.split (":")[0];

        this.left_header = new LeftHeader (this.model);
        this.left_header.set_decoration_layout(layout.split (":")[0]);
        this.header_paned.add1 (this.left_header);
        this.left_header.show ();

        this.right_header = new Gtk.HeaderBar ();
        this.right_header.set_decoration_layout(":" + layout.split (":")[1]);
        this.right_header.show_close_button = true;
        this.header_paned.add2 (this.right_header);
        this.right_header.show ();
    }

    private void setup_paned_sync () {
        this.content_paned.notify["position"].connect((s, p) => {
            this.header_paned.freeze_notify ();
            this.header_paned.position = this.content_paned.position;
            this.header_paned.thaw_notify ();
        });
        this.header_paned.notify["position"].connect((s, p) => {
            this.content_paned.freeze_notify ();
            this.content_paned.position = this.header_paned.position;
            this.content_paned.thaw_notify ();
        });
        this.content_paned.position = 300;
        this.content_paned.position = this.header_paned.position;
    }
}
