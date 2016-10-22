/* Copyright (C) 2016 Sam Parkinson
 *
 * This site provides the sign-in wizard.  The wizard has 4 states/views:
 * 1.  Sign in to Reddit (WebView)
 * 2.  Hit Reddit API to grant access token and refresh token
 * 3.  Hit Reddit API for user metadata (SFR.AccountAuthed.setup)
 * 4.  Pick icon to represent account
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
        var query = Soup.Form.decode (uri.get_query ());
        string state = query.lookup ("state");

        if (state != this.state) {
            this.display_error ("OAuth flow did not preserve state");
            return;
        }

        if (query.contains ("code")) {
            this.visible_child_name = "loading-oauth";
            string code = query.lookup ("code");
            this.grant_authorization_code (code);
        } else {
            this.display_error (query.lookup ("error"));
            return;
        }
    }

    private SFR.AccountAuthed acc;

    private void grant_authorization_code (string code) {
        var msg = new Soup.Message(
            "POST", "https://www.reddit.com/api/v1/access_token"
        );
        msg.priority = Soup.MessagePriority.VERY_HIGH;
        var form = Soup.Form.encode (
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

            this.visible_child_name = "loading-about-me";
            this.acc = new SFR.AccountAuthed (this.model);
            acc.load_authorization_code.begin (
                root,
                (obj, res) => { 
                    this.pick_emoji_title.label = "Almost There %s...".printf (
                        this.acc.username
                    );
                    this.visible_child_name = "pick-emoji";
                }
            );
        });
    }

    [GtkChild]
    private Gtk.Label pick_emoji_title;
    [GtkChild]
    private Gtk.FlowBox emoji_box;
    [GtkChild]
    private Gtk.Label pick_emoji_error;

    [GtkCallback]
    private void pick_emoji_clicked_cb (Gtk.Button button) {
        var children = this.emoji_box.get_selected_children ();
        Gtk.FlowBoxChild selected = children.nth_data (0);

        var image = (Gtk.Image) selected.get_child ();
        if (image.icon_name == null) {
            this.pick_emoji_error.show ();
        } else {
            this.acc.set_icon_name (image.icon_name);
            this.model.add_account (this.acc);
        }
    }

    private void display_error (string message) {
        this.visible_child_name = "error";
        this.error_label.label = message;
    }
}
