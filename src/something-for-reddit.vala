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

const string APPLICATION_MODEL_PATH = "/tmp/something-for-reddit.json";

class SFR.ApplicationModel : Object {
    public Soup.Session soup_session;
    public List<SFR.Account> accounts;

    public ApplicationModel () {
        this.soup_session = new Soup.Session ();


        try {
            var parser = new Json.Parser ();
            parser.load_from_file (APPLICATION_MODEL_PATH);
            this.load_json (parser.get_root ().get_object ());
        } catch (Error e) {
            stdout.printf ("Couldn't read model file: %s\n", e.message);
            this.accounts.append (new SFR.AccountAnnon (this));
            this.active_account = this.accounts.nth_data (0);
        }
        
        this.notify.connect((s, p) => {
            this.save ();
        });
    }

    public bool should_show_welcome { get; set; default = true; }

    public SFR.Account active_account { get; set; }

    public void add_account (SFR.Account acc) {
        this.accounts.append (acc);
        this.active_account = acc;
        this.should_show_welcome = false;
        this.save ();
    }

    public void load_json (Json.Object root) {
        this.should_show_welcome =
            root.get_boolean_member ("should_show_welcome");

        root.get_array_member ("accounts").foreach_element ((a, i, node) => {
            var item = node.get_object ();
            var type = item.get_int_member ("type");

            SFR.Account acc = new SFR.AccountAnnon (this);
            if (type == SFR.AccountType.AUTHED) {
                acc = new SFR.AccountAuthed (this);
            }
            acc.load_json (item.get_object_member ("data"));
            this.accounts.append (acc);
        });

        this.active_account = this.accounts.nth_data (
            (int) root.get_int_member ("active_account")
        );
    }

    public void to_json (Json.Builder builder) {
        builder.set_member_name ("should_show_welcome");
        builder.add_boolean_value (this.should_show_welcome);

        builder.set_member_name ("accounts");
        builder.begin_array ();
        foreach (var a in this.accounts) {
            builder.begin_object ();

            builder.set_member_name ("type");
            builder.add_int_value (a.get_type_id ());

            builder.set_member_name ("data");
            builder.begin_object ();
            a.to_json (builder);
            builder.end_object ();

            builder.end_object ();
        }
        builder.end_array ();

        builder.set_member_name ("active_account");
        builder.add_int_value (this.accounts.index (this.active_account));
    }

    public void save () {
        var builder = new Json.Builder ();

        builder.begin_object ();
        this.to_json (builder);
        builder.end_object ();

        var gen = new Json.Generator ();
        gen.set_root (builder.get_root ());
        gen.to_file (APPLICATION_MODEL_PATH);
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

    [GtkCallback]
    private void continue_clicked_cb (Gtk.Button button) {
        this.model.should_show_welcome = false;
    }
}

class SFR.App : Gtk.Application {
    private SFR.ApplicationModel model;

    public App () {
        Object (
            application_id: "today.sam.reddit-is-gtk",
            flags: ApplicationFlags.HANDLES_OPEN
        );
        this.model = new SFR.ApplicationModel ();
    }

    protected override void activate () {
        var window = new Gtk.ApplicationWindow (this);
        window.title = "Something for Reddit";
        window.set_default_size (400, 400);

        this.reset_content (window);
        window.show();
        this.model.notify["should-show-welcome"].connect ((s, p) => {
            this.reset_content (window);
        });
    }

    protected override void open (File[] files, string hint) {
        foreach (File file in files) {
            string uri = file.get_uri ();

            var window = new Gtk.ApplicationWindow (this);
            window.title = "Something for Reddit";
            window.set_default_size (400, 400);

            var model  = new SFR.AppWindowModel (this.model);
            new SFR.AppWindowManager (window, model);
            model.load_uri (uri);
            window.show ();
        }
    }

    private void reset_content (Gtk.ApplicationWindow window) {
        if (window.get_child () != null) {
            window.remove (window.get_child ());
        }

        if (this.model.should_show_welcome) {
            var welcome = new SFR.WelcomeWindowContent (this.model);
            welcome.request_login.connect (() => {
                window.remove (window.get_child ());

                var view = new SFR.SignInView (this.model);
                window.add (view);
                view.show ();
            });

            window.add (welcome);
            welcome.show();
        } else {
            var model = new SFR.AppWindowModel (this.model);
            new SFR.AppWindowManager (window, model);
            model.load_uri ("/r/all");
        }
    }

    public static int main (string[] args) {
        var app = new SFR.App ();
        return app.run (args);
    }
}
