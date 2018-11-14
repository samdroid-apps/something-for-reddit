from unittest.mock import MagicMock

from gi.repository import Gtk

from redditisgtk import identitybutton
from redditisgtk.gtktestutil import with_test_mainloop, find_widget, wait_for

@with_test_mainloop
def test_button_shows_name():
    ic = MagicMock()
    ic.active_token.user_name = 'UN1'

    btn = identitybutton.IdentityButton(ic)
    assert find_widget(btn, label='UN1', kind=Gtk.Button)

    (cb,), _ = ic.token_changed.connect.call_args
    ic.active_token.user_name = 'UN2'
    cb(ic)
    assert find_widget(btn, label='UN2', kind=Gtk.Button)


@with_test_mainloop
def test_popover_lists_accounts():
    ic = MagicMock()
    ic.all_tokens = [
            (1, MagicMock(user_name='user name 1')),
            (2, MagicMock(user_name='user name 2'))]

    popover = identitybutton._IdentityPopover(ic)
    assert find_widget(popover, label='Anonymous')
    assert find_widget(popover, label='user name 1')
    assert find_widget(popover, label='user name 2')

    ic.all_tokens = [(1, MagicMock(user_name='user name 1 new'))]
    (cb,), _ = ic.token_changed.connect.call_args
    cb(ic)
    assert find_widget(popover, label='Anonymous')
    assert find_widget(popover, label='user name 1 new')
    assert find_widget(popover, label='user name 2', many=True) == []
    assert find_widget(popover, label='user name 1', many=True) == []

@with_test_mainloop
def test_popover_selects_row():
    ic = MagicMock()
    ic.all_tokens = [
            (1, MagicMock(user_name='user name 1')),
            (2, MagicMock(user_name='user name 2'))]
    ic.active_token = ic.all_tokens[0][1]

    popover = identitybutton._IdentityPopover(ic)

    def get_row(text: str):
        label = find_widget(popover, label=text)
        while not isinstance(label, Gtk.ListBoxRow):
            assert label
            label = label.get_parent()
        return label

    row1 = get_row('user name 1')
    row2 = get_row('user name 2')
    listbox = find_widget(popover, kind=Gtk.ListBox)

    assert listbox.get_selected_rows() == [row1]
    listbox.emit('row-selected', row2)
    wait_for(lambda: ic.switch_account.called)
    assert ic.switch_account.call_args[0][0] == 2
