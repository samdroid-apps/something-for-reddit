/* Copyright (C) 2016 Sam Parkinson
 *
 * This file is part of Something for Reddit.
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
    public abstract int get_type_id ();
    public abstract void to_json (Json.Builder builder);
    public abstract void load_json (Json.Object root);

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
}

class SFR.AccountAuthed : SFR.Account {
    public override int get_type_id () {
        return SFR.AccountType.AUTHED;
    }

    private string access_token;
    private string refresh_token;
    private Soup.Session session;

    private string _username = "Loading Username";
    public override string username { get { return this._username; } }
    private string _icon_name = "face-smile";
    public override string icon_name { get { return this._icon_name; } }

    public AccountAuthed () {
        this.session = new Soup.Session ();
        this.session.user_agent = USER_AGENT;
    }

    public AccountAuthed.new_from_authorization_code (Json.Object root) {
        this ();
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

    public async Json.Object send_request_get (string path) {
        var msg = new Soup.Message(
            "GET", "https://oauth.reddit.com%s".printf (path)
        );
        msg.request_headers.append(
            "Authorization", "bearer %s".printf (this.access_token)
        );

        var stream = yield this.session.send_async (msg);
        if (msg.status_code == 401) {
            stdout.printf ("TODO: FIX TOKEN EXPIRY\n");
        }

        var parser = new Json.Parser ();
        yield parser.load_from_stream_async (stream);
        return parser.get_root ().get_object ();
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
