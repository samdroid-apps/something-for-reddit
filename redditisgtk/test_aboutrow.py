from unittest.mock import MagicMock, patch

from gi.repository import Gtk

from redditisgtk import aboutrow
from redditisgtk.gtktestutil import with_test_mainloop, find_widget, wait_for


@with_test_mainloop
def test_subreddit():
    api = MagicMock()
    root = aboutrow.get_about_row(api, '/r/linux')


@with_test_mainloop
@patch('redditisgtk.submit.SubmitWindow', autospec=True)
def test_subreddit_submit(SubmitWindow):
        api = MagicMock()
        root = aboutrow.get_about_row(api, '/r/linux')

        find_widget(root, label='Submit', kind=Gtk.Button).emit('clicked')
        wait_for(lambda: SubmitWindow.called)
        SubmitWindow.assert_called_with(api, sub='linux')


@with_test_mainloop
def test_subreddit_subscribe_button_initial_state():
    api = MagicMock()
    api.lower_user_subs = ['/r/sub/']

    root = aboutrow.get_about_row(api, '/r/linux')
    find_widget(root, label='Subscribe', kind=Gtk.Button)

    root = aboutrow.get_about_row(api, '/r/sub')
    find_widget(root, label='Subscribed', kind=Gtk.Button)


@with_test_mainloop
def test_subreddit_subscribe_button_toggle():
    api = MagicMock()
    root = aboutrow.get_about_row(api, '/r/linux')
    btn = find_widget(root, label='Subscribe', kind=Gtk.Button)
    btn.emit('clicked')

    wait_for(lambda: api.set_subscribed.called)
    (name, active, cb), _ = api.set_subscribed.call_args
    assert name == 'linux'
    assert active == True
    
    cb(None)
    assert btn == find_widget(root, label='Subscribed', kind=Gtk.Button)


@with_test_mainloop
def test_subreddit_info():
    api = MagicMock()
    root = aboutrow.get_about_row(api, '/r/linux')

    expander = find_widget(root, kind=Gtk.Expander)
    expander.activate()
    wait_for(lambda: api.get_subreddit_info.called)

    (name, cb), _ = api.get_subreddit_info.call_args
    assert name == 'linux'
    cb({'data': {'description': 'hello'}})

    assert find_widget(root, label='hello').props.visible == True

    expander.activate()
    expander.activate()
    assert api.get_subreddit_info.call_count == 1


@with_test_mainloop
def test_user_about_row():
    api = MagicMock()
    root = aboutrow.get_about_row(api, '/u/bob')

    assert find_widget(root, label='bob')

    wait_for(lambda: api.get_user_info.called)
    (name, cb), _ = api.get_user_info.call_args
    assert name == 'bob'
    cb({'data': {'link_karma': 2, 'comment_karma': 1}})

    assert find_widget(root, label='2l / 1c')
