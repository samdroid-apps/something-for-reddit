from unittest.mock import MagicMock

from redditisgtk import newmarkdown
from redditisgtk.gtktestutil import (with_test_mainloop, snapshot_widget,
                                     find_widget)
from redditisgtk.conftest import assert_matches_snapshot


def test_hello():
    widget = newmarkdown.make_markdown_widget('hello')
    assert_matches_snapshot('newmarkdown--hello', snapshot_widget(widget))


def test_inline():
    widget = newmarkdown.make_markdown_widget('**b** _i_ ~~s~~ `<code>`')
    assert_matches_snapshot('newmarkdown--inline', snapshot_widget(widget))


def test_super():
    w = newmarkdown.make_markdown_widget('hello ^my world')
    assert_matches_snapshot('newmarkdown--super', snapshot_widget(w))

    w = newmarkdown.make_markdown_widget('hello ^(woah long) world')
    assert_matches_snapshot('newmarkdown--super-long', snapshot_widget(w))


def test_blockquote():
    widget = newmarkdown.make_markdown_widget('''
hello world

> **quoted**
>
> > sub quote
    ''')
    assert_matches_snapshot('newmarkdown--quote', snapshot_widget(widget))


def test_hr():
    widget = newmarkdown.make_markdown_widget('''
hello

---

world
    ''')
    assert_matches_snapshot('newmarkdown--hr', snapshot_widget(widget))


def test_heading():
    widget = newmarkdown.make_markdown_widget('''
# big
### small
    ''')
    assert_matches_snapshot('newmarkdown--heading', snapshot_widget(widget))


def test_list():
    widget = newmarkdown.make_markdown_widget('''
1. hello
3. world

* yeah
* sam
    ''')
    assert_matches_snapshot('newmarkdown--list', snapshot_widget(widget))


def test_link():
    widget = newmarkdown.make_markdown_widget('/r/linux')
    assert_matches_snapshot('newmarkdown--link--r', snapshot_widget(widget))

    cb = MagicMock()
    label = find_widget(widget, label='<a href="/r/linux">/r/linux</a>')
    label.get_toplevel().load_uri_from_label = cb

    label.emit('activate-link', '/r/linux')
    assert cb.called
    (link,), _ = cb.call_args
    assert link == '/r/linux'


def test_code():
    widget = newmarkdown.make_markdown_widget('''
hello:

    <html>
    </html>
''')
    assert_matches_snapshot('newmarkdown--code', snapshot_widget(widget))


def test_escaping():
    # This is "valid", e.g.
    # https://www.reddit.com/r/programmingcirclejerk/comments/9v7ix9/github_cee_lo_green_implements_fk_you_as_a_feature/e9adb06/
    widget = newmarkdown.make_markdown_widget('Please refer to <url> for')
    assert_matches_snapshot('newmarkdown--escaping', snapshot_widget(widget))

    w = newmarkdown.make_markdown_widget('Code: `<hello></hello>`')
    assert_matches_snapshot('newmarkdown--escaping-code', snapshot_widget(w))

    w = newmarkdown.make_markdown_widget('& I <3 you')
    assert_matches_snapshot('newmarkdown--escaping-amp', snapshot_widget(w))

def test_error():
    # OK so this comment is no longer valid, so I'm not going to bother to fix
    # things for it:
    # https://www.reddit.com/r/reddit.com/comments/6ewgt/reddit_markdown_primer_or_how_do_you_do_all_that/c03nmy1/
    w = newmarkdown.make_html_widget('<p>Issue &trade;</p>')
    assert_matches_snapshot('newmarkdown--error-handler', snapshot_widget(w))
