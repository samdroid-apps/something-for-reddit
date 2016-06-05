# Copyright 2016 Sam Parkinson <sam@sam.today>
#
# This file is part of Reddit is Gtk+.
#
# Reddit is Gtk+ is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Reddit is Gtk+ is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Reddit is Gtk+.  If not, see <http://www.gnu.org/licenses/>.

import os
from gi.repository import GLib
from gi.repository import GObject


def get_data_file_path(name):
    '''
    Returns the path for storing user data.

    Makes the directory if it does not exist currently.  Does not check
    if the file exists.

    Args:
        name (str)
    '''
    d = os.path.expanduser('~/.local/share/reddit-is-gtk')
    if not os.path.isdir(d):
        os.makedirs(d)
    return os.path.join(d, name)


class ReadController(GObject.GObject):

    def __init__(self):
        GObject.GObject.__init__(self)
        self._set = set([])
        self.load()

    def read(self, name):
        self._set.add(name)
        GLib.idle_add(self.save)

    def is_read(self, name):
        return name in self._set

    def save(self):
        with open(get_data_file_path('read'), 'w') as f:
            for i in self._set:
                f.write(i)
                f.write('\n')

    def load(self):
        if os.path.isfile(get_data_file_path('read')):
            with open(get_data_file_path('read')) as f:
                l = 0
                for i in f:
                    self._set.add(i.strip())
                    l += 1


_ctrl = None


def get_read_controller():
    global _ctrl
    if _ctrl is None:
        _ctrl = ReadController()
    return _ctrl
