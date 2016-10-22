[GtkTemplate (ui="/today/sam/reddit-is-gtk/left-view.ui")]
class SFR.LeftView : Gtk.Box {
    private SFR.AppWindowModel model;

    [GtkChild]
    Gtk.ListBox list_box;

    public LeftView (SFR.AppWindowModel model) {
        this.model = model;
        this.model.notify["left-listing"].connect((s, p) => {
            debug ("Listing changed, rebuilding left view");
            this.list_box.foreach((widget) => {
                this.list_box.remove(widget);
            });
            foreach (var item in this.model.left_listing.items) {
                var w = new SFR.LeftViewItem (item);
                this.list_box.add(w);
                w.show();
            }
        });
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

        string l = "%i points · ".printf (this.model.score);
        if (this.model.n_comments == 0) {
            l += "no";
        } else {
            l += "%i".printf (this.model.n_comments);
        }
        l += " · ";
        if (this.model.is_selfpost) {
            l += "self.%s".printf (this.model.subreddit);
        } else {
            l += "%s · %s".printf (this.model.domain, this.model.subreddit);
        }
        l += " · TIMESTAMP · %s".printf (this.model.author_name);
        this.info.label = l;

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
}
