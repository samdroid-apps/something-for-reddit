import time
import typing

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio


def with_test_mainloop(function):
    def f(*args, **kwargs):
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
                    self.retval = function(*args, **kwargs)
                except Exception as e:
                    self.exception = e
                app.quit()

        app = MyApplication()
        app.run()
        Gio.Resource._unregister(r)
        if app.exception is not None:
            raise app.exception
        return app.retval

    return f

def _iter_all_widgets(root: Gtk.Widget):
    yield root
    if isinstance(root, Gtk.Container):
        for child in root.get_children():
            yield from _iter_all_widgets(child)

def find_widget(root: Gtk.Widget,
                kind: typing.Type[Gtk.Widget] = None,
                label: str = None,
                placeholder: str = None,
                many: bool = False):
    found = []
    for widget in _iter_all_widgets(root):
        if kind is not None and not isinstance(widget, kind):
            continue

        my_label = None
        if hasattr(widget, 'get_label'):
            my_label = widget.get_label()
        # Mainly for the stackswitcher radio buttons
        if not my_label and hasattr(widget, 'get_child'):
            child = widget.get_child()
            if hasattr(child, 'get_label'):
                my_label = child.get_label()
        if label is not None and my_label != label:
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
        assert len(found) == 1
        return found[0]


def wait_for(cond: typing.Callable[[], bool], timeout: float= 5):
    start_time = time.time()
    while True:
        if cond():
            return

        if time.time() - start_time > timeout:
            raise AssertionError('Timeout expired')

        Gtk.main_iteration_do(False)
