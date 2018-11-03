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

from gi.repository import GObject
from gi.repository import Gtk

class EmptyView(Gtk.Bin):

    action = GObject.Signal('action')

    def __init__(self, title: str, action: str = None):
        Gtk.Bin.__init__(self)

        builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/empty-view.ui')
        self._g = builder.get_object
        self.add(self._g('box'))
        self.get_child().show()

        self._g('title').props.label = title

        if action is not None:
            self._g('action').props.label = action
            self._g('action').props.visible = True
            self._g('action').connect('clicked', self.__action_clicked_cb)

    def __action_clicked_cb(self, button):
        self.action.emit()
