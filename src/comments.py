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

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from redditisgtk.markdownpango import markdown_to_pango, SaneLabel
from redditisgtk.palettebutton import connect_palette
from redditisgtk.api import get_reddit_api
from redditisgtk.buttons import (ScoreButtonBehaviour, AuthorButtonBehaviour,
                                 TimeButtonBehaviour, SubButtonBehaviour,
                                 process_shortcuts)


class CommentsView(Gtk.ScrolledWindow):
    '''Downloads comments, shows selftext'''

    got_post_data = GObject.Signal('got-post-data', arg_types=[object])

    def __init__(self, post=None, comments=None, permalink=None):
        Gtk.ScrolledWindow.__init__(self)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.get_style_context().add_class('root-comments-view')
        self.props.hscrollbar_policy = Gtk.PolicyType.NEVER
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

        self._top = _PostTopBar(post, self, hideable=False,
                                refreshable=True, show_subreddit=True)
        self._top.get_style_context().add_class('root-comments-bar')
        self._box.add(self._top)
        self._top.show()

        selfpost_label = SaneLabel(
            '<big>{title}</big>\n'
            '{selftext_pango}'.format(
                selftext_pango=markdown_to_pango(post.get('selftext')),
                title=post['title']))
        selfpost_label.get_style_context().add_class('root-comments-label')
        self._box.add(selfpost_label)
        selfpost_label.show()

        self._comments = None
        self._load_full = None
        self._all_comments = [self._top]
        self._selected = self._top

    def focus(self):
        self._selected.grab_focus()

    def get_link_name(self):
        return self._post['name']

    def get_header_height(self):
        return self._comments.get_allocation().y

    def refresh(self, caller=None):
        self._spinner.start()
        self._msg = get_reddit_api().send_request(
            'GET', self._permalink, self.__message_done_cb)

    def do_unrealize(self):
        if self._msg is not None:
            get_reddit_api().cancel(self._msg)

    def __message_done_cb(self, j):
        self._spinner.stop()
        if self._post is None:
            self._post = j[0]['data']['children'][0]['data']
            self._init_post(self._post)

        self._msg = None
        self._all_comments = [self._top]
        self._selected = self._top

        if self._load_full is not None:
            self._load_full.hide()
            self._load_full.destroy()
        permalink_segments = len(self._permalink.rstrip('/').split('/'))
        # More than /r/rct/comments/4ns96b/new_to_rct_lovely_community_3/
        if permalink_segments > 6:
            self._load_full = LoadFullCommentsRow()
            self._load_full.load_full.connect(self.__load_full_cb)
            self._box.add(self._load_full)
            self._all_comments.append(self._load_full)
            self._load_full.show()
        elif self._load_full is not None:
            self._box.remove(self._load_full)
            self._load_full.destroy()

        if self._comments is not None:
            self._box.remove(self._comments)
            self._comments.hide()
            self._comments.destroy()

        # The 0th one is just the self post
        self._comments = _CommentsView(j[1]['data']['children'],
                                       self,
                                       first=True)
        self._box.add(self._comments)
        self._comments.show()

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

    def added_comment_row(self, row):
        self._all_comments.append(row)

    def do_event(self, event):
        def move(direction, jump):
            if jump:
                row = self._selected
                while isinstance(row, CommentRow) and row.depth > 0:
                    # FIXME:  This must be bad
                    # Me > List > Box > Revealer > Box > Next Row!!
                    row = row.get_parent().get_parent().get_parent() \
                             .get_parent().get_parent()
                kids = [self._top] + self._comments.get_children()
                i = kids.index(row)
                if 0 <= i + direction < len(kids):
                    row = kids[i + direction]
            else:
                i = self._all_comments.index(self._selected)
                row = None
                while 0 <= i + direction < len(self._all_comments):
                    row = self._all_comments[i + direction]
                    if row.get_mapped():
                        break
                    else:
                        i += direction
                        row = None

            if row is not None:
                row.grab_focus()
                self._selected = row
            else:
                # We went too far!
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

    def __init__(self, data, toplevel_cv, first=False, depth=0):
        Gtk.ListBox.__init__(self)
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

    def _add_comments(self, data):
        for comment in data:
            comment_data = comment['data']
            row = CommentRow(comment_data, self._depth, self._toplevel_cv)
            self._toplevel_cv.added_comment_row(row)
            row.recurse()
            row.got_more_comments.connect(self.__got_more_comments_cb)
            self.insert(row, -1)
            row.show()

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


class LoadFullCommentsRow(Gtk.InfoBar):

    load_full = GObject.Signal('load_full')

    def __init__(self):
        Gtk.InfoBar.__init__(self,
                             message_type=Gtk.MessageType.QUESTION)

        label = Gtk.Label(label='Showing only a subset of comments')
        self.get_content_area().add(label)
        label.show()

        self.add_button('Show All Comments', 1)

    def do_response(self, response):
        self.load_full.emit()


class _PostTopBar(Gtk.Bin):

    hide_toggled = GObject.Signal('hide-toggled', arg_types=[bool])

    def __init__(self, data, toplevel_cv, hideable=True,
                 refreshable=False, show_subreddit=False):
        Gtk.Bin.__init__(self, can_focus=True)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
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

        self._read = self._b.get_object('unread')
        self._read.props.visible = 'new' in data
        if 'new' in data:
            if data['new']:
                self._read.props.active = False
                self._read.get_style_context().add_class('unread')
                self._read.props.label = 'Mark as Read'
            else:
                self._read.props.active = True
                self._read.props.sensitive = False
                self._read.props.label = 'Read'

        self._name_button = self._b.get_object('name')
        self._abb = AuthorButtonBehaviour(
            self._name_button, self.data,
            self._toplevel_cv.get_original_poster())

        self._score_button = self._b.get_object('score')
        self._score_button.props.visible = 'score' in data
        if 'score' in data:
            self._sbb = ScoreButtonBehaviour(self._score_button, self.data)

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
            'r': (activate, [self._reply_button]),
            't': (activate, [self._time_button]),
            'a': (self.get_toplevel().goto_sublist,
                  ['/u/{}'.format(self.data['author'])]),
            's': (self.get_toplevel().goto_sublist,
                  ['/r/{}'.format(self.data['subreddit'])]),
            'space': (toggle, [self.expand]),
        }
        return process_shortcuts(shortcuts, event)

    def refresh_clicked_cb(self, button):
        self._toplevel_cv.refresh()

    def read_toggled_cb(self, toggle):
        if toggle.props.active:
            get_reddit_api().read_message(self.data['name'])
            self._read.get_style_context().remove_class('unread')
            self._read.props.active = True
            self._read.props.sensitive = False
            self._read.props.label = 'Read'

    def hide_toggled_cb(self, toggle):
        self.hide_toggled.emit(not toggle.props.active)

    def favorite_toggled_cb(self, button):
        get_reddit_api().set_saved(self.data['name'], button.props.active,
                                   None)

    def _make_reply_palette(self):
        palette = _ReplyPopover(self.data)
        palette.get_child().show_all()
        palette.posted.connect(self.__reply_posted_cb)
        return palette

    def __reply_posted_cb(self, caller, new_id):
        self._toplevel_cv.reply_posted(new_id)


class _ReplyPopover(Gtk.Popover):

    posted = GObject.Signal('posted', arg_types=[str])

    def __init__(self, data, **kwargs):
        Gtk.Popover.__init__(self, **kwargs)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.data = data
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box)

        sw = Gtk.ScrolledWindow()
        sw.set_size_request(500, 300)
        box.add(sw)
        self._textview = Gtk.TextView()
        self._textview.props.wrap_mode = Gtk.WrapMode.WORD
        self._textview.set_size_request(500, 300)
        sw.add(self._textview)

        self._done = Gtk.Button(label='Post Reply')
        self._done.connect('clicked', self.__done_clicked_cb)
        box.add(self._done)

        box.show_all()

    def do_event(self, event):
        shortcuts = {
            '<Ctrl>Return': (self.__done_clicked_cb, [None])
        }
        return process_shortcuts(shortcuts, event)

    def __done_clicked_cb(self, button):
        self._done.props.label = 'Sending...'
        self._done.props.sensitive = False
        b = self._textview.props.buffer
        text = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
        get_reddit_api().reply(self.data['name'], text, self.__reply_done_cb)

    def __reply_done_cb(self, data):
        new_id = data['json']['data']['things'][0]['data']['id']
        self.posted.emit(new_id)
        self.hide()
        self.destroy()


class CommentRow(Gtk.ListBoxRow):

    refresh = GObject.Signal('refresh')
    got_more_comments = GObject.Signal('got-more-comments', arg_types=[object])

    def __init__(self, data, depth, toplevel_cv):
        Gtk.ListBoxRow.__init__(self, selectable=False)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.data = data
        self.depth = depth
        self._toplevel_cv = toplevel_cv
        self._top = None

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self._box)
        self._box.show()

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

    def do_event(self, event):
        if self._top is not None:
            return self._top.do_event(event)
        else:
            shortcuts = {
                'Return': (self.__load_more_cb, [self._more_button])
            }
            return process_shortcuts(shortcuts, event)

    def __load_more_cb(self, button):
        button.props.sensitive = False
        get_reddit_api().load_more(
            self._toplevel_cv.get_link_name(),
            self.data, self.__loaded_more_cb)

    def __loaded_more_cb(self, comments):
        self.got_more_comments.emit(comments)

    def _show_normal_comment(self):
        self._top = _PostTopBar(self.data, self._toplevel_cv)
        self._top.hide_toggled.connect(self.__hide_toggled_cb)
        self._box.add(self._top)
        self._top.show()

        body_pango = markdown_to_pango(self.data['body'])
        self._label = SaneLabel(body_pango)
        self._box.add(self._label)
        self._label.show()

        self._sub = None
        self._revealer = None
        if self.data.get('replies'):
            self._revealer = Gtk.Revealer(
                transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN,
                reveal_child=True
            )
            revealer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self._revealer.add(revealer_box)
            revealer_box.show()
            self._box.add(self._revealer)
            self._revealer.show()

            self._sub = _CommentsView(
                self.data['replies']['data']['children'],
                self._toplevel_cv,
                depth=self.depth + 1)
            revealer_box.add(self._sub)
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
