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

class SFR.MarkdownTesterApp : Gtk.Application {
    public MarkdownTesterApp () {
        Object (
            application_id: "today.sam.something-for-reddit.markdown-tester",
            flags: ApplicationFlags.HANDLES_OPEN
        );
    }

    protected override void activate () {
        this._activate ();
    }

    private void _activate (string? text = null) {
        var window = new Gtk.ApplicationWindow (this);
        window.title = "Markdown Tester";
        window.set_default_size (400, 400);

        var w = new SFR.MarkdownTester (text);
        window.add (w);
        w.show ();

        window.show();

        var css_provider = new Gtk.CssProvider ();
        css_provider.load_from_resource (
            "/today/sam/reddit-is-gtk/markdown.css"
        );
        var screen = Gdk.Screen.get_default ();
        Gtk.StyleContext.add_provider_for_screen (
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        );
    }

    protected override void open (File[] files, string hint) {
        foreach (File file in files) {
            string uri = file.get_uri ();
            this._activate (uri);
        }
    }

    public static int main (string[] args) {
        var app = new SFR.MarkdownTesterApp ();
        return app.run (args);
    }
}

[GtkTemplate (ui="/today/sam/reddit-is-gtk/markdown-tester.ui")]
class SFR.MarkdownTester : Gtk.Paned {
    [GtkChild]
    Gtk.Bin preview_bin;

    public MarkdownTester (string? text) {
        this.size_allocate.connect ((w, alloc) => {
            this.position = alloc.width / 2;
        });
    }
    
    [GtkCallback]
    void text_buffer_changed_cb (Gtk.TextBuffer text_buffer) {
        Gtk.TextIter start, end;
        text_buffer.get_bounds (out start, out end);
        var text = text_buffer.get_text (start, end, true);

        var old_child = this.preview_bin.get_child ();
        if (old_child != null) {
            this.preview_bin.remove (old_child);
        }

        var w = new RedditMarkdownWidget (text);
        this.preview_bin.add (w);
        w.show ();
    }
}
