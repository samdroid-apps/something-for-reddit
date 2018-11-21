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


from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from redditisgtk.comments import CommentsView
from redditisgtk.gtkutil import process_shortcuts
from redditisgtk.api import RedditAPI
from redditisgtk.readcontroller import get_read_controller
from redditisgtk import aboutrow
from redditisgtk import sublistrows


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

    def __init__(self, api: RedditAPI, sub: str = None):
        Gtk.ScrolledWindow.__init__(self)
        self.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        self._api = api
        self._sub = sub
        self._msg = None
        self._first_load = True

        self._spinner = Gtk.Spinner()
        self.add(self._spinner)
        self._spinner.show()

        if self._sub is not None:
            self.goto(self._sub)

    def get_uri(self):
        return self._sub

    def goto(self, sub):
        '''
        Sub could be '/r/gnu+linux' or '/r/rct/hot?t=month
        or even '/message/inbox'
        '''
        if self._msg is not None:
            self._api.cancel(self._msg)
        self._sub = sub
        width = self.get_allocated_width()
        self.remove(self.get_child())

        self.add(self._spinner)
        self._spinner.show()
        self._spinner.start()
        self.set_size_request(width, -1)

        self._msg = self._api.get_list(sub, self.__got_list_cb)

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

        if self._first_load:
            # First load you have to let the view set the size,
            # otherwise you get the tiny 20px width of the spinner
            self.set_size_request(-1, -1)
            self._first_load = False
        else:
            # If we keep the size request set, the user can't resize the view
            width = self.get_allocated_width()
            self.set_size_request(-1, -1)
            if isinstance(self.get_parent(), Gtk.Paned):
                self.get_parent().props.position = width

        self._first_row = None
        row = aboutrow.get_about_row(self._api, self._sub)
        if row is not None:
            row.get_style_context().add_class('about-row')
            self._listbox.insert(row, -1)
            row.show()
            self._first_row = row

        self.insert_data(j)
        self.focus()

    def _do_move(self, direction: int):
        focused = self._listbox.get_toplevel().get_focus()
        if focused.get_parent() == self._listbox:
            selected_row = focused
        else:
            selected_row = self._listbox.get_selected_row()
            if selected_row is None:
                selected_row = self._first_row

        new_index = selected_row.get_index() + direction
        new_row = self._listbox.get_row_at_index(new_index)

        if new_row is not None:
            new_row.grab_focus()
        else:
            # We went too far!
            s.error_bell()
            s.get_style_context().remove_class('angry')
            s.get_style_context().add_class('angry')
            GLib.timeout_add(
                500,
                s.get_style_context().remove_class,
                'angry')


    def __listbox_event_cb(self, listbox, event):
        shortcuts = {
            'k': (self._do_move, [-1]),
            'j': (self._do_move, [+1]),
            'Up': (self._do_move, [-1]),
            'Down': (self._do_move, [+1]),
            '0': (listbox.select_row, [self._first_row])
        }
        return process_shortcuts(shortcuts, event)

    def focus(self):
        s = None
        if self._listbox is not None:
            s = self._listbox.get_selected_row()
        if s is None:
            s = self._first_row
        s.grab_focus()

    def insert_data(self, j):
        first_inserted_row = None

        if 'data' not in j:
            return

        for post in j['data']['children']:
            if post['kind'] == 't3':
                row = sublistrows.LinkRow(self._api, post)
                row.goto_comments.connect(self.__row_goto_comments_cb)
            elif post['kind'] == 't1' or post['kind'] == 't4':
                row = sublistrows.MessageRow(self._api, post)
            else:
                row = Gtk.Label(label=str(post))
                row.set_line_wrap(True)
            self._listbox.insert(row, -1)
            row.show()
            if self._first_row is None:
                self._first_row = row
            if first_inserted_row is None:
                first_inserted_row = row

        row = sublistrows.MoreItemsRow(j['data']['after'])
        row.load_more.connect(self.__load_more_cb)
        self._listbox.insert(row, -1)
        row.show()
        if first_inserted_row is None:
            first_inserted_row = row

        return first_inserted_row

    def __load_more_cb(self, row, after):
        if row.is_loading_state:
            # Already loading
            return

        row.show_loading_state()
        row.grab_focus()

        def got_data(data):
            self._listbox.remove(row)
            row.hide()
            row.destroy()

            added_row = self.insert_data(data)
            if added_row is not None:
                # newly created widgets can not be focused until drawn
                GLib.idle_add(added_row.grab_focus)

        self._msg = self._api.get_list(
            '{}?after={}'.format(self._sub, after),
            got_data,
        )

    def __row_selected_cb(self, listbox, row):
        if row is None:
            return
        row.grab_focus()  # For keyboard shortcuts to work

        if hasattr(row, 'read'):
            row.read()

        if isinstance(row, sublistrows.MessageRow):
            if 'context' not in row.data:
                row.data['context'] = '/r/{}/comments/{}/slug/{}/'.format(
                    row.data['subreddit'],
                    row.data['link_id'][len('t4_'):],
                    row.data['id'])
            get_read_controller().read(row.data['name'])
            self._handle_activate(permalink=row.data['context'],
                                  link_first=False)
        elif isinstance(row, sublistrows.LinkRow):
            self._handle_activate(row.data)
        elif isinstance(row, sublistrows.MoreItemsRow):
            row.activate()
        elif isinstance(row, aboutrow.AboutRow):
            pass
        else:
            raise Exception('Unknown type of row activated: {}'.format(row))

    def _handle_activate(self, data=None, permalink=None, link_first=True):
        link = None
        if data is not None:
            get_read_controller().read(data['name'])
            if not data.get('is_self') and 'url' in data:
                link = data['url']

        comments = CommentsView(self._api, data, permalink=permalink)
        self.new_other_pane.emit(link, comments, link_first)

    def __row_goto_comments_cb(self, row):
        row.read()
        self._handle_activate(row.data, link_first=False)
