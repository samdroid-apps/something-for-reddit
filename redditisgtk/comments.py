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

import os
import time
import cProfile

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from redditisgtk import newmarkdown
from redditisgtk.palettebutton import connect_palette
from redditisgtk.api import RedditAPI
from redditisgtk.buttons import (ScoreButtonBehaviour, AuthorButtonBehaviour,
                                 TimeButtonBehaviour, SubButtonBehaviour)
from redditisgtk.gtkutil import process_shortcuts
from redditisgtk import emptyview


ENABLE_PROFILE = 'COMMENTS_PROFILE' in os.environ

if ENABLE_PROFILE:  # pragma: no cover
    profile = cProfile.Profile()
    profile.done = True
    profile.start = 0


class CommentsView(Gtk.ScrolledWindow):
    '''Downloads comments, shows selftext'''

    got_post_data = GObject.Signal('got-post-data', arg_types=[object])

    def __init__(self, api: RedditAPI, post=None, comments=None, permalink=None):
        Gtk.ScrolledWindow.__init__(self)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.get_style_context().add_class('root-comments-view')
        self.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        self._api = api
        self._post = post
        self._msg = None

        self._permalink = permalink
        if post is not None and permalink is None:
            self._permalink = post['permalink']
        if self._permalink is None:
            raise Exception('We have no link for a post!')

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._box)
        self._box.show()

        self._spinner = Gtk.Spinner()
        self._box.pack_end(self._spinner, True, True, 0)
        self._spinner.show()

        if self._post is not None:
            self._init_post(self._post)

        if comments is not None:
            self.__message_done_cb(comments)
        else:
            self.refresh()

    def _init_post(self, post):
        self.got_post_data.emit(post)

        self._top = _PostTopBar(self._api, post, self, hideable=False,
                                refreshable=True, show_subreddit=True)
        self._top.get_style_context().add_class('root-comments-bar')
        self._box.add(self._top)
        self._top.show()

        body = '# ' + post['title']
        if post.get('selftext'):
            bost = body + '\n' + post['selftext']

        selfpost_label = newmarkdown.make_markdown_widget(body)
        selfpost_label.get_style_context().add_class('root-comments-label')
        self._box.add(selfpost_label)
        selfpost_label.show()

        self._comments = None
        self._load_full = None
        self._selected = self._top

    def focus(self):
        self._selected.grab_focus()

    def get_link_name(self):
        return self._post['name']

    def get_header_height(self):
        return self._comments.get_allocation().y

    def refresh(self, caller=None):
        self._spinner.start()
        self._msg = self._api.send_request(
            'GET', self._permalink, self.__message_done_cb)

    def do_unrealize(self):
        if self._msg is not None:
            self._api.cancel(self._msg)

    def __message_done_cb(self, j):
        self._spinner.stop()
        if self._post is None:
            self._post = j[0]['data']['children'][0]['data']
            self._init_post(self._post)

        self._msg = None
        self._selected = self._top

        if self._load_full is not None:
            self._load_full.hide()
            self._load_full.destroy()
            self._load_full = None

        permalink_segments = len(self._permalink.rstrip('/').split('/'))
        # More than /r/rct/comments/4ns96b/new_to_rct_lovely_community_3/
        if permalink_segments > 6:
            self._load_full = LoadFullCommentsRow()
            self._load_full.load_full.connect(self.__load_full_cb)
            self._box.add(self._load_full)
            self._load_full.show()

        if self._comments is not None:
            self._box.remove(self._comments)
            self._comments.destroy()

        if len(j[1]['data']['children']) == 0:
            self._comments = emptyview.EmptyView(
                'No Comments', action='Add a comment')
            self._comments.action.connect(self.__add_comment_clicked_cb)
        else:
            if ENABLE_PROFILE:  # pragma: no cover
                print('[COMMENTS PROFILE] Start')
                profile.enable()
                profile.done = False
                profile.start = time.time()

            # The 0th one is just the self post
            self._comments = _CommentsView(
                    self._api, j[1]['data']['children'],
                    self, first=True)

        self._box.add(self._comments)
        self._comments.show()

    def __add_comment_clicked_cb(self, view):
        self._top.show_reply()

    def __load_full_cb(self, row):
        # First 6 = /r/rct/comments/4ns96b/new_to_rct_lovely_community_3/
        self._permalink = '/'.join(self._permalink.split('/')[:6])
        self.refresh()

    def reply_posted(self, new_id):
        # First 6 = /r/rct/comments/4ns96b/new_to_rct_lovely_community_3/
        parts = self._permalink.split('/')[:6]
        parts.append(new_id)
        self._permalink = '/'.join(parts)
        self.refresh()

    def get_original_poster(self):
        return self._post['author']

    def _get_next_row(self, relative_to):
        if relative_to == self._top:
            return self._load_full or self._comments.get_children()[0]
        if relative_to == self._load_full:
            return self._comments.get_children()[0]

        row = relative_to
        # 1st, try to see if I have a child to descend into
        if isinstance(row, CommentRow) and row.get_sub() is not None:
            child = row.get_sub().get_children()[0]
            if child.get_mapped():
                return child

        # 2nd, try siblings and parents iteratively
        while isinstance(row, CommentRow):
            parent_listview = row.get_parent()
            kids = parent_listview.get_children()
            i = kids.index(row)
            if i+1 < len(kids) and kids[i+1].get_mapped():
                return kids[i+1]
            else:
                # Walk up to next CommentRow
                row = row.get_parent()
                while not isinstance(row, CommentRow):
                    row = row.get_parent()
        return None

    def _get_last_child_of(self, row):
        if row.get_sub() is not None:
            child = row.get_sub().get_children()[-1]
            if child.get_mapped():
                return self._get_last_child_of(child)
        return row

    def _get_prev_row(self, row):
        if self._load_full is not None and row == self._load_full:
            return self._top

        if row == self._top:
            return None

        assert isinstance(row, CommentRow)
        # Find the row before me
        if isinstance(row, CommentRow):
            parent_listview = row.get_parent()
            kids = parent_listview.get_children()
            i = kids.index(row)
            if i == 0:
                # Return parent is there is no row before us
                if row.depth == 0:
                    return self._load_full or self._top

                # Walk up to next CommentRow
                row = row.get_parent()
                while not isinstance(row, CommentRow):
                    row = row.get_parent()
                return row
            else:
                return self._get_last_child_of(kids[i-1])
        return None

    def do_event(self, event):
        def move(direction, jump):
            if jump:
                row = self._selected
                while isinstance(row, CommentRow) and row.depth > 0:
                    # Walk up to next CommentRow
                    row = row.get_parent()
                    while not isinstance(row, CommentRow):
                        row = row.get_parent()
                kids = [self._top] + self._comments.get_children()
                i = kids.index(row)
                if 0 <= i + direction < len(kids):
                    row = kids[i + direction]
            else:
                f = self._get_next_row if direction > 0 else self._get_prev_row
                while True:
                    row = f(self._selected)
                    if row is None or row.get_mapped():
                        break

            if row is not None:
                row.grab_focus()
                self._selected = row
            else:
                # We went too far!
                self.error_bell()
                self._selected.get_style_context().remove_class('angry')
                self._selected.get_style_context().add_class('angry')
                GLib.timeout_add(
                    500,
                    self._selected.get_style_context().remove_class,
                    'angry')

        def load_full():
            if self._load_full is not None:
                self.__load_full_cb(None)

        shortcuts = {
            'k': (move, [-1, False]),
            'j': (move, [+1, False]),
            'Up': (move, [-1, False]),
            'Down': (move, [+1, False]),
            'h': (move, [-1, True]),
            'l': (move, [+1, True]),
            'Left': (move, [-1, True]),
            'Right': (move, [+1, True]),
            '<ctrl>f': (load_full, []),
            '<ctrl>r': (self.refresh, []),
        }
        return process_shortcuts(shortcuts, event)


class _CommentsView(Gtk.ListBox):
    '''
    Actually holds the comments

    This is recursive, eg, like:

    _CommentsView
        | CommentRow
        |   | _CommentsView
        |   |   | CommentRow
        | CommentRow
    '''

    def __init__(self, api: RedditAPI, data, toplevel_cv, first=False, depth=0):
        Gtk.ListBox.__init__(self)
        self._api = api
        self._first_row = None
        self._is_first = first
        self._depth = depth
        self._toplevel_cv = toplevel_cv

        ctx = self.get_style_context()
        ctx.add_class('comments-view')
        if self._is_first:
            ctx.add_class('first')
        ctx.add_class('depth-{}'.format(depth % 5))
        self._add_comments(data)

        if first and ENABLE_PROFILE:  # pragma: no cover
            self.connect_after('draw', self.__draw_cb)

    def __draw_cb(self, widget, cr):
        if not profile.done:
            profile.done = True
            profile.disable()
            profile.print_stats(sort='tottime')
            print('[COMMENTS PROFILE] Done', time.time() - profile.start)

    def _add_comments(self, data):
        index = 0
        def do_add_comment():
            nonlocal index

            if index >= len(data):
                return

            comment_data = data[index]['data']
            row = CommentRow(self._api, comment_data, self._depth, self._toplevel_cv)
            row.recurse()
            row.got_more_comments.connect(self.__got_more_comments_cb)
            self.insert(row, -1)
            row.show()

            index += 1
            if index < len(data):
                GLib.idle_add(do_add_comment)

        do_add_comment()

    def do_row_activated(self, row):
        if self._is_first:
            viewport = self.get_parent().get_parent()
            comments_view = viewport.get_parent()
            # Stop the kinetic scroll, otherwise it will override our
            # scrolling adjustment
            comments_view.props.kinetic_scrolling = False

            # Scroll to the top of the collapsed row
            r = row.get_allocation()
            header = comments_view.get_header_height()
            adj = viewport.get_vadjustment()
            adj.props.value = r.y + header

            comments_view.props.kinetic_scrolling = True

            row.do_activated()

    def __got_more_comments_cb(self, caller_button, more_comments):
        caller_button.hide()
        self.remove(caller_button)
        caller_button.destroy()

        self._add_comments(more_comments)


class LoadFullCommentsRow(Gtk.ListBoxRow):

    load_full = GObject.Signal('load_full')

    def __init__(self):
        Gtk.ListBoxRow.__init__(self)

        self._ib = Gtk.InfoBar(message_type=Gtk.MessageType.QUESTION)
        self._ib.connect('response', self.__response_cb)
        self.add(self._ib)
        self._ib.show()

        label = Gtk.Label(label='Showing only a subset of comments')
        self._ib.get_content_area().add(label)
        label.show()

        self._button = self._ib.add_button('Show All Comments', 1)

    def grab_focus(self):
        self._button.grab_focus()

    def __response_cb(self, ib, response):
        self.load_full.emit()
        self._button.props.label = 'Loading...'


class _PostTopBar(Gtk.Bin):

    hide_toggled = GObject.Signal('hide-toggled', arg_types=[bool])

    def __init__(self, api: RedditAPI, data, toplevel_cv, hideable=True,
                 refreshable=False, show_subreddit=False):
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

    def read_toggled_cb(self, toggle):
        if toggle.props.active:
            self._api.read_message(self.data['name'])
            self._read.get_style_context().remove_class('unread')
            self._read.props.active = True
            self._read.props.sensitive = False
            self._read.props.label = 'Read'

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


class CommentRow(Gtk.ListBoxRow):

    refresh = GObject.Signal('refresh')
    got_more_comments = GObject.Signal('got-more-comments', arg_types=[object])

    def __init__(self, api: RedditAPI, data, depth, toplevel_cv):
        Gtk.ListBoxRow.__init__(self, selectable=False)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self._api = api
        self.data = data
        self.depth = depth
        self._toplevel_cv = toplevel_cv
        self._top = None
        self._sub = None
        self._more_button = None

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._box)
        self._box.show()

    def get_sub(self):
        return self._sub

    def recurse(self):
        if 'body' in self.data:
            self._show_normal_comment()
        else:
            self._more_button = Gtk.Button.new_with_label(
                'Show {} more comments...'.format(self.data['count']))
            self._more_button.connect('clicked', self.__load_more_cb)
            self._more_button.get_style_context().add_class('load-more')
            self._box.add(self._more_button)
            self._more_button.show()

    def do_focus_in_event(self, event):
        if self._more_button is not None:
            self._more_button.grab_focus()

    def do_event(self, event):
        if self._top is not None:
            return self._top.do_event(event)

    def __load_more_cb(self, button):
        button.props.sensitive = False
        self._api.load_more(
            self._toplevel_cv.get_link_name(),
            self.data, self.__loaded_more_cb)

    def __loaded_more_cb(self, comments):
        self.got_more_comments.emit(comments)

    def _show_normal_comment(self):
        self._top = _PostTopBar(self._api, self.data, self._toplevel_cv)
        self._top.hide_toggled.connect(self.__hide_toggled_cb)
        self._box.add(self._top)
        self._top.show()

        self._label = newmarkdown.make_html_widget(self.data['body_html'])
        self._box.add(self._label)
        self._label.show()

        self._sub = None
        self._revealer = None
        if self.data.get('replies'):
            self._revealer = Gtk.Revealer(
                transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
                reveal_child=True
            )
            self._box.add(self._revealer)
            self._revealer.show()

            self._sub = _CommentsView(
                self._api,
                self.data['replies']['data']['children'],
                self._toplevel_cv,
                depth=self.depth + 1)
            self._revealer.add(self._sub)
            self._sub.show()
        else:
            self._top.expand.hide()

    def __hide_toggled_cb(self, top, hidden):
        if self._revealer is not None:
            self._revealer.props.reveal_child = hidden

    def do_activated(self):
        if self._revealer is not None:
            rc = not self._revealer.props.reveal_child
            self._revealer.props.reveal_child = rc
            self._top.expand.props.active = not rc
