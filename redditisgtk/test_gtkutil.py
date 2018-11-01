from unittest.mock import MagicMock

from gi.repository import Gdk

from redditisgtk import gtkutil


def fake_event(keyval, event_type=Gdk.EventType.KEY_PRESS, ctrl=False):
    ev = MagicMock()
    ev.type = event_type
    ev.keyval = keyval
    if ctrl:
        ev.state = Gdk.ModifierType.CONTROL_MASK
    else:
        ev.state = 0
    return ev


def test_process_shortcuts():
    up_cb = MagicMock()
    k_cb = MagicMock()

    shortcuts = {
        'Up': (up_cb, ['up']),
        '<Ctrl>k': (k_cb, ['k']),
    }

    gtkutil.process_shortcuts(shortcuts, fake_event('', event_type=None))
    assert not up_cb.called
    assert not k_cb.called

    gtkutil.process_shortcuts(shortcuts, fake_event(65362))
    assert up_cb.called
    assert up_cb.call_args[0] == ('up',)

    gtkutil.process_shortcuts(shortcuts, fake_event(107))
    assert not k_cb.called

    gtkutil.process_shortcuts(shortcuts, fake_event(107, ctrl=True))
    assert k_cb.called
    assert k_cb.call_args[0] == ('k',)
