from unittest.mock import MagicMock

from redditisgtk import newmarkdown
from redditisgtk.gtktestutil import (with_test_mainloop, snapshot_widget,
                                     find_widget)
from redditisgtk.conftest import assert_matches_snapshot


def test_hello(datadir):
    widget = newmarkdown.make_markdown_widget('hello')
    assert_matches_snapshot('newmarkdown--hello', snapshot_widget(widget))


def test_inline(datadir):
    widget = newmarkdown.make_markdown_widget('**b** _i_ ~~s~~ `<code>`')
    assert_matches_snapshot('newmarkdown--inline', snapshot_widget(widget))


def test_blockquote(datadir):
    widget = newmarkdown.make_markdown_widget('''
hello world

> **quoted**
>
> > sub quote
    ''')
    assert_matches_snapshot('newmarkdown--quote', snapshot_widget(widget))


def test_hr(datadir):
    widget = newmarkdown.make_markdown_widget('''
hello

---

world
    ''')
    assert_matches_snapshot('newmarkdown--hr', snapshot_widget(widget))


def test_heading(datadir):
    widget = newmarkdown.make_markdown_widget('''
# big
### small
    ''')
    assert_matches_snapshot('newmarkdown--heading', snapshot_widget(widget))


def test_list(datadir):
    widget = newmarkdown.make_markdown_widget('''
1. hello
3. world

* yeah
* sam
    ''')
    assert_matches_snapshot('newmarkdown--list', snapshot_widget(widget))


def test_link(datadir):
    widget = newmarkdown.make_markdown_widget('/r/linux')
    assert_matches_snapshot('newmarkdown--link--r', snapshot_widget(widget))

    cb = MagicMock()
    label = find_widget(widget, label='<a href="/r/linux">/r/linux</a>')
    label.get_toplevel().load_uri_from_label = cb

    label.emit('activate-link', '/r/linux')
    assert cb.called
    (link,), _ = cb.call_args
    assert link == '/r/linux'


def test_code(datadir):
    widget = newmarkdown.make_markdown_widget('''
hello:

    <html>
    </html>
''')
    assert_matches_snapshot('newmarkdown--code', snapshot_widget(widget))


def test_escaping(datadir):
    # This is "valid", e.g.
    # https://www.reddit.com/r/programmingcirclejerk/comments/9v7ix9/github_cee_lo_green_implements_fk_you_as_a_feature/e9adb06/
    widget = newmarkdown.make_markdown_widget('Please refer to <url> for')
    assert_matches_snapshot('newmarkdown--escaping', snapshot_widget(widget))

    w = newmarkdown.make_markdown_widget('Code: `<hello></hello>`')
    assert_matches_snapshot('newmarkdown--escaping-code', snapshot_widget(w))
