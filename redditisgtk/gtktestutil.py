import time
import typing
import functools
from unittest.mock import MagicMock

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gio


def with_test_mainloop(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # It would probably be slightly better to find this from PATH
        r = Gio.resource_load('./__build_prefix/share/something-for-reddit'
                              '/reddit-is-gtk.gresource')
        Gio.Resource._register(r)

        class MyApplication(Gtk.Application):
            def __init__(self):
                Gtk.Application.__init__(self, application_id='today.sam.reddit-is-gtk')
                self.exception = None
                self.retval = None

            def do_activate(self):
                try:
                    self.retval = func(*args, **kwargs)
                except Exception as e:
                    self.exception = e
                app.quit()

        app = MyApplication()
        app.run()
        Gio.Resource._unregister(r)
        if app.exception is not None:
            raise app.exception
        return app.retval

    return wrapper


def _iter_all_widgets(root: Gtk.Widget):
    yield root
    if isinstance(root, Gtk.Container):
        for child in root.get_children():
            yield from _iter_all_widgets(child)


def get_focused(root: Gtk.Widget) -> Gtk.Widget:
    for widget in _iter_all_widgets(root):
        if widget.is_focus():
            return widget


def get_label_for_widget(widget: Gtk.Widget):
    my_label = None
    if hasattr(widget, 'get_label'):
        my_label = widget.get_label()

    # Mainly for the stackswitcher radio buttons
    if not my_label and hasattr(widget, 'get_child'):
        child = widget.get_child()
        if hasattr(child, 'get_label'):
            my_label = child.get_label()

    if not my_label and hasattr(widget, 'get_text'):
        my_label = widget.get_text()

    return my_label


def debug_print_widgets(root: Gtk.Widget):  # pragma: no cover
    for widget in _iter_all_widgets(root):
        print(widget, get_label_for_widget(widget))


def snapshot_widget(root: Gtk.Widget) -> dict:
    style = root.get_style_context()
    snap = {
        'type': type(root).__name__,
        'label': get_label_for_widget(root),
        'classes': style.list_classes()}

    if isinstance(root, Gtk.Container):
        snap['children'] = list(map(snapshot_widget, root.get_children()))

    return snap


def find_widget(root: Gtk.Widget,
                kind: typing.Type[Gtk.Widget] = None,
                label: str = None,
                placeholder: str = None,
                many: bool = False):
    found = []
    for widget in _iter_all_widgets(root):
        if kind is not None and not isinstance(widget, kind):
            continue

        if label is not None and get_label_for_widget(widget) != label:
            continue

        my_placeholder = None
        if hasattr(widget, 'get_placeholder_text'):
            my_placeholder = widget.get_placeholder_text()
        if placeholder and my_placeholder != placeholder:
            continue

        found.append(widget)

    if many:
        return found
    else:
        if len(found) == 1:
            return found[0]
        else:
            debug_print_widgets(root)
            assert len(found) == 1


def wait_for(cond: typing.Callable[[], bool], timeout: float= 5):
    start_time = time.time()
    while True:
        if cond():
            return

        if time.time() - start_time > timeout:
            raise AssertionError('Timeout expired')

        Gtk.main_iteration_do(False)


def fake_event(keyval, event_type=Gdk.EventType.KEY_PRESS, ctrl=False):
    if isinstance(keyval, str):
        keyval = ord(keyval)

    ev = MagicMock()
    ev.type = event_type
    ev.keyval = keyval
    if ctrl:
        ev.state = Gdk.ModifierType.CONTROL_MASK
    else:
        ev.state = 0
    return ev
