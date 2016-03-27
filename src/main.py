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
import sys
import json
import time
import urllib.parse
from uuid import uuid4

from gi.repository import GObject
from gi.repository import WebKit2
from gi.repository import Soup
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio

from redditisgtk.sublist import SubList
from redditisgtk.subentry import SubEntry
from redditisgtk.submit import SubmitWindow
from redditisgtk.infopopover import InfoPalette
from redditisgtk.api import get_reddit_api, is_special_sub
from redditisgtk.webviews import FullscreenableWebview, WebviewToolbar
from redditisgtk.readcontroller import get_read_controller
from redditisgtk.identity import IdentityCombo


VIEW_WEB = 0
VIEW_COMMENTS = 1


class RedditWindow(Gtk.Window):

    def __init__(self, start_sub='/r/all'):
        Gtk.Window.__init__(self, title='Reddit is Gtk+')

        self.set_default_size(600, 600)
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider.get_default()
        css_provider.load_from_resource('/today/sam/reddit-is-gtk/style.css')
        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)


        self._paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.add(self._paned)
        self._paned.show()

        # Should be a bin, but it can be a box if it wants
        self._webview_bin = Gtk.EventBox()
        self._webview = FullscreenableWebview()
        self._webview_bin.add(self._webview)
        self._webview.show()
        self._comments = None
        self._stack = Gtk.Stack()
        self._stack.connect('notify::visible-child', self.__stack_child_cb)
        self._paned.add2(self._stack)
        self._stack.show()

        self._make_header()

        self._sublist = SubList()
        self._sublist.new_other_pane.connect(self.__new_other_pane_cb)
        self._paned.add1(self._sublist)
        self._sublist.show()
        self._sublist.goto(start_sub)

        get_reddit_api().request_failed.connect(self.__request_failed_cb)

    def __request_failed_cb(self, api, msg, info):
        dialog = Gtk.Dialog(use_header_bar=True)
        label = Gtk.Label(label=info)
        dialog.get_content_area().add(label)
        label.show()

        dialog.add_button('Retry', Gtk.ResponseType.ACCEPT)
        dialog.add_button(':shrug-shoulders:', Gtk.ResponseType.REJECT)
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)

        dialog.props.transient_for = self
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            get_reddit_api().resend_message(msg)
        dialog.destroy()

    def __new_other_pane_cb(self, sublist, link, comments):
        if self._comments is not None:
            self._stack.remove(self._comments)
        self._stack.remove(self._webview_bin)

        self._comments = comments
        if self._comments is not None:
            self._stack.add_titled(self._comments, 'comments', 'Comments')
            self._stack.set_visible_child(self._comments)
            self._comments.show()

        self._stack.add_titled(self._webview_bin, 'web', 'Web')
        self._webview_bin.show()
        self._webview.show()
        if link is not None:
            self.load_uri_from_label(link)
        self._paned.position = 400  # TODO: constant

    def load_uri_from_label(self, uri):
        self._stack.set_visible_child(self._webview_bin)
        self._webview.load_uri(uri)

    def _make_header(self):
        self._header = Gtk.HeaderBar()
        self._header.props.show_close_button = True
        self.set_titlebar(self._header)
        self._header.show()

        self._identity = IdentityCombo()
        self._header.pack_start(self._identity)
        self._identity.show()

        self._submit = Gtk.Button(label='Submit')
        self._submit.connect('clicked', self.__submit_cb)
        self._header.pack_start(self._submit)
        self._submit.show()

        # TODO:  Can we have a real sidebar icon
        self._info = Gtk.Button(label='ℹ')
        self._info.connect('clicked', self.__info_cb)
        self._header.pack_start(self._info)
        self._info.show()

        self._stack_switcher = Gtk.StackSwitcher(stack=self._stack)
        self._header.pack_end(self._stack_switcher)
        self._stack_switcher.show()

        self._webview_toolbar = WebviewToolbar(self._webview)
        self._header.pack_end(self._webview_toolbar)


        self._subentry = SubEntry()
        self._subentry.activate.connect(self.__subentry_activate_cb)
        self._header.props.custom_title = self._subentry
        self._subentry.show()

    def __stack_child_cb(self, stack, pspec):
        self._webview_toolbar.props.visible = \
            stack.props.visible_child == self._webview_bin

    def __submit_cb(self, button):
        w = SubmitWindow(sub=self._sublist.get_sub_name())
        w.done.connect(self.__submit_done_cb)
        w.show()

    def __submit_done_cb(self, window, sub_name, uri):
        self._sublist.goto('/r/' + sub_name)

    def __info_cb(self, button):
        current_sub = self._sublist.get_sub_name()
        palette = InfoPalette(current_sub, relative_to=button)
        palette.show()

    def goto_sublist(self, to):
        '''
        Public api for children:
             widget.get_toplevel().goto_sublist('/u/samdroid_/overview')
        '''
        self._sublist.goto(to)
        self._subentry.props.text = to

    def __subentry_activate_cb(self, entry, sub):
        self._sublist.goto(sub)


class Application(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)
        self.connect('startup', self.__do_startup_cb)

    def do_activate(self):
        w = RedditWindow()
        self.add_window(w)
        w.show()

    # TODO:  Using do_startup causes SIGSEGV for me
    def __do_startup_cb(self, app):
        builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/app-menu.ui')
        self._menu = builder.get_object('app-menu')
        self.props.app_menu = self._menu

        # TODO, this just renders as disabled :(
        a = Gio.SimpleAction.new('app.sign-in', None)
        a.connect('activate', print)
        self.add_action(a)


def run():
    a = Application()
    status = a.run()
    get_read_controller().save()
    sys.exit(status)
