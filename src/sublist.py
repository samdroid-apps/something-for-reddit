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
from redditisgtk.api import get_reddit_api, is_special_sub
from redditisgtk.readcontroller import get_read_controller
from redditisgtk.mediapreview import get_preview_palette


class SubList(Gtk.ScrolledWindow):
    '''
    Lists post in a subreddit, items in an inbox.  Whatever really.
    '''

    new_other_pane = GObject.Signal(
        'new-other-pane', arg_types=[str, object])

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        self.props.hscrollbar_policy = Gtk.PolicyType.NEVER
        self._sub = None
        self._msg = None

        self._spinner = Gtk.Spinner()
        self.add(self._spinner)
        self._spinner.show()

    def get_sub_name(self):
        '''Returns the sub name, eg. "gnu" or "all" or "funny"'''
        # /r/[name]?t=whatever -> name
        return self._sub.split('/')[2].split('?')[0]

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
        self._listbox.connect('row-activated', self.__row_selected_cb)
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

        row.get_style_context().add_class('read')
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

    def _handle_activate(self, data, comments=None):
        link = None
        get_read_controller().read(data['name'])

        if not data.get('is_self') and 'url' in data:
            link = data['url']
        comments = CommentsView(data, comments=comments)
        self.new_other_pane.emit(link, comments)

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


# from the 'distinguished' attribute
AUTHOR_COLORS = {
    None: '',
    'moderator': 'lightgreen',
    'admin': 'red',
    'special': 'purple'
}


class SubItemRow(Gtk.ListBoxRow):
    def __init__(self, data):
        Gtk.ListBoxRow.__init__(self)
        self.data = data['data']
        self._pbl = None
        self._msg = None

        if get_read_controller().is_read(self.data['name']):
            self.get_style_context().add_class('read')

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(box)
        box.show()

        l = Gtk.Label()
        l.props.xalign = 0
        l.props.justify = Gtk.Justification.LEFT
        l.set_line_wrap(True)

        self.data['score'] = self.data['score'] if 'score' in self.data else ''
        self.data['num_comments'] = self.data.get('num_comments') or 'no'

        edited_string = ''
        if self.data.get('edited'):
            edited_string = '(edited {})'.format(
                arrow.get(self.data['edited']).humanize())
        score_color = {True: 'color="darkorange"',
                       False: 'color="darkorchid"'}.get(
                        self.data.get('likes'), '')

        nsfw_tag = ''
        if self.data.get('over18'):
            # One day, we will pipe this through gettext
            nsfw_tag = ' <span color="red">{}</span>'.format('NSFW')

        gilded_tag = ''
        if self.data.get('gilded') > 0:
            gilded_tag = ('<span bgcolor="darkorange" color="white"><b>'
                          '★{}</b></span> ').format(self.data['gilded'])

        author_color = '' if not self.data['distinguished'] else \
            'bgcolor="{}"'.format(AUTHOR_COLORS[self.data['distinguished']])
        
        l.set_markup(
            '<span {color}><big>{gilded_tag}'
            '<span weight="heavy" {score_color}>{score}</span></big>'
            ' <span {author_color}>{author}</span> in'
            ' /r/{subreddit}{nsfw_tag}\n'
            '<big>{title}</big>\n'
            '{num_comments} comments · {domain}'
            ' · {created_string} {edited_string}'
            '</span>'.format(
                color='color="green"' if self.data.get('stickied') else '',
                score_color=score_color,
                edited_string=edited_string,
                created_string=arrow.get(self.data['created_utc']).humanize(),
                nsfw_tag=nsfw_tag,
                gilded_tag=gilded_tag,
                author_color=author_color,
                **self.data))
        box.add(l)
        l.show()

        self._fetch_thumbnail(self.data.get('thumbnail'))
        self._image_button = Gtk.Button()
        self._image = Gtk.Image()
        self._image_button.set_image(self._image)
        box.add(self._image_button)
        self._preview_palette = None

    def _fetch_thumbnail(self, url):
        if not url or url in ['default', 'self', 'nsfw']:
            return

        self._msg = get_reddit_api().download_thumb(url,
                                                    self.__message_done_cb)

    def do_unrealize(self):
        if self._msg is not None:
            get_reddit_api().cancel(self._msg)

    def __message_done_cb(self, pixbuf):
        self._msg = None
        self._image.props.pixbuf = pixbuf
        self._image.show()
        self._image_button.show()
        self._image_button.connect('clicked', self.__image_clicked_cb)

    def __image_clicked_cb(self, button):
        if self._preview_palette is None:
            self._preview_palette = get_preview_palette(
                self.data, relative_to=button)
        self._preview_palette.show()
