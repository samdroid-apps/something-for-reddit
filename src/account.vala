/* Copyright (C) 2016 Sam Parkinson
 *
 * This file contains the Account models, which represent an Account on
 * a site.  They are used to access the site's api.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

const string USER_AGENT = "GNU:something-for-reddit:v0.9 (by /u/samtoday)";

enum SFR.AccountType {
    ANNON,
    AUTHED
}

abstract class SFR.Account {
    protected Soup.Session session;

    public Account () {
        this.session = new Soup.Session ();
        this.session.user_agent = USER_AGENT;
    }

    public abstract int get_type_id ();
    public abstract void to_json (Json.Builder builder);
    public abstract void load_json (Json.Object root);

    public abstract async Json.Object send_request_get (string path);

    public async SFR.Listing get_listing (string path) {
        var root = yield this.send_request_get (path);
        return new SFR.Listing (root);
    }

    public abstract string username { get; }
    public abstract string icon_name { get; }
}

class SFR.AccountAnnon : Account {
    public override int get_type_id () {
        return SFR.AccountType.ANNON;
    }

    public override string username { get { return "Annon"; } }
    public override string icon_name { get { return "security-medium"; } }

    public override void load_json (Json.Object root) {}
    public override void to_json (Json.Builder builder) {}

    public override async Json.Object send_request_get (string path) {
        var msg = new Soup.Message(
            "GET", "https://api.reddit.com%s".printf (path)
        );
        var stream = yield this.session.send_async (msg);

        var parser = new Json.Parser ();
        yield parser.load_from_stream_async (stream);
        return parser.get_root ().get_object ();
    }
}

class SFR.AccountAuthed : SFR.Account {
    public override int get_type_id () {
        return SFR.AccountType.AUTHED;
    }

    private string access_token;
    private string refresh_token;

    private string _username = "Loading Username";
    public override string username { get { return this._username; } }
    private string _icon_name = "face-smile";
    public override string icon_name { get { return this._icon_name; } }

    public AccountAuthed.new_from_authorization_code (Json.Object root) {
        base ();
        this.access_token = root.get_string_member ("access_token");
        this.refresh_token = root.get_string_member ("refresh_token");
    }

    public async void setup () {
        var root = yield this.send_request_get ("/api/v1/me");
        this._username = root.get_string_member ("name");
    }

    public void set_icon_name (string icon_name) {
        this._icon_name = icon_name;
    }

    public override async Json.Object send_request_get (string path) {
        var msg = new Soup.Message(
            "GET", "https://oauth.reddit.com%s".printf (path)
        );
        msg.request_headers.append(
            "Authorization", "bearer %s".printf (this.access_token)
        );

        var stream = yield this.session.send_async (msg);
        if (msg.status_code == 401) {
            debug ("Hit %s, but token expired", path);
            yield this.do_refresh_token ();

            // Recursive hey?  Ain't yield beautiful
            return yield this.send_request_get (path);
        }

        var parser = new Json.Parser ();
        yield parser.load_from_stream_async (stream);
        return parser.get_root ().get_object ();
    }

    public async void do_refresh_token () {
        var msg = new Soup.Message(
            "POST", "https://www.reddit.com/api/v1/access_token"
        );
        msg.priority = Soup.MessagePriority.VERY_HIGH;

        var form = Soup.Form.encode (
            "grant_type", "refresh_token",
            "refresh_token", this.refresh_token,
            "redirect_uri", "redditgtk://done",
            null
        );
        msg.set_request(
            "application/x-www-form-urlencoded",
            Soup.MemoryUse.COPY,
            form.data
        );
        msg.request_headers.append(
            "Authorization", "Basic V0NOM2pxb0oxLTByMFE6Cg=="
        );

        var stream = yield this.session.send_async (msg);
        var parser = new Json.Parser ();
        yield parser.load_from_stream_async (stream);
        var root = parser.get_root ().get_object ();

        if (root.has_member ("error")) {
            error (
                "Error refreshing token: %s",
                root.get_string_member ("error")
            );
        }

        this.access_token = root.get_string_member ("access_token");
        debug ("Got new token: %s", this.access_token);
    }

    public override void load_json (Json.Object root) {
        this.access_token = root.get_string_member ("access_token");
        this.refresh_token = root.get_string_member ("refresh_token");
        this._username = root.get_string_member ("username");
        this._icon_name = root.get_string_member ("icon_name");
    }

    public override void to_json (Json.Builder builder) {
        builder.set_member_name ("access_token");
        builder.add_string_value (this.access_token);

        builder.set_member_name ("refresh_token");
        builder.add_string_value (this.refresh_token);

        builder.set_member_name ("username");
        builder.add_string_value (this.username);

        builder.set_member_name ("icon_name");
        builder.add_string_value (this.icon_name);
    }
}
