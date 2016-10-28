class SFR.RedditMarkdownWidget : Gtk.Label {
    public RedditMarkdownWidget (string markdown) {
        Object (
            label: markdown,
            selectable: true,
            wrap: true
        );
    }
}
