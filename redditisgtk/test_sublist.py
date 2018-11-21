import json
from unittest.mock import MagicMock, patch

from gi.repository import Gtk

from redditisgtk import sublist
from redditisgtk.gtktestutil import (with_test_mainloop, find_widget, wait_for,
                                     fake_event)


class FixtureMessageRow(Gtk.Label):
    def __init__(self, api, data):
        assert data['win']
        Gtk.Label.__init__(self, label='message row')


class FixtureLinkRow(Gtk.Label):
    goto_comments = MagicMock()

    def __init__(self, api, data):
        assert data['win']
        Gtk.Label.__init__(self, label='link row')


class FixtureMoreItemsRow(Gtk.Label):
    load_more = MagicMock()

    def __init__(self, data):
        assert data == 'win'
        Gtk.Label.__init__(self, label='more items row')


@with_test_mainloop
@patch('redditisgtk.aboutrow.get_about_row',
       return_value=Gtk.Label(label='about row'))
@patch('redditisgtk.sublistrows.MessageRow', FixtureMessageRow)
@patch('redditisgtk.sublistrows.LinkRow', FixtureLinkRow)
@patch('redditisgtk.sublistrows.MoreItemsRow', FixtureMoreItemsRow)
def test_sublist_create(get_about_row):
    api = MagicMock()
    root = sublist.SubList(api, '/r/linux')

    assert find_widget(root, kind=Gtk.Spinner)
    assert root.get_uri() == '/r/linux'

    (sub, cb), _ = api.get_list.call_args
    assert sub == '/r/linux'
    data = {
        'data': {
            'children': [
                {'kind': 't1', 'win': 1},
                {'kind': 't3', 'win': 1},
            ],
            'after': 'win',
        },
    }
    # Load the data
    cb(data)
    assert not find_widget(root, kind=Gtk.Spinner, many=True)

    get_about_row.assert_called_with(api, '/r/linux')
    assert find_widget(root, label='about row', kind=Gtk.Label)
    assert find_widget(root, kind=FixtureMessageRow)
    assert find_widget(root, kind=FixtureLinkRow)
    assert find_widget(root, kind=FixtureMoreItemsRow)
