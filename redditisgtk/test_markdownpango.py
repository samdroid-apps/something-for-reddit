from unittest.mock import MagicMock

from redditisgtk import markdownpango


def test_markdown_to_pango_basic():
    assert markdownpango.markdown_to_pango('**hello**') == '<b>hello</b>'
    assert markdownpango.markdown_to_pango('`hello`') == '<tt>hello</tt>'
    assert markdownpango.markdown_to_pango('~~hello~~') == '<s>hello</s>'

def test_markdown_to_pango_list():
    assert markdownpango.markdown_to_pango('* hello\n* world') == \
            '∙ hello\n∙ world'
    assert markdownpango.markdown_to_pango('1. hello\n2. world') == \
            '∙ hello\n∙ world'

def test_markdown_to_pango_link():
    assert markdownpango.markdown_to_pango('https://example.com') == \
            '<a href="https://example.com">https://example.com</a>'

def test_sane_label_link():
    url = 'https://test-uri/'
    label = markdownpango.SaneLabel('hello ' + url)
    assert label.get_label() == 'hello ' + url

    cb = MagicMock()
    label.get_toplevel().load_uri_from_label = cb

    label.emit('activate-link', url)
    assert cb.called
    (link,), _ = cb.call_args
    assert link == url
