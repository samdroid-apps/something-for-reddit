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


import subprocess
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import WebKit2

class FullscreenableWebview(WebKit2.WebView):
    def do_enter_fullscreen(self):
        self._old_parent = self.get_parent()
        self._old_parent.remove(self)

        self._fullscreen = Gtk.Window()
        self._fullscreen.add(self)
        self._fullscreen.show()

    def do_leave_fullscreen(self):
        self._fullscreen.remove(self)
        self._old_parent.add(self)
        del self._old_parent

        self._fullscreen.destroy()
        del self._fullscreen


class ProgressContainer(Gtk.Overlay):
    '''
    Overlays a progress bar on a webview passed to the constructor
    '''
    def __init__(self, webview):
        Gtk.Overlay.__init__(self)
        self._webview = webview
        self.add(self._webview)
        self._webview.show()

        self._progress = Gtk.ProgressBar(halign=Gtk.Align.FILL,
                                         valign=Gtk.Align.START)
        self.add_overlay(self._progress)

        self._webview.connect('notify::estimated-load-progress',
                              self.__notify_progress_cb)

    def __notify_progress_cb(self, webview, pspec):
        progress = webview.props.estimated_load_progress
        if progress == 1.0:
            self._progress.hide()
        else:
            self._progress.show()
            self._progress.set_fraction(progress)


class WebviewToolbar(Gtk.Bin):
    def __init__(self, webview):
        Gtk.Bin.__init__(self)
        self._webview = webview
        self._b = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/webview-toolbar.ui')
        self.add(self._b.get_object('toolbar'))
        self._b.get_object('toolbar').show_all()

        self._b.get_object('back').connect(
            'clicked', self.__clicked_cb, webview.go_back)
        self._b.get_object('forward').connect(
            'clicked', self.__clicked_cb, webview.go_forward)
        self._b.get_object('external').connect('clicked', self.__external_cb)

        webview.connect('load-changed', self.__load_changed_cb)

    def __load_changed_cb(self, webview, load_event):
        self._b.get_object('back').props.sensitive = \
            self._webview.can_go_back()
        self._b.get_object('forward').props.sensitive = \
            self._webview.can_go_forward()

    def __external_cb(self, button):
        uri = self._webview.props.uri
        subprocess.call(['xdg-open', uri])

    def __clicked_cb(self, button, func):
        func()
