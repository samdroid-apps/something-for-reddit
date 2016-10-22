[GtkTemplate (ui="/today/sam/reddit-is-gtk/left-view.ui")]
class SFR.LeftView : Gtk.Box {
    private SFR.AppWindowModel model;

    [GtkChild]
    Gtk.ListBox list_box;

    // the only GtkBin like thing I found in glade
    [GtkChild]
    Gtk.Revealer meta_bin;

    public LeftView (SFR.AppWindowModel model) {
        this.model = model;
        this.model.notify["left-listing"].connect ((s, p) => {
            debug ("Listing changed, rebuilding left view");
            this.list_box.foreach((widget) => {
                this.list_box.remove(widget);
            });
            foreach (var item in this.model.left_listing.items) {
                var w = new SFR.LeftViewItem (item);
                this.list_box.add(w);
                w.show();
            }

            debug ("Listing meta, rebuilding");
            var child = this.meta_bin.get_child ();
            if (child != null) {
                this.meta_bin.remove (child);
            }

            var lm = this.model.left_meta;
            var type = lm.get_type_id ();
            Gtk.Widget w = null;
            if (type == SFR.MetaType.SUBREDDIT) {
                w = new SFR.MetaToolbarSubreddit ((SFR.MetaModelSubreddit) lm);
            }
            if (w != null) {
                this.meta_bin.add (w);
                w.show ();
            }
        });
    }
}


[GtkTemplate (ui="/today/sam/reddit-is-gtk/meta-toolbar-subreddit.ui")]
class SFR.MetaToolbarSubreddit : Gtk.Box {
    private SFR.MetaModelSubreddit model;

    [GtkChild]
    private Gtk.Stack main_stack;
    [GtkChild]
    private Gtk.Stack subscribe_stack;
    [GtkChild]
    private Gtk.Entry active;
    [GtkChild]
    private Gtk.Entry subs;

    public MetaToolbarSubreddit (SFR.MetaModelSubreddit model) {
        this.model = model;

        this.loaded_changed ();
        this.model.notify["loaded"].connect ((s, p) => {
            this.loaded_changed ();
        });

        this.model.bind_property (
            "is_subscribed", this.subscribe_stack, "visible-child-name",
            BindingFlags.DEFAULT | BindingFlags.SYNC_CREATE,
            (binding, srcval, ref targetval) => {
                bool src = (bool) srcval;
                targetval.set_string (src ? "unsubscribe" : "subscribe");
                return true;
            }
        );
        this.model.bind_property (
            "subscribers", this.subs, "text",
            BindingFlags.DEFAULT | BindingFlags.SYNC_CREATE,
            (binding, srcval, ref targetval) => {
                int64 src = (int64) srcval;
                targetval.set_string ("%lld".printf (src));
                return true;
            }
        );
        this.model.bind_property (
            "active_users", this.active, "text",
            BindingFlags.DEFAULT | BindingFlags.SYNC_CREATE,
            (binding, srcval, ref targetval) => {
                int64 src = (int64) srcval;
                targetval.set_string ("%lld".printf (src));
                return true;
            }
        );
    }

    private void loaded_changed () {
        this.main_stack.visible_child_name = (
            this.model.loaded ? "loaded" : "loading"
        );
    }
}

class SFR.LeftViewItem : Gtk.ListBoxRow {
    public LeftViewItem (SFR.ListingItem item) {
        var type = item.get_type_id ();
        Gtk.Widget? child = null;
        if (type == SFR.ListingItemType.POST) {
            child = new SFR.LeftViewPost ((SFR.Post) item);
        }

        if (child != null) {
            this.add (child);
            child.show ();
        }
    }
}

const int SUMMARY_LEN = 500;

int min(int a, int b) { return a < b ? a : b; }

[GtkTemplate (ui="/today/sam/reddit-is-gtk/left-view-post.ui")]
class SFR.LeftViewPost : Gtk.Box {
    private SFR.Post model;

    [GtkChild]
    Gtk.Label title;
    [GtkChild]
    Gtk.Label summary;
    [GtkChild]
    Gtk.Label info;
    [GtkChild]
    Gtk.Button upvote;
    [GtkChild]
    Gtk.Button downvote;

    public LeftViewPost (SFR.Post model) {
        this.model = model;
        this.title.label = this.model.title;

        if (this.model.is_selfpost) {
            this.summary.label = this.model.selftext.substring(
                0, min(SUMMARY_LEN, this.model.selftext.length)
            );
        } else {
            this.summary.label = "";
        }


        this.model.notify.connect ((s, p) => { this.update_info_label (); });
        this.update_info_label ();

        this.model.bind_property (
            "vote", this.upvote, "active",
            BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL,
            (binding, srcval, ref targetval) => {
                SFR.Vote src = (SFR.Vote) srcval;
                targetval.set_boolean (src == SFR.Vote.UP);
                return true;
            },
            (binding, srcval, ref targetval) => {
                bool src = (bool) srcval;
                targetval.set_enum (src ? SFR.Vote.UP : SFR.Vote.NONE);
                return true;
            }
        );
        this.model.bind_property (
            "vote", this.downvote, "active",
            BindingFlags.SYNC_CREATE | BindingFlags.BIDIRECTIONAL,
            (binding, srcval, ref targetval) => {
                SFR.Vote src = (SFR.Vote) srcval;
                targetval.set_boolean (src == SFR.Vote.DOWN);
                return true;
            },
            (binding, srcval, ref targetval) => {
                bool src = (bool) srcval;
                targetval.set_enum (src ? SFR.Vote.DOWN : SFR.Vote.NONE);
                return true;
            }
        );

    }

    private void update_info_label () {
        string l = "%i points · ".printf (this.model.score);
        if (this.model.n_comments == 0) {
            l += "no ";
        } else {
            l += "%i".printf (this.model.n_comments);
        }
        l += "c · ";
        if (this.model.is_selfpost) {
            l += "self.%s".printf (this.model.subreddit);
        } else {
            l += "%s · %s".printf (this.model.domain, this.model.subreddit);
        }
        l += " · TIMESTAMP · %s".printf (this.model.author_name);
        this.info.label = l;
    }
}
