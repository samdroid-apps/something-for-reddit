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

import re
import sys
from argparse import ArgumentParser

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib

from redditisgtk.sublist import SubList
from redditisgtk.subentry import SubEntry
from redditisgtk.api import get_reddit_api
from redditisgtk.webviews import (FullscreenableWebview, ProgressContainer,
                                  WebviewToolbar)
from redditisgtk.readcontroller import get_read_controller
from redditisgtk.identity import IdentityButton
from redditisgtk.comments import CommentsView
from redditisgtk.settings import get_settings, show_settings


VIEW_WEB = 0
VIEW_COMMENTS = 1


class RedditWindow(Gtk.Window):

    def __init__(self, start_sub=None):
        Gtk.Window.__init__(self, title='Something For Reddit',
                            icon_name='reddit-is-a-dead-bird')
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.set_default_size(600, 600)
        self.set_wmclass("reddit-is-gtk", "Something For Reddit")

        settings = Gtk.Settings.get_default()
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider.get_default()
        if settings.props.gtk_application_prefer_dark_theme:
            css_provider.load_from_resource(
                '/today/sam/reddit-is-gtk/style.dark.css')
        else:
            css_provider.load_from_resource(
                '/today/sam/reddit-is-gtk/style.css')
        context = Gtk.StyleContext()
        context.add_provider_for_screen(screen, css_provider,
                                        Gtk.STYLE_PROVIDER_PRIORITY_USER)

        self._paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.add(self._paned)
        self._paned.show()

        self._webview = FullscreenableWebview()
        self._webview_bin = ProgressContainer(self._webview)
        self._comments = None
        self._stack = Gtk.Stack()
        self._stack.connect('notify::visible-child', self.__stack_child_cb)
        self._paned.add2(self._stack)
        #self._paned.child_set_property(self._stack, 'shrink', True)
        self._stack.show()

        if start_sub is None:
            start_sub = get_settings()['default-sub']
        self._sublist = SubList()
        self._sublist.new_other_pane.connect(self.__new_other_pane_cb)
        self._paned.add1(self._sublist)
        #self._paned.child_set_property(self._sublist, 'shrink', True)
        self._sublist.show()
        self._sublist.goto(start_sub)

        self._make_header(start_sub)
        left = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        left.add_widget(self._left_header)
        left.add_widget(self._sublist)
        self._paned.connect('notify::position',
                            self.__notify_position_cb,
                            self._header_paned)
        self._header_paned.connect('notify::position',
                                   self.__notify_position_cb,
                                   self._paned)

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

    def do_event(self, event):
        if event.type != Gdk.EventType.KEY_PRESS:
            return
        if isinstance(self.get_focus(), (Gtk.TextView, Gtk.Entry)):
            return

        if event.keyval == Gdk.KEY_F6:
            self._subentry.focus()
            return True
        if event.keyval == Gdk.KEY_1:
            self._sublist.focus()
            return True
        if event.keyval == Gdk.KEY_2:
            self._stack.set_visible_child(self._comments)
            self._comments.focus()
            return True
        if event.keyval == Gdk.KEY_3:
            self._stack.set_visible_child(self._webview_bin)
            self._webview.grab_focus()
            return True

        if event.state & Gdk.ModifierType.MOD1_MASK:
            if event.keyval == Gdk.KEY_Left:
                self._webview.go_back()
                return True
            if event.keyval == Gdk.KEY_Right:
                self._webview.go_forward()
                return True

    def __new_other_pane_cb(self, sublist, link, comments, link_first):
        if self._comments is not None:
            self._stack.remove(self._comments)
        self._stack.remove(self._webview_bin)

        self._comments = comments
        if self._comments is not None:
            self._stack.add_titled(self._comments, 'comments', 'Comments')
            self._comments.show()

        self._stack.add_titled(self._webview_bin, 'web', 'Web')
        self._webview_bin.show()
        self._webview.show()
        self._paned.position = 400  # TODO: constant

        if link_first and link:
            self._stack.set_visible_child(self._webview_bin)
            self._webview.load_uri(link)
        else:
            self._stack.set_visible_child(self._comments)
            if link is not None:
                self._webview.load_when_visible(link)


    def load_uri_from_label(self, uri):
        if re.match('https?:\/\/(www\.|np\.)?reddit\.com\/', uri):
            self.goto_reddit_uri(uri)
            return
        self._stack.set_visible_child(self._webview_bin)
        self._webview.load_uri(uri)

    def __notify_position_cb(self, caller, pspec, other):
        other.props.position = caller.props.position

    def _make_header(self, start_sub):
        self._header_paned = Gtk.Paned()
        self.set_titlebar(self._header_paned)

        self._left_header = Gtk.HeaderBar()
        layout = Gtk.Settings.get_default().props.gtk_decoration_layout
        self._left_header.set_decoration_layout(layout.split(':')[0])

        self._right_header = Gtk.HeaderBar()
        self._right_header.set_decoration_layout(':'+layout.split(':')[1])
        self._right_header.props.show_close_button = True

        self._subentry = SubEntry(start_sub)
        self._subentry.activate.connect(self.__subentry_activate_cb)
        self._subentry.escape_me.connect(self.__subentry_escape_me_cb)
        self._left_header.props.custom_title = self._subentry
        self._subentry.show()

        self._header_paned.add1(self._left_header)
        self._header_paned.add2(self._right_header)
        self._header_paned.show_all()

        self._identity = IdentityButton()
        self._right_header.pack_start(self._identity)
        self._identity.show()

        self._stack_switcher = Gtk.StackSwitcher(stack=self._stack)
        self._right_header.pack_end(self._stack_switcher)
        self._stack_switcher.show()

        self._webview_toolbar = WebviewToolbar(self._webview)
        self._right_header.pack_end(self._webview_toolbar)

    def __stack_child_cb(self, stack, pspec):
        self._webview_toolbar.props.visible = \
            stack.props.visible_child == self._webview_bin

    def get_sublist(self):
        return self._sublist

    def get_comments_view(self):
        return self._comments

    def goto_sublist(self, to):
        '''
        Public api for children:
             widget.get_toplevel().goto_sublist('/u/samdroid_/overview')
        '''
        self._sublist.goto(to)
        self._subentry.goto(to)

    def goto_reddit_uri(self, uri):
        '''
        Go to a reddit.com uri, eg. "https://www.reddit.com/r/rct"
        '''
        for cond in ['https://', 'http://', 'www.', 'np.', 'reddit.com']:
            if uri.startswith(cond):
                uri = uri[len(cond):]

        # Disregard the '' before the leading /
        parts = uri.split('/')[1:]
        if len(parts) <= 3:
            # /u/*/*, /r/*, /r/*/*(sorting)
            self.goto_sublist(uri)
        if parts[2] == 'comments':
            self.goto_sublist('/r/{}/'.format(parts[1]))
            cv = CommentsView(permalink=uri)
            cv.got_post_data.connect(self.__cv_got_post_data_cb)
            self.__new_other_pane_cb(None, None, cv, False)

    def __cv_got_post_data_cb(self, cv, post):
        if not post.get('is_self') and 'url' in post:
            self.__new_other_pane_cb(None, post['url'], cv, True)

    def __subentry_activate_cb(self, entry, sub):
        self._sublist.goto(sub)
        self._sublist.focus()

    def __subentry_escape_me_cb(self, entry):
        self._sublist.focus()


class Application(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id='today.sam.reddit-is-gtk')
        self.connect('startup', self.__do_startup_cb)
        GLib.set_application_name("Something For Reddit")
        GLib.set_prgname("reddit-is-gtk")
        self._w = None
        self._queue_uri = None

    def do_activate(self):
        self._w = RedditWindow()
        self.add_window(self._w)
        self._w.show()
        if self._queue_uri is not None:
            self._w.goto_reddit_uri(self._queue_uri)
            self._queue_uri = None

    def goto_reddit_uri(self, uri):
        if self._w is None:
            self._queue_uri = uri
        else:
            self._w.goto_reddit_uri(uri)

    # TODO:  Using do_startup causes SIGSEGV for me
    def __do_startup_cb(self, app):
        actions = [('about', self.__about_cb), ('quit', self.__quit_cb),
                   ('shortcuts', self.__shortcuts_cb),
                   ('settings', self.__settings_cb)]
        for name, cb in actions:
            a = Gio.SimpleAction.new(name, None)
            a.connect('activate', cb)
            self.add_action(a)

        builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/app-menu.ui')
        self._menu = builder.get_object('app-menu')
        self.props.app_menu = self._menu

    def __about_cb(self, action, param):
        about_dialog = Gtk.AboutDialog(
            program_name='Something for Reddit',
            comments=('A simple but powerful Reddit client, built for KDE and'
                      'powered by Qt5'),
            license_type=Gtk.License.GPL_3_0,
            logo_icon_name='reddit-is-a-dead-bird',
            authors=['Sam P. <sam@sam.today>'],
            website='https://github.com/samdroid-apps/something-for-reddit',
            website_label='Git Repo and Issue Tracker on GitHub',
            version='0.2',
            transient_for=self._w,
            modal=True)
        about_dialog.present()

    def __quit_cb(self, action, param):
        self.quit()

    def __shortcuts_cb(self, action, param):
        builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/shortcuts-window.ui')
        builder.get_object('window').show()

    def __settings_cb(self, action, param):
        show_settings()


def run():
    parser = ArgumentParser(
        description='Something For Reddit - a Gtk+ Reddit Client')
    parser.add_argument('uri', help='Reddit.com URI to open, or None',
                        default=None, nargs='?')
    parser.add_argument('--dark', help='Force Gtk+ dark theme',
                        action='store_true')
    args = parser.parse_args()

    settings = Gtk.Settings.get_default()
    theme = get_settings()['theme']
    if theme == 'dark':
        settings.props.gtk_application_prefer_dark_theme = True
    elif theme == 'light':
        settings.props.gtk_application_prefer_dark_theme = False

    if args.dark:
        settings.props.gtk_application_prefer_dark_theme = True

    a = Application()
    if args.uri is not None:
        a.goto_reddit_uri(args.uri)
    status = a.run()
    get_read_controller().save()
    sys.exit(status)
