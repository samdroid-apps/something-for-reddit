from unittest.mock import MagicMock

from gi.repository import Gtk

from redditisgtk import emptyview 
from redditisgtk.gtktestutil import with_test_mainloop, find_widget, wait_for


@with_test_mainloop
def test_emptyview_has_label():
    root = emptyview.EmptyView('yo')
    assert find_widget(root, label='yo')


@with_test_mainloop
def test_emptyview_with_action():
    root = emptyview.EmptyView('yo', action='do')
    root.action = MagicMock()
    find_widget(root, label='do', kind=Gtk.Button).emit('clicked')
    wait_for(lambda: root.action.emit.called)
