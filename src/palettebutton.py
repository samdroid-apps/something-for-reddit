from gi.repository import GObject


class _PaletteButton(GObject.GObject):
    '''
    Like a Gtk.MenuButton, but instead of requiring the palette to be
    constructed initially, it is created on demand by the "create_palette"
    method (when subclassed)
    '''

    def __init__(self, button, recycle):
        self._button = button
        self._recycle = recycle
        self._palette = None
        self._self_triggered = False

        self._button.connect('toggled', self.do_toggled)

    def do_toggled(self, button):
        if self._self_triggered:
            return

        if self._button.props.active:
            if self._palette is None:
                self._palette = self.create_palette()
                self._palette.connect('closed', self.__palette_closed_cb)
            self._palette.props.relative_to = button
            self._palette.show()
        else:
            self._palette.hide()
            if not self._recycle:
                self._palette = None

    def __palette_closed_cb(self, palette):
        self._self_triggered = True
        self._button.props.active = False
        self._self_triggered = False
        if not self._recycle:
            self._palette = None


def connect_palette(button, create_palette_func, recycle_palette=False):
    p = _PaletteButton(button, recycle_palette)
    p.create_palette = create_palette_func
    return p
