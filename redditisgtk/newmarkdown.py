import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
import html

import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern, SimpleTagPattern
from markdown.treeprocessors import Treeprocessor

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango


_URI_RE = r'(https?://|/r/|/u/)([^ \r\t\n]+)'


class _URIPattern(Pattern):
    def handleMatch(self, match):
        uri = match.group(2) + match.group(3)
        el = Element('a')
        el.set('href', uri)
        el.text = markdown.util.AtomicString(uri)
        return el


class _RedditExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['uriregex'] = _URIPattern(_URI_RE, md)

        s_tag = SimpleTagPattern('(~~)([^~]+)~~', 'strike')
        md.inlinePatterns.add('s', s_tag, '>not_strong')

        html_pattern = md.inlinePatterns['html']
        old = html_pattern.handleMatch
        def handleMatch(match):
            # Reddit allows interesting markdown, for example this should pass
            # through fully: "Hello <name>!"
            group_number = 2 if markdown.version_info[0] <= 2 else 1
            raw_html = html_pattern.unescape(match.group(2))
            try:
                root = ElementTree.fromstring('<div>'+raw_html+'</div>')
            except ElementTree.ParseError:
                # This is not proper html, so pass it through rather than
                # extracting it into an unchangeable stash
                return raw_html
            else:
                # This is proper html, so pass it through
                return old(data)
        html_pattern.handleMatch = handleMatch


MDX_CONTEXT = markdown.Markdown(extensions=[_RedditExtension()])


class AlignedLabel(Gtk.Label):
    def __init__(self, **kwargs):
        super().__init__(
            xalign=0,
            justify=Gtk.Justification.LEFT,
            wrap=True,
            wrap_mode=Pango.WrapMode.WORD_CHAR,
            **kwargs)


HTML_TO_PANGO_INLINE_TAG = {
    'strong': ('<b>', '</b>'),
    'em': ('<i>', '</i>'),
    'strike': ('<s>', '</s>'),
    'br': ('\n', ''),
}

def _html_inline_tag_to_pango(el: Element) -> (str, str):
    if el.tag in HTML_TO_PANGO_INLINE_TAG:
        return HTML_TO_PANGO_INLINE_TAG[el.tag]
    elif el.tag == 'a':
        if el.get('href') is None:
            return '', ''

        href = html.escape(el.get('href'))
        return f'<a href="{href}">', '</a>'
    else:  # pragma: no cover
        print('Unknown inline tag', el)
        # ElementTree.dump(el) 
        return '', ''


def _make_inline_label(el: Element, initial_text: str = None) -> Gtk.Label:
    fragments = [initial_text]

    def extract_text(el, root=False):
        if el.tag == 'code':
            # special case, as code is processed before rawhtml, so it does not
            # get escaped
            fragments.append('<tt>')
            text = ''.join(el.itertext())
            fragments.append(html.escape(text))
            fragments.append('</tt>')
            return

        if not root:
            start, end = _html_inline_tag_to_pango(el)
            fragments.append(start)
        fragments.append(html.escape(el.text or '').replace('\n', ''))
        for inner in el:
            extract_text(inner)
            fragments.append(html.escape(inner.tail or '').replace('\n', ''))
        if not root:
            fragments.append(end)

    extract_text(el, True)

    label = AlignedLabel()
    label.connect('activate-link', __activate_link_cb)

    markup = ''.join(x for x in fragments if x is not None)
    label.set_markup(markup)

    label.show()
    return label


def __activate_link_cb(label, uri):
    window = label.get_toplevel()
    window.load_uri_from_label(uri)
    return True


BLOCK_TAGS = ['div', 'ol', 'ul', 'blockquote']
HEADING_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']


def _make_li_widget(el: Element, parent: Element, index: int) -> Gtk.Widget:
    dot = '⚫ '
    if parent is not None and parent.tag == 'ol':
        dot = f'{index+1}. '
    return _make_inline_label(el, initial_text=dot)


def _make_block_widget(el: Element) -> Gtk.Widget:
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.get_style_context().add_class('mdx-block')
    box.get_style_context().add_class('mdx-block-'+el.tag)

    assert el.text is None or el.text.strip() == ''
    for i, inner in enumerate(el):
        assert inner.tail is None or inner.tail.strip() == ''
        box.add(convert_tree_to_widgets(inner, parent=el, index=i))

    box.show()
    return box

def _make_heading_widget(el: Element) -> Gtk.Widget:
    label = AlignedLabel()
    label.props.label = el.text
    label.get_style_context().add_class('mdx-heading')
    label.get_style_context().add_class('mdx-heading-'+el.tag)
    label.show()
    return label


def _make_code_widget(el: Element) -> Gtk.Widget:
    assert len(list(el)) == 1
    child = list(el)[0]
    code = child.text
    assert code is not None

    label = AlignedLabel()
    label.props.label = html.unescape(code)
    label.get_style_context().add_class('mdx-block-code')
    label.show()
    return label


def convert_tree_to_widgets(el: Element, parent: Element = None,
                            index: int = None) -> Gtk.Label:
    if el.tag == 'p':
        return _make_inline_label(el)
    elif el.tag == 'li':
        return _make_li_widget(el, parent, index)
    elif el.tag in BLOCK_TAGS:
        return _make_block_widget(el)
    elif el.tag in HEADING_TAGS:
        return _make_heading_widget(el)
    elif el.tag == 'pre':
        return _make_code_widget(el)
    elif el.tag == 'hr':
        return Gtk.Separator(visible=True)
    else:  # pragma: no cover
        print('Unhandled tag', el)
        placeholder = Gtk.Spinner()
        placeholder.start()
        placeholder.show()
        return placeholder


def make_markdown_widget(text: str) -> Gtk.Widget:
    '''
    Make a widget of some given text.  The markdown widget will be resizable
    (it will wrap) and it will probably be a GTK box.

    Args:

        text - markdown text input
    '''
    html = MDX_CONTEXT.convert(text)
    root = ElementTree.fromstring('<div>'+html+'</div>')
    return convert_tree_to_widgets(root)


if __name__ == '__main__':
    # Usage:
    #   python newmarkdown.py test.md
    with open(sys.argv[1]) as f:
        test_text = f.read()

    window = Gtk.Window()

    w = make_markdown_widget(test_text)
    sw = Gtk.ScrolledWindow()
    sw.add(w)
    sw.show()

    window.add(sw)
    window.set_default_size(400, 400)
    window.show()
    window.connect('delete-event', Gtk.main_quit)
    Gtk.main()
