import json
from unittest.mock import MagicMock

from gi.repository import Gtk

from redditisgtk import comments
from redditisgtk.gtktestutil import (with_test_mainloop, find_widget, wait_for,
                                     get_focused, fake_event)

PERMALINK = '/r/MaliciousCompliance/comments/9vzevr/you_need_a_doctors_note_you_got_it/'


@with_test_mainloop
def test_load_selftext(datadir):
    api = MagicMock()

    root = comments.CommentsView(api, permalink=PERMALINK)
    assert find_widget(root, kind=Gtk.Spinner)

    (method, link, cb), _ = api.send_request.call_args
    assert method == 'GET'
    assert link == PERMALINK

    with open(datadir / 'comments--thread.json') as f:
        cb(json.load(f))

    # Title:
    assert find_widget(root, label='You need a doctor’s note? You got it!')
    # Body:
    assert find_widget(root, label='This happened today.')
