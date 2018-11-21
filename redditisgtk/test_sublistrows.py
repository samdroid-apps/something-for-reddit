import json
from unittest.mock import MagicMock, patch

from gi.repository import Gtk

from redditisgtk import sublistrows
from redditisgtk.gtktestutil import (with_test_mainloop, find_widget, wait_for,
                                     fake_event)

@with_test_mainloop
def test_subitemrow_thumb_from_preview(json_loader):
    api = MagicMock()
    row = sublistrows.LinkRow(api,
                              json_loader('sublistrows--thumb-from-previews'))

    assert api.download_thumb.called
    (url, cb), _ = api.download_thumb.call_args
    assert url == 'https://external-preview.redd.it/AxVEZvB8AZsAPFSlrGM3HGDCss0bxYEbNu89NmgUdTg.jpg?width=108&crop=smart&auto=webp&s=a906c3a7241def971591ded4d7f9ff9abe6b050c'


@with_test_mainloop
def test_message_row_pm(json_loader):
    api = MagicMock()
    row = sublistrows.MessageRow(api, json_loader('sublistrows--pm'))

    assert find_widget(row, label='re: Blog down')
    assert find_widget(row, label='thanks a lot!')
    # author:
    assert find_widget(row, label='bambambazooka', kind=Gtk.Button)


@with_test_mainloop
def test_message_row_pm_shortcuts(json_loader):
    api = MagicMock()
    toplevel = MagicMock()

    row = sublistrows.MessageRow(api, json_loader('sublistrows--pm'))
    row.get_toplevel = lambda: toplevel

    row.do_event(fake_event('a'))
    toplevel.goto_sublist.assert_called_once_with('/u/bambambazooka')
