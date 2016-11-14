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
