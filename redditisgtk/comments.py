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
from redditisgtk import posttopbar


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

        self._top = posttopbar.PostTopBar(
            self._api, post, self, hideable=False,
            refreshable=True, show_subreddit=True)
        self._top.get_style_context().add_class('root-comments-bar')
        self._box.add(self._top)
        self._top.show()

        body = '# ' + post['title']
        if post.get('selftext'):
            body = body + '\n\n' + post['selftext']

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

    def get_next_row(self, relative_to):
        if relative_to == self._top:
            return self._load_full or self._comments.get_children()[0]
        if relative_to == self._load_full:
            return self._comments.get_children()[0]

        row = relative_to
        # 1st, try to see if I have a child to descend into
        if isinstance(row, CommentRow) and row.get_sub() is not None:
            children  = row.get_sub().get_children()
            if len(children) >= 1 and children[0].get_mapped():
                return children[0]

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
            children = row.get_sub().get_children()
            if len(children) >= 1 and children[-1].get_mapped():
                return self._get_last_child_of(children[-1])
        return row

    def get_prev_row(self, row):
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
                f = self.get_next_row if direction > 0 else self.get_prev_row
                while True:
                    row = f(self._selected)
                    if row is None or row.get_mapped():
                        break

            if row is not None:
                self.select_row(row)
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

    def select_row(self, row):
        row.grab_focus()
        self._selected = row


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
        '''
        Add comments from the given data list

        Returns the widget for the first comment added
        '''
        index = 0
        def do_add_comment():
            nonlocal index

            if index >= len(data):
                return

            comment_data = data[index]['data']
            if 'body' in comment_data:
                row = NormalCommentRow(self._api, comment_data, self._depth, self._toplevel_cv)
            else:
                row = LoadMoreCommentsRow(self._api, comment_data, self._depth, self._toplevel_cv)
                row.got_more_comments.connect(self.__got_more_comments_cb)
            row.recurse()
            self.insert(row, -1)
            row.show()

            if self._first_row is None:
                self._first_row = row

            index += 1
            if index < len(data):
                GLib.idle_add(do_add_comment)

            return row

        return do_add_comment()

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

    def __got_more_comments_cb(self, caller_row, more_comments):
        row = self._add_comments(more_comments)
        if row is None:
            # If no comments were added, just select the previous row
            row = self._toplevel_cv.get_prev_row(caller_row)

        if row is not None:
            self._toplevel_cv.select_row(row)

        caller_row.hide()
        self.remove(caller_row)
        caller_row.destroy()


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


class CommentRow(Gtk.ListBoxRow):
    def __init__(self, data, depth):
        Gtk.ListBoxRow.__init__(self, selectable=False)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)

        self.data = data
        self.depth = depth

    def get_sub(self):
        return None


class NormalCommentRow(CommentRow):

    refresh = GObject.Signal('refresh')

    def __init__(self, api: RedditAPI, data, depth, toplevel_cv):
        super().__init__(data, depth)
        self._api = api
        self._toplevel_cv = toplevel_cv
        self._top = None
        self._sub = None

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._box)
        self._box.show()

    def get_sub(self):
        return self._sub

    def do_event(self, event):
        if self._top is not None:
            return self._top.do_event(event)

    def recurse(self):
        self._top = posttopbar.PostTopBar(
            self._api, self.data, self._toplevel_cv)
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


class LoadMoreCommentsRow(CommentRow):

    got_more_comments = GObject.Signal('got-more-comments', arg_types=[object])

    def __init__(self, api: RedditAPI, data, depth, toplevel_cv):
        super().__init__(data, depth)

        self._api = api
        self._toplevel_cv = toplevel_cv
        self._more_button = None

    def recurse(self):
        self._more_button = Gtk.Button.new_with_label(
            'Show {} more comments...'.format(self.data['count']))
        self._more_button.connect('clicked', self.__load_more_cb)
        self._more_button.get_style_context().add_class('load-more')
        self.add(self._more_button)
        self._more_button.show()

    def do_focus_in_event(self, event):
        if self._more_button is not None:
            self._more_button.grab_focus()

    def __load_more_cb(self, button):
        button.props.sensitive = False
        self._api.load_more(
            self._toplevel_cv.get_link_name(),
            self.data, self.__loaded_more_cb)

    def __loaded_more_cb(self, comments):
        self.got_more_comments.emit(comments)
