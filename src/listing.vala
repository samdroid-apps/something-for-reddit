enum SFR.ListingItemType {
    POST
}

abstract class SFR.ListingItem : Object {
    public abstract int get_type_id ();
}

class SFR.Listing : Object {
    public List<SFR.ListingItem> items;

    public Listing (Json.Object root) {
        debug ("SFR.Listing.new");

        var listing = root.get_object_member ("data");
        listing.get_array_member ("children").foreach_element ((a, i, node) => {
            var obj = node.get_object ();
            var kind = obj.get_string_member ("kind");
            var data = obj.get_object_member ("data");

            if (kind == "t3") {
                this.items.append (new Post (data));
            } else {
                warning ("ListingItem of unknown kind: %s", kind);
            }
        });
    }
}

enum SFR.Vote {
    UP,
    NONE,
    DOWN
}

class SFR.Post : SFR.ListingItem {
    public override int get_type_id () { return SFR.ListingItemType.POST; }

    public string title { get; set; }
    public string domain { get; set; }
    public string selftext { get; set; }
    public string author_name { get; set; }
    public string url { get; set; }
    public string subreddit { get; set; }
    public int score { get; set; }
    public int n_comments { get; set; }
    public bool is_selfpost {
        get { return this.domain == "self." + this.subreddit; }
    }

    private SFR.Vote _vote;
    public SFR.Vote vote {
        get { return this._vote; }
        set {
            debug ("TODO: Send for for %s to %s", value.to_string (), this.fullname);
            this._vote = value;
        }
    }

    public string fullname;

    public Post (Json.Object root) {
        this.title = root.get_string_member ("title");
        this.domain = root.get_string_member ("domain");
        this.selftext = root.get_string_member ("selftext");
        this.subreddit = root.get_string_member ("subreddit");
        this.author_name = root.get_string_member ("author");
        this.url = root.get_string_member ("url");
        this.score = (int) root.get_int_member ("score");
        this.n_comments = (int) root.get_int_member ("num_comments");

        this.fullname = root.get_string_member ("name");

        if (root.get_null_member ("likes")) {
            this._vote = SFR.Vote.NONE;
        } else {
            this._vote = root.get_boolean_member ("likes") ?
                SFR.Vote.UP : SFR.Vote.DOWN;
        }

        /*
        foreach (unowned string name in root.get_members ()) {
            debug (name);
        }
        */
    }
}
