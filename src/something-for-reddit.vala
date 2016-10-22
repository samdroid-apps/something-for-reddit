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

class SFR.Account : Object {
    public string username {
        get { return "Annon"; }
    }
}

class SFR.AccountAuthed : SFR.Account {
    private string access_token;
    private string refresh_token;

    public AccountAuthed.new_from_authorization_code (Json.Object root) {
        this.access_token = root.get_string_member ("access_token");
        this.refresh_token = root.get_string_member ("refresh_token");
    }
}

class SFR.ApplicationModel : Object {
    public Soup.Session soup_session;
    public List<SFR.Account> accounts;

    public ApplicationModel () {
        this.soup_session = new Soup.Session ();
    }

    public bool should_show_welcome {
        get { return this.accounts.length () == 0; }
    }

    public signal void should_show_welcome_changed ();

    public void add_account (SFR.Account acc) {
        this.accounts.append (acc);
        if (this.accounts.length () == 1) {
            this.should_show_welcome_changed ();
        }
    }

    public SFR.Account active_account {
        get { return this.accounts.nth_data (0); }
    }
}

const string API_SCOPE = "edit history identity mysubreddits privatemessages submit subscribe vote read save";
const string CLIENT_ID = "WCN3jqoJ1-0r0Q";

[GtkTemplate (ui="/today/sam/reddit-is-gtk/sign-in-view.ui")]
class SFR.SignInView : Gtk.Stack {
    private string state;
    private SFR.ApplicationModel model;

    [GtkChild]
    private Gtk.ScrolledWindow webview_sw;

    public SignInView (SFR.ApplicationModel model) {
        this.model = model;
        this.state = "FIXME-make-a-real-random";

        var webview = new WebKit.WebView ();

        var ctx = webview.get_context ();
        ctx.register_uri_scheme ("redditgtk", this.uri_scheme);

        var uri = new Soup.URI (
            "https://www.reddit.com/api/v1/authorize.compact"
        );
        uri.set_query_from_fields (
            "client_id", CLIENT_ID,
            "response_type", "code",
            "redirect_uri", "redditgtk://done",
            "state", this.state,
            "duration", "permanent",
            "scope", API_SCOPE
        );

        webview.load_uri (uri.to_string (false));
        this.webview_sw.add (webview);
        webview.show ();
    }

    [GtkChild]
    private Gtk.Label error_label;

    private void uri_scheme (WebKit.URISchemeRequest request) {
        var uri = new Soup.URI (request.get_uri ());
        var query = Soup.form_decode (uri.get_query ());
        string state = query.lookup ("state");

        if (state != this.state) {
            this.display_error ("OAuth flow did not preserve state");
            return;
        }

        if (query.contains ("code")) {
            this.visible_child_name = "loading";
            string code = query.lookup ("code");
            this.grant_authorization_code (code);
        } else {
            this.display_error (query.lookup ("error"));
            return;
        }
    }

    private void grant_authorization_code (string code) {
        var msg = new Soup.Message(
            "POST", "https://www.reddit.com/api/v1/access_token"
        );
        msg.priority = Soup.MessagePriority.VERY_HIGH;
        var form = Soup.form_encode(
            "grant_type", "authorization_code",
            "code", code,
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

        this.model.soup_session.queue_message (msg, (session, msg) => {
            var parser = new Json.Parser ();
            parser.load_from_data (
                (string) msg.response_body.flatten ().data, -1
            );
            var root = parser.get_root ().get_object ();

            if (root.has_member ("error")) {
                this.display_error (root.get_string_member ("error"));
            }

            var acc = new SFR.AccountAuthed.new_from_authorization_code (root);
            this.model.add_account (acc);
        });
    }

    private void display_error (string message) {
        this.visible_child_name = "error";
        this.error_label.label = message;
    }
}

[GtkTemplate (ui="/today/sam/reddit-is-gtk/welcome-window-content.ui")]
class SFR.WelcomeWindowContent : Gtk.Box {
    private SFR.ApplicationModel model;

    public WelcomeWindowContent (SFR.ApplicationModel model) {
        this.model = model;
    }

    public signal void request_login ();

    [GtkCallback]
    private void sign_in_clicked_cb (Gtk.Button button) {
        this.request_login ();
    }
}

class SFR.App : Gtk.Application {
    private SFR.ApplicationModel model;

    public App () {
        Object (application_id: "today.sam.reddit-is-gtk");
        this.model = new SFR.ApplicationModel ();
    }

    protected override void activate () {
        var window = new Gtk.ApplicationWindow (this);
        window.title = "Something for Reddit";
        window.set_default_size (400, 400);

        this.reset_content (window);
        window.show();
        this.model.should_show_welcome_changed.connect ((m) => {
            this.reset_content (window);
        });
    }

    private void reset_content (Gtk.Window window) {
        if (window.get_child () != null) {
            window.remove (window.get_child ());
        }

        Gtk.Widget content;
        if (this.model.should_show_welcome) {
            var welcome = new SFR.WelcomeWindowContent (this.model);
            content = welcome;
            welcome.request_login.connect (() => {
                window.remove (window.get_child ());

                var view = new SFR.SignInView (this.model);
                window.add (view);
                view.show ();
            });
        } else {
            content = new Gtk.Label (this.model.active_account.username);
        }
        window.add (content);
        content.show();
    }

    public static int main (string[] args) {
        var app = new SFR.App ();
        return app.run (args);
    }
}
