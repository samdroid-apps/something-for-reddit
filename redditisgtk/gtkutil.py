# Copyright 2018 Sam Parkinson <sam@sam.today>
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

from gi.repository import Gtk
from gi.repository import Gdk


def process_shortcuts(shortcuts, event: Gdk.Event):
    '''
    Shortcuts is a dict of:
        accelerator string: (self._function, [arguments])

    Accelerator is passed to Gtk.accelerator_parse
    Event is the GdkEvent
    '''
    if event.type != Gdk.EventType.KEY_PRESS:
        return
    for accel_string, value in shortcuts.items():
        key, mods = Gtk.accelerator_parse(accel_string)
        emods = event.state & (Gdk.ModifierType.CONTROL_MASK |
                               Gdk.ModifierType.SHIFT_MASK)

        if event.keyval == key and (emods & mods or mods == emods == 0):
            func, args = value
            try:
                func(*args)
            except Exception as e:
                print(e)
                return False
            return True
