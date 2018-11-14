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
from gi.repository import Gdk

from redditisgtk.palettebutton import connect_palette
from redditisgtk.api import RedditAPI
from redditisgtk.buttons import (ScoreButtonBehaviour, AuthorButtonBehaviour,
                                 TimeButtonBehaviour, SubButtonBehaviour)
from redditisgtk.gtkutil import process_shortcuts


class PostTopBar(Gtk.Bin):

    hide_toggled = GObject.Signal('hide-toggled', arg_types=[bool])

    def __init__(self,
                 api: RedditAPI,
                 data: dict,
                 toplevel_cv,
                 hideable=True,
                 refreshable=False,
                 show_subreddit=False):
        Gtk.Bin.__init__(self, can_focus=True)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self._api = api
        self.data = data
        self._toplevel_cv = toplevel_cv

        self._b = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/post-top-bar.ui')
        self.add(self._b.get_object('box'))
        self.get_child().show()

        self.expand = self._b.get_object('expand')
        self.expand.props.visible = hideable
        self._b.get_object('refresh').props.visible = refreshable

        self._favorite = self._b.get_object('favorite')
        self._favorite.props.visible = 'saved' in self.data
        self._favorite.props.active = self.data.get('saved')

        self._name_button = self._b.get_object('name')
        self._abb = AuthorButtonBehaviour(
            self._name_button, self.data,
            self._toplevel_cv.get_original_poster(),
            show_flair=True)

        self._score_button = self._b.get_object('score')
        self._score_button.props.visible = 'score' in data
        if 'score' in data:
            self._sbb = ScoreButtonBehaviour(
                self._api, self._score_button, self.data)

        self._time_button = self._b.get_object('time')
        self._tbb = TimeButtonBehaviour(self._time_button, self.data)

        self._reply_button = self._b.get_object('reply')
        self._reply_pb = connect_palette(
            self._reply_button, self._make_reply_palette, recycle_palette=True)

        self._sub_button = self._b.get_object('sub')
        self._sub_button.props.visible = show_subreddit
        if show_subreddit:
            self._subbb = SubButtonBehaviour(self._sub_button, self.data)

        self._b.connect_signals(self)

        # We need to lazy allocate this list, otherwise we get bogus sizes
        self._hideables = None

    def do_get_request_mode(self):
        return Gtk.SizeRequestMode.HEIGHT_FOR_WIDTH

    def do_get_preferred_width(self):
        minimum, natural = Gtk.Bin.do_get_preferred_width(self)
        return 0, natural

    def do_get_preferred_height_for_width(self, width):
        # FIXME:  Worse for performance than the nested ListBoxes??
        if self._hideables is None:
            self._hideables = []
            for child in self._b.get_object('box').get_children():
                if child.props.visible:
                    minimum, natural = child.get_preferred_width()
                    self._hideables.append((child, natural))

        new_width = 0
        for b, w in self._hideables:
            new_width += w
            if new_width > width:
                b.hide()
            else:
                b.show()

        minh, nath = Gtk.Bin.do_get_preferred_height(self)
        return minh, nath

    def do_event(self, event):
        def toggle(button):
            button.props.active = not button.props.active

        def activate(button):
            button.props.active = True

        shortcuts = {
            'u': (self._sbb.vote, [+1]),
            'd': (self._sbb.vote, [-1]),
            'n': (self._sbb.vote, [0]),
            'f': (toggle, [self._favorite]),
            't': (activate, [self._time_button]),
            'a': (self.get_toplevel().goto_sublist,
                  ['/u/{}'.format(self.data['author'])]),
            's': (self.get_toplevel().goto_sublist,
                  ['/r/{}'.format(self.data['subreddit'])]),
            'r': (self.show_reply, []),
            'space': (toggle, [self.expand]),
            # The ListBoxRow usually eats these shortcuts, but we want
            # the ListBox to handle them, so we need to pass it up
            'Up': (self._toplevel_cv.do_event, [event]),
            'Down': (self._toplevel_cv.do_event, [event]),
        }
        return process_shortcuts(shortcuts, event)

    def show_reply(self):
        if self._reply_button.props.visible:
            self._reply_button.props.active = True
        else:
            self._show_reply_modal()

    def refresh_clicked_cb(self, button):
        self._toplevel_cv.refresh()

    def hide_toggled_cb(self, toggle):
        self.hide_toggled.emit(not toggle.props.active)

    def favorite_toggled_cb(self, button):
        self._api.set_saved(self.data['name'], button.props.active,
                                   None)

    def _make_reply_palette(self):
        popover = Gtk.Popover()
        contents = _ReplyPopoverContents(self._api, self.data)
        contents.posted.connect(self.__reply_posted_cb)
        popover.add(contents)
        return popover

    def _show_reply_modal(self):
        dialog = Gtk.Dialog(use_header_bar=True)
        contents = _ReplyPopoverContents(self._api, self.data,
                                         header_bar=dialog.get_header_bar())
        dialog.get_content_area().add(contents)
        contents.posted.connect(self.__reply_posted_cb)

        dialog.props.transient_for = self.get_toplevel()
        dialog.show()

    def __reply_posted_cb(self, caller, new_id):
        self._toplevel_cv.reply_posted(new_id)


class _ReplyPopoverContents(Gtk.Box):

    posted = GObject.Signal('posted', arg_types=[str])

    def __init__(self, api: RedditAPI, data, header_bar=None, **kwargs):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.data = data
        self._api = api

        sw = Gtk.ScrolledWindow()
        sw.set_size_request(500, 300)
        self.add(sw)
        self._textview = Gtk.TextView()
        self._textview.props.wrap_mode = Gtk.WrapMode.WORD
        self._textview.set_size_request(500, 300)
        self._textview.connect('event', self.__event_cb)
        sw.add(self._textview)

        self._done = Gtk.Button(label='Post Reply')
        self._done.connect('clicked', self.__done_clicked_cb)
        if header_bar is not None:
            header_bar.pack_end(self._done)
            self._done.get_style_context().add_class('suggested-action')
            self._done.show()
        else:
            self.add(self._done)

        self.show_all()

    def __event_cb(self, textview, event):
        shortcuts = {
            '<Ctrl>Return': (self.__done_clicked_cb, [None])
        }
        return process_shortcuts(shortcuts, event)

    def __done_clicked_cb(self, button):
        self._done.props.label = 'Sending...'
        self._done.props.sensitive = False
        b = self._textview.props.buffer
        text = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
        self._api.reply(self.data['name'], text, self.__reply_done_cb)

    def __reply_done_cb(self, data):
        new_id = data['json']['data']['things'][0]['data']['id']
        self.posted.emit(new_id)

        parent = self.get_parent()
        parent.hide()
        parent.destroy()
        self.destroy()
