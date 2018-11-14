from unittest.mock import MagicMock

from gi.repository import Gtk

from redditisgtk import subentry
from redditisgtk.gtktestutil import (with_test_mainloop, find_widget, wait_for,
                                     fake_event)


def test_clean_sub():
    assert subentry.clean_sub('') == '/'
    assert subentry.clean_sub('hello') == '/hello'
    assert subentry.clean_sub('/u/sam') == '/user/sam'


def test_clean_sub_passes_through_uris():
    assert subentry.clean_sub('https://') == 'https://'
    assert subentry.clean_sub('http://reddit.com') == 'http://reddit.com'


def test_format_sub_for_api_frontpage():
    assert subentry.format_sub_for_api('') == '/hot'
    assert subentry.format_sub_for_api('/') == '/hot'
    assert subentry.format_sub_for_api('/top') == '/top'


def test_format_sub_for_api_subreddit():
    assert subentry.format_sub_for_api('r/linux') == '/r/linux/hot'
    assert subentry.format_sub_for_api('/r/l/top?t=all') == '/r/l/top?t=all'


def test_format_sub_for_api_user():
    assert subentry.format_sub_for_api('/u/sam') == '/user/sam/overview'
    assert subentry.format_sub_for_api('/u/sam/up') == '/user/sam/up'


@with_test_mainloop
def test_subentry_create():
    api = MagicMock()
    api.user_name = 'username'
    root = subentry.SubEntry(api, text='/r/linux')

    assert find_widget(root, label='/r/linux')


@with_test_mainloop
def test_subentry_palette_activate():
    api = MagicMock()
    api.user_name = 'username'
    root = subentry.SubEntry(api)
    root.activate = MagicMock()

    down_button = find_widget(root, kind=Gtk.Button)
    down_button.emit('clicked')
    poproot = root._palette  # err IDK about this
    wait_for(lambda: poproot.props.visible)

    btn = find_widget(
            poproot, label='/user/username/submitted', kind=Gtk.Button)
    btn.emit('clicked')
    wait_for(lambda: root.activate.emit.called)
    assert root.activate.emit.call_args[0][0] == '/user/username/submitted'


@with_test_mainloop
def test_subentry_palette_subreddits():
    api = MagicMock()
    api.user_name = 'username'
    api.user_subs = ['/r/linux']
    root = subentry.SubEntry(api)

    down_button = find_widget(root, kind=Gtk.Button)
    down_button.emit('clicked')
    poproot = root._palette  # err IDK about this
    wait_for(lambda: poproot.props.visible)

    assert find_widget(poproot, label='/r/linux', many=True)
    assert not find_widget(poproot, label='/r/gnu', many=True)

    api.user_subs = ['/r/gnu']
    (cb,), _ = api.subs_changed.connect.call_args
    cb(api)
    assert not find_widget(poproot, label='/r/linux', many=True)
    assert find_widget(poproot, label='/r/gnu', many=True)


@with_test_mainloop
def test_subentry_open_uri():
    api = MagicMock()
    api.user_name = 'username'
    root = subentry.SubEntry(api)
    toplevel = MagicMock()

    entry = find_widget(root, kind=Gtk.Entry)
    # err IDK about this
    entry.is_focus = lambda: True
    entry.props.text = 'https://reddit.com/r/yes'

    poproot = root._palette  # err IDK about this
    poproot.get_toplevel = lambda: toplevel
    wait_for(lambda: poproot.props.visible)

    btn = find_widget(poproot, label='Open this reddit.com URI',
                      kind=Gtk.Button)
    btn.emit('clicked')
    wait_for(lambda: toplevel.goto_reddit_uri.called)
    toplevel.goto_reddit_uri.assert_called_once_with(
        'https://reddit.com/r/yes')


@with_test_mainloop
def test_subentry_palette_subreddits_filter():
    api = MagicMock()
    api.user_name = 'username'
    api.user_subs = ['/r/linux', '/r/gnu']
    root = subentry.SubEntry(api)
    poproot = root._palette  # err IDK about this

    entry = find_widget(root, kind=Gtk.Entry)
    entry.props.text = '/r/l'


    # When using the button, all should be visible
    down_button = find_widget(root, kind=Gtk.Button)
    down_button.emit('clicked')
    wait_for(lambda: poproot.props.visible)

    assert find_widget(poproot, label='/r/linux', many=True)
    assert find_widget(poproot, label='/r/gnu', many=True)

    # err IDK about this
    entry.is_focus = lambda: True
    entry.props.text = '/r/li'
    wait_for(lambda: poproot.props.visible)

    assert find_widget(poproot, label='/r/linux', many=True)
    assert not find_widget(poproot, label='/r/gnu', many=True)
