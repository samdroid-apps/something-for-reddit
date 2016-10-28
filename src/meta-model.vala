enum SFR.MetaType {
    NONE,
    SUBREDDIT,
    USER
}

abstract class SFR.MetaModel : Object {
    public abstract SFR.MetaType get_type_id ();
    // Called to know if I should keep this meta model instance even when I
    // am changing path
    public abstract bool applies_for_path (string path);
}

class SFR.MetaModelNone : SFR.MetaModel {
    public override SFR.MetaType get_type_id () { return SFR.MetaType.NONE; }
    public override bool applies_for_path (string path) {
        return false;
    }
}

class SFR.MetaModelSubreddit : SFR.MetaModel {
    public override SFR.MetaType get_type_id () {
        return SFR.MetaType.SUBREDDIT;
    }

    private string _subreddit;
    public string subreddit { get { return this._subreddit; } }
    private SFR.ApplicationModel model;

    public bool loaded { get; set; default = false; }

    private bool _is_subscribed;
    public bool is_subscribed {
        get { return this._is_subscribed; }
        set {
            this.loaded = false;
            this.model.active_account.set_subscribed.begin (
                this.subreddit,
                value,
                (obj, res) => {
                    this._is_subscribed = value;
                    this.notify_property ("is-subscribed");
                    this.loaded = true;
                }
            );
        }
    }
    public int64 subscribers { get; set; }
    public int64 active_users { get; set; }
    public string description { get; set; default = ""; }

    public MetaModelSubreddit (string subreddit, SFR.ApplicationModel model) {
        this._subreddit = subreddit;
        this.model = model;

        var aa = this.model.active_account;
        // Directly interacting with the Reddit API... Yuck?
        aa.send_request_get.begin (
            @"/r/$( this.subreddit )/about",
            (obj, res) => {
                Json.Object resp = aa.send_request_get.end (res);
                var data = resp.get_object_member ("data");
                this.loaded = true;
                this.description = data.get_string_member ("description");
                this._is_subscribed =
                    data.get_boolean_member ("user_is_subscriber");
                this.subscribers =
                    data.get_int_member ("subscribers");
                this.active_users =
                    data.get_int_member ("accounts_active");
            }
        );
    }

    public override bool applies_for_path (string path) {
        var split = path.split ("/");
        // split = [""/"r"/"subredditname"]
        if (split.length < 3 || split[1] != "r") {
            return false;
        }
        return split[2] == this._subreddit;
    }
}

SFR.MetaModel get_meta_model_for_path (string path,
                                       SFR.ApplicationModel model) {
    var split = path.split ("/");
    debug ("Get meta model for path: %s %u", path, split.length);

    if (split.length >= 3 && split[1] == "r" && split[2] != "all") {
        return new SFR.MetaModelSubreddit (split[2], model);
    }
    return new SFR.MetaModelNone ();
}
