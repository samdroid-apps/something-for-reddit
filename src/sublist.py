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


import json
import arrow
from pprint import pprint

from gi.repository import Gtk
from gi.repository import Soup
from gi.repository import GObject

from redditisgtk.comments import CommentsView, CommentRow, MessageRow
from redditisgtk.buttons import (ScoreButtonBehaviour, AuthorButtonBehaviour,
                                 SubButtonBehaviour, TimeButtonBehaviour)
from redditisgtk.api import get_reddit_api
from redditisgtk.readcontroller import get_read_controller
from redditisgtk.mediapreview import get_preview_palette


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
        self.remove(self.get_child())
        self.add(self._spinner)
        self._spinner.show()
        self._spinner.start()
        self._msg = get_reddit_api().get_list(sub, self.__got_list_cb)

    def __got_list_cb(self, j):
        self._msg = None
        self.remove(self.get_child())
        self._listbox = Gtk.ListBox()
        self._listbox.connect('row-selected', self.__row_selected_cb)
        # THINK:  Hidden refresh function?
        # self._listbox.connect('row-activated', self.__row_selected_cb)
        self._listbox.props.selection_mode = Gtk.SelectionMode.BROWSE
        self.add(self._listbox)
        self._listbox.show()
        self.insert_data(j)

    def insert_data(self, j):
        if 'data' not in j:
            return

        for post in j['data']['children']:
            if post['kind'] == 't3':
                row = SubItemRow(post)
                row.goto_comments.connect(self.__row_goto_comments_cb)
            elif post['kind'] == 't1':
                row = CommentRow(post['data'], 0)
            elif post['kind'] == 't4':
                row = MessageRow(post['data'])
                pprint(post['data'])
            else:
                row = Gtk.Label(label=str(post))
                row.set_line_wrap(True)
            self._listbox.insert(row, -1)
            row.show()

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

        if hasattr(row, 'read'):
            row.read()
        if 'context' in row.data:
            # We need to download first
            # TODO: Progress indicator for user
            get_reddit_api().get_list(row.data['context'],
                                      self.__got_context_list_cb)
        else:
            self._handle_activate(row.data)

    def __got_context_list_cb(self, data):
        self._handle_activate(data[0]['data']['children'][0]['data'],
                              comments=data)

    def _handle_activate(self, data, comments=None, link_first=True):
        link = None
        get_read_controller().read(data['name'])

        if not data.get('is_self') and 'url' in data:
            link = data['url']
        comments = CommentsView(data, comments=comments)
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
