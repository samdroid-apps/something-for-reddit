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


from pprint import pprint

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject

from redditisgtk.comments import CommentsView
from redditisgtk.buttons import (ScoreButtonBehaviour, AuthorButtonBehaviour,
                                 SubButtonBehaviour, TimeButtonBehaviour,
                                 SubscribeButtonBehaviour, process_shortcuts)
from redditisgtk.markdownpango import markdown_to_pango, set_markup_sane
from redditisgtk.api import get_reddit_api
from redditisgtk.readcontroller import get_read_controller
from redditisgtk.mediapreview import get_preview_palette
from redditisgtk.submit import SubmitWindow


class SubList(Gtk.ScrolledWindow):
    '''
    Lists post in a subreddit, items in an inbox.  Whatever really.
    '''

    new_other_pane = GObject.Signal(
        'new-other-pane', arg_types=[str, object, bool])
    '''
    Args:
        link (str):  Link to put in webview or None
        comments_view (Gtk.Widget):  New comments view
        link_first (bool):  if True the link should be the default view
            - if a link is available - whereas False makes the comments
            the default view
    '''

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        self.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        self._sub = None
        self._msg = None
        self._first_load = True

        self._spinner = Gtk.Spinner()
        self.add(self._spinner)
        self._spinner.show()

    def get_uri(self):
        return self._sub

    def goto(self, sub):
        '''
        Sub could be '/r/gnu+linux' or '/r/rct/hot?t=month
        or even '/message/inbox'
        '''
        if self._msg is not None:
            get_reddit_api().cancel(self._msg)
        self._sub = sub
        width = self.get_allocated_width()
        self.remove(self.get_child())

        self.add(self._spinner)
        self._spinner.show()
        self._spinner.start()
        self.set_size_request(width, -1)

        self._msg = get_reddit_api().get_list(sub, self.__got_list_cb)

    def __got_list_cb(self, j):
        self._msg = None
        self.remove(self.get_child())

        self._listbox = Gtk.ListBox()
        self._listbox.connect('event', self.__listbox_event_cb)
        self._listbox.connect('row-selected', self.__row_selected_cb)
        self._listbox.connect('row-activated', self.__row_selected_cb)
        self._listbox.props.selection_mode = Gtk.SelectionMode.BROWSE
        self.add(self._listbox)
        self._listbox.show()

        if not self._first_load:
            # If we keep the size request set, the user can't resize the view
            width = self.get_allocated_width()
            self.set_size_request(-1, -1)
            if isinstance(self.get_parent(), Gtk.Paned):
                self.get_parent().props.position = width
        else:
            # First load you have to let the view set the size,
            # otherwise you get the tiny 20px width of the spinner
            self.set_size_request(-1, -1)
            self._first_load = False

        self._first_row = None
        row = get_about_row(self._sub)
        if row is not None:
            row.get_style_context().add_class('about-row')
            self._listbox.insert(row, -1)
            row.show()
            self._first_row = row

        self.insert_data(j)
        self.focus()

    def __listbox_event_cb(self, listbox, event):
        def move(direction):
            focused = listbox.get_toplevel().get_focus()
            if focused.get_parent() == listbox:
                s = focused
            else:
                s = listbox.get_selected_row() or self._first_row
            row = listbox.get_row_at_index(s.get_index() + direction)
            if row is not None:
                row.grab_focus()
            else:
                # We went too far!
                s.error_bell()
                s.get_style_context().remove_class('angry')
                s.get_style_context().add_class('angry')
                GLib.timeout_add(
                    500,
                    s.get_style_context().remove_class,
                    'angry')

        shortcuts = {
            'k': (move, [-1]),
            'j': (move, [+1]),
            'Up': (move, [-1]),
            'Down': (move, [+1]),
            '0': (listbox.select_row, [self._first_row])
        }
        return process_shortcuts(shortcuts, event)

    def focus(self):
        s = self._listbox.get_selected_row() or self._first_row
        s.grab_focus()

    def insert_data(self, j):
        if 'data' not in j:
            return

        for post in j['data']['children']:
            if post['kind'] == 't3':
                row = SubItemRow(post)
                row.goto_comments.connect(self.__row_goto_comments_cb)
            elif post['kind'] == 't1' or post['kind'] == 't4':
                row = MessageRow(post)
            else:
                row = Gtk.Label(label=str(post))
                row.set_line_wrap(True)
            self._listbox.insert(row, -1)
            row.show()
            if self._first_row is None:
                self._first_row = row

        row = MoreItemRow(j['data']['after'])
        row.load_more.connect(self.__load_more_cb)
        self._listbox.insert(row, -1)
        row.show()

    def __load_more_cb(self, caller, after):
        self._msg = get_reddit_api().get_list(
            '{}?after={}'.format(self._sub, after),
            self.insert_data
        )

    def __row_selected_cb(self, listbox, row):
        if row is None:
            return
        row.grab_focus()  # For keyboard shortcuts to work

        if hasattr(row, 'read'):
            row.read()
        if isinstance(row, MessageRow):
            if 'context' not in row.data:
                row.data['context'] = '/r/{}/comments/{}/slug/{}/'.format(
                    row.data['subreddit'],
                    row.data['link_id'][len('t4_'):],
                    row.data['id'])
            get_read_controller().read(row.data['name'])
            self._handle_activate(permalink=row.data['context'],
                                  link_first=False)
        else:
            self._handle_activate(row.data)

    def _handle_activate(self, data=None, permalink=None, link_first=True):
        link = None
        if data is not None:
            get_read_controller().read(data['name'])
            if not data.get('is_self') and 'url' in data:
                link = data['url']

        comments = CommentsView(data, permalink=permalink)
        self.new_other_pane.emit(link, comments, link_first)

    def __row_goto_comments_cb(self, row):
        row.read()
        self._handle_activate(row.data, link_first=False)


class MoreItemRow(Gtk.ListBoxRow):

    load_more = GObject.Signal('load-more', arg_types=[str])

    def __init__(self, after):
        Gtk.ListBoxRow.__init__(self)
        self._after = after

        if after is not None:
            b = Gtk.Button(label='Load More')
        else:
            b = Gtk.Button(label='End of Listing')
            b.props.sensitive = False
        b.connect('clicked', self.__clicked_cb)
        self.add(b)
        b.show()

    def __clicked_cb(self, button):
        self.hide()
        self.load_more.emit(self._after)
        self.destroy()


class SubItemRow(Gtk.ListBoxRow):

    goto_comments = GObject.Signal('goto-comments')

    def __init__(self, data):
        Gtk.ListBoxRow.__init__(self)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.get_style_context().add_class('link-row')
        self.data = data['data']
        self._msg = None

        self._builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/row-link.ui')
        self._g = self._builder.get_object
        self.add(self._g('box'))

        read = get_read_controller().is_read(self.data['name'])
        if read:
            self.read()

        # Keep a reference so the GC doesn't collect them
        self._sbb = ScoreButtonBehaviour(self._g('score'), self.data)
        self._abb = AuthorButtonBehaviour(self._g('author'), self.data)
        self._srbb = SubButtonBehaviour(self._g('subreddit'), self.data)
        self._tbb = TimeButtonBehaviour(self._g('time'), self.data)

        self._g('nsfw').props.visible = self.data.get('over_18')
        self._g('saved').props.visible = self.data.get('saved')
        self._g('sticky').props.visible = self.data.get('stickied')
        if self.data.get('stickied'):
            self.get_style_context().add_class('sticky')

        if self.data['num_comments']:
            self._g('comments').props.label = \
                '{}c'.format(self.data['num_comments'])
        else:
            self._g('comments').props.label = 'no c'
        self._g('comments').connect('clicked', self.__comments_clicked_cb)

        self._g('title').props.label = self.data['title']
        self._g('domain').props.label = self.data['domain']

        self._fetch_thumbnail(self.data.get('thumbnail'))
        self._preview_palette = None

    def read(self):
        self.get_style_context().add_class('read')
        self._g('unread').props.visible = False

    def do_event(self, event):
        shortcuts = {
            'u': (self._sbb.vote, [+1]),
            'd': (self._sbb.vote, [-1]),
            'n': (self._sbb.vote, [0]),
            'c': (self.goto_comments.emit, []),
            'a': (self.get_toplevel().goto_sublist,
                  ['/u/{}'.format(self.data['author'])]),
            's': (self.get_toplevel().goto_sublist,
                  ['/r/{}'.format(self.data['subreddit'])]),
        }
        return process_shortcuts(shortcuts, event)

    def __comments_clicked_cb(self, button):
        self.goto_comments.emit()

    def _fetch_thumbnail(self, url):
        if not url or url in ['default', 'self', 'nsfw']:
            return
        self._msg = get_reddit_api().download_thumb(
            url, self.__message_done_cb)

    def do_unrealize(self):
        if self._msg is not None:
            get_reddit_api().cancel(self._msg)

    def __message_done_cb(self, pixbuf):
        self._msg = None
        self._g('preview').props.pixbuf = pixbuf
        self._g('preview-button').show()
        self._g('preview-button').connect('clicked', self.__image_clicked_cb)

    def __image_clicked_cb(self, button):
        if self._preview_palette is None:
            self._preview_palette = get_preview_palette(
                self.data, relative_to=button)
        self._preview_palette.show()


class MessageRow(Gtk.ListBoxRow):

    def __init__(self, data):
        Gtk.ListBoxRow.__init__(self)
        self.get_style_context().add_class('link-row')
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.data = data['data']
        self._msg = None

        is_comment_reply = self.data.get('subreddit') is not None

        self._builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/row-comment.ui')
        self._g = self._builder.get_object
        self.add(self._g('box'))

        read = not self.data.get('new', True)
        if read:
            self.read()

        # Keep a reference so the GC doesn't collect them
        self._abb = AuthorButtonBehaviour(self._g('author'), self.data)
        self._tbb = TimeButtonBehaviour(self._g('time'), self.data)
        if is_comment_reply:
            self._srbb = SubButtonBehaviour(self._g('subreddit'), self.data)
        else:
            self._g('subreddit').props.sensitive = False
            self._g('subreddit').props.label = 'PM'

        self._g('nsfw').props.visible = self.data.get('over_18')
        self._g('saved').props.visible = self.data.get('saved')

        self._g('title').props.label = (self.data.get('link_title') or
                                        self.data['subject'])
        body_pango = markdown_to_pango(self.data['body'])
        set_markup_sane(self._g('text'), body_pango)

        if is_comment_reply:
            self._g('type-private-message').props.visible = False
        else:
            self._g('type-comment-reply').props.visible = False

    def do_event(self, event):
        shortcuts = {
            'a': (self.get_toplevel().goto_sublist,
                  ['/u/{}'.format(self.data['author'])]),
            's': (self.get_toplevel().goto_sublist,
                  ['/r/{}'.format(self.data['subreddit'])]),
        }
        return process_shortcuts(shortcuts, event)

    def read(self):
        if 'new' in self.data and self.data['new']:
            get_reddit_api().read_message(self.data['name'])
            self.data['new'] = False
        self.get_style_context().add_class('read')
        self._g('unread').props.visible = False


class _SubredditAboutRow(Gtk.ListBoxRow):

    def __init__(self, subreddit_name):
        Gtk.ListBoxRow.__init__(self, selectable=False)

        self._subreddit_name = subreddit_name
        self._loaded = False

        self._builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/subreddit-about.ui')
        self._g = self._builder.get_object

        self.add(self._g('box'))
        self._g('subreddit').props.label = self._subreddit_name
        self._sbb = SubscribeButtonBehaviour(
            self._g('subscribe'), self._subreddit_name)
        self._g('submit').connect('clicked', self.__submit_clicked_cb)
        self._g('expander').connect(
            'notify::expanded', self.__notify_expanded_cb)

    def __submit_clicked_cb(self, button):
        w = SubmitWindow(sub=self._subreddit_name)
        w.show()

    def __notify_expanded_cb(self, expander, pspec):
        if not self._loaded:
            get_reddit_api().get_subreddit_info(
                self._subreddit_name, self.__got_info_cb)
            self._loaded = True

    def __got_info_cb(self, data):
        data = data['data']
        set_markup_sane(self._g('sidebar'),
                        markdown_to_pango(data['description']))


class _UserAboutRow(Gtk.ListBoxRow):

    def __init__(self, name):
        Gtk.ListBoxRow.__init__(self, selectable=False)

        self._name = name

        self._builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/user-about.ui')
        self._g = self._builder.get_object

        self.add(self._g('box'))
        self._g('name').props.label = self._name

        get_reddit_api().get_user_info(
            self._name, self.__got_info_cb)

    def __got_info_cb(self, data):
        data = data['data']
        self._g('karma').props.label = \
            '{link_karma}l / {comment_karma}c'.format(**data)


def get_about_row(sub):
    # Disregard leading slash
    url_parts = sub.strip('/').split('/')

    # Show if it is like /r/sub
    if len(url_parts) >= 2 and url_parts[0] == 'r' and url_parts[1] != 'all':
        return _SubredditAboutRow(url_parts[1])

    # Eg. /user/name(/*)
    if len(url_parts) >= 2 and url_parts[0] in ('user', 'u'):
        return _UserAboutRow(url_parts[1])

    return None
