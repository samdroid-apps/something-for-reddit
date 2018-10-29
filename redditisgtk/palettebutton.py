# Copyright 2016 Sam Parkinson <sam@sam.today>
#
# This file is part of Something for Reddit.
#
# Something for Reddit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Something for Reddit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Something for Reddit.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import GObject
from gi.repository import Gtk


class _PaletteButton(GObject.GObject):
    '''
    Like a Gtk.MenuButton, but instead of requiring the palette to be
    constructed initially, it is created on demand by the "create_palette"
    method (when subclassed)
    '''

    def __init__(self, button, recycle, modalify):
        self._button = button
        self._recycle = recycle
        self._modalify = modalify
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
                self._pc = self._palette.get_child()

            if not self._button.props.visible and self._modalify:
                dialog = Gtk.Dialog(use_header_bar=True)
                self._palette.remove(self._pc)
                dialog.get_content_area().add(self._pc)

                dialog.props.transient_for = self._button.get_toplevel()
                dialog.connect('response', self.__dialog_closed_cb)
                dialog.show()
            else:
                self._palette.props.relative_to = button
                self._palette.show()
        else:
            self._palette.hide()
            if not self._recycle:
                self._palette = None

    def __dialog_closed_cb(self, dialog, response):
        dialog.get_content_area().remove(self._pc)
        self._palette.add(self._pc)

        self.__palette_closed_cb(None)

    def __palette_closed_cb(self, palette):
        self._self_triggered = True
        self._button.props.active = False
        self._self_triggered = False
        if not self._recycle:
            self._palette = None


def connect_palette(button, create_palette_func, recycle_palette=False,
                    modalify=False):
    p = _PaletteButton(button, recycle_palette, modalify)
    p.create_palette = create_palette_func
    return p
