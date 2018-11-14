import json
from unittest.mock import MagicMock, patch

from gi.repository import Gtk

from redditisgtk import posttopbar
from redditisgtk.gtktestutil import (with_test_mainloop, find_widget, wait_for,
                                     fake_event)


@with_test_mainloop
def test_for_comment(datadir):
    api = MagicMock()
    toplevel_cv = MagicMock()

    with open(datadir / 'posttopbar--comment.json') as f:
        data = json.load(f)

    bar = posttopbar.PostTopBar(api, data, toplevel_cv)
    # author
    assert find_widget(bar, label='andnbspsc', kind=Gtk.Button)
    # score 
    assert find_widget(bar, label='score hidden', kind=Gtk.Button)
    # no subreddit
    assert not find_widget(bar, label='linux', many=True)


@with_test_mainloop
def test_for_post(datadir):
    api = MagicMock()
    toplevel_cv = MagicMock()

    with open(datadir / 'posttopbar--post.json') as f:
        data = json.load(f)

    bar = posttopbar.PostTopBar(api, data, toplevel_cv, show_subreddit=True)
    # author
    assert find_widget(bar, label='sandragen', kind=Gtk.Button)
    # score
    assert find_widget(bar, label='score hidden', kind=Gtk.Button)
    # subreddit
    assert find_widget(bar, label='linux', many=True)


@with_test_mainloop
def test_vote_key(datadir):
    api = MagicMock()
    toplevel_cv = MagicMock()
    with open(datadir / 'posttopbar--comment.json') as f:
        data = json.load(f)

    bar = posttopbar.PostTopBar(api, data, toplevel_cv)
    bar.get_toplevel = lambda: api
    bar.do_event(fake_event('u'))
    assert api.vote.call_args[0] == ('t1_e9nhj7n', +1)
    bar.do_event(fake_event('d'))
    assert api.vote.call_args[0] == ('t1_e9nhj7n', -1)
    bar.do_event(fake_event('n'))
    assert api.vote.call_args[0] == ('t1_e9nhj7n', 0)


@with_test_mainloop
def test_reply_palette(datadir):
    api = MagicMock()
    toplevel_cv = MagicMock()
    with open(datadir / 'posttopbar--comment.json') as f:
        data = json.load(f)

    bar = posttopbar.PostTopBar(api, data, toplevel_cv)
    bar.get_toplevel = lambda: api
    poproot = Gtk.Popover()
    with patch('gi.repository.Gtk.Popover') as Popover:
        Popover.return_value = poproot
        bar.do_event(fake_event('r'))

        wait_for(lambda: Popover.called)

    assert poproot.props.visible
    tv = find_widget(poproot, kind=Gtk.TextView)
    tv.props.buffer.set_text('hello')

    btn = find_widget(poproot, kind=Gtk.Button, label='Post Reply')
    btn.emit('clicked')
    wait_for(lambda: btn.props.sensitive is False)
    (name, text, cb), _ = api.reply.call_args
    assert name == 't1_e9nhj7n'
    assert text == 'hello'

    cb({'json': {'data': {'things': [{'data': {'id': 'MYID'}}]}}})
    assert poproot.props.visible == False
