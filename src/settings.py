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

from gi.repository import Gtk
from gi.repository import Gio


_settings = None


def get_settings():
    '''
    Returns our Gio.Settings
    '''
    global _settings
    if _settings is None:
        _settings = Gio.Settings(schema='today.sam.something-for-reddit')
    return _settings


_window = None


def show_settings():
    global _window
    if _window is not None:
        _window.show()
        return

    builder = Gtk.Builder.new_from_resource(
        '/today/sam/reddit-is-gtk/settings-window.ui')
    _window = builder.get_object('window')
    _window.show()

    def __theme_changed_cb(combo, original_value):
        builder.get_object('restart-warning').props.visible = \
            combo.props.active_id != original_value

    theme_combo = builder.get_object('theme')
    get_settings().bind('theme', theme_combo,
                        'active-id', Gio.SettingsBindFlags.DEFAULT)
    theme_combo.connect('changed', __theme_changed_cb,
                        theme_combo.props.active_id)
    get_settings().bind('default-sub', builder.get_object('default-sub'),
                        'text', Gio.SettingsBindFlags.DEFAULT)
