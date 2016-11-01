const int MAX_NESTING = 100;
const int MAX_TABLE_COLS = 100;

class SFR.RedditMarkdownWidget : Gtk.Label {
    public RedditMarkdownWidget (string markdown) {
        var callbacks = Snudown.Callbacks ();
        var md = new Snudown.Markdown (
            0,
            MAX_NESTING,
            MAX_TABLE_COLS,
            callbacks,
            null
        );
        Object (
            //label: markdown,
            label: "%i %i %i %i %i".printf (
                Snudown.TableFlags.ALIGN_L,
                Snudown.TableFlags.ALIGN_R,
                Snudown.TableFlags.ALIGN_CENTER,
                Snudown.TableFlags.ALIGNMASK,
                Snudown.TableFlags.HEADER
            ),
            selectable: true,
            wrap: true
        );
    }
}
