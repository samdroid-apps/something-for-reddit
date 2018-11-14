from unittest.mock import MagicMock

from redditisgtk import gtkutil
from redditisgtk.gtktestutil import fake_event


def test_process_shortcuts():
    up_cb = MagicMock()
    k_cb = MagicMock()

    shortcuts = {
        'Up': (up_cb, ['up']),
        '<Ctrl>k': (k_cb, ['k']),
    }

    gtkutil.process_shortcuts(shortcuts, fake_event('a', event_type=None))
    assert not up_cb.called
    assert not k_cb.called

    gtkutil.process_shortcuts(shortcuts, fake_event(65362))
    assert up_cb.called
    assert up_cb.call_args[0] == ('up',)

    gtkutil.process_shortcuts(shortcuts, fake_event('k'))
    assert not k_cb.called

    gtkutil.process_shortcuts(shortcuts, fake_event('k', ctrl=True))
    assert k_cb.called
    assert k_cb.call_args[0] == ('k',)
