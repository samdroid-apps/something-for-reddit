# Copyright 2016-2018 Sam Parkinson <sam@sam.today>
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
from gi.repository import Gdk
from gi.repository import GObject

from redditisgtk.buttons import (ScoreButtonBehaviour, AuthorButtonBehaviour,
                                 SubButtonBehaviour, TimeButtonBehaviour)
from redditisgtk.gtkutil import process_shortcuts
from redditisgtk import newmarkdown
from redditisgtk.api import RedditAPI
from redditisgtk.readcontroller import get_read_controller
from redditisgtk.mediapreview import get_preview_palette


class MoreItemsRow(Gtk.ListBoxRow):

    load_more = GObject.Signal('load-more', arg_types=[str])

    def __init__(self, after):
        Gtk.ListBoxRow.__init__(self)
        self.is_loading_state = False
        self._after = after

        if after is not None:
            self._btn = Gtk.Button(label='Load More')
        else:
            self._btn = Gtk.Button(
                label='End of Listing',
                sensitive=False,
            )
        self._btn.connect('clicked', self.__clicked_cb)
        self.add(self._btn)
        self._btn.show()

    def __clicked_cb(self, button):
        self.activate()

    def activate(self):
        self.load_more.emit(self._after)

    def show_loading_state(self):
        self.is_loading_state = True

        self._btn.remove(self._btn.get_child())
        spinner = Gtk.Spinner()
        spinner.start()
        self._btn.add(spinner)
        spinner.show()

        self._btn.props.sensitive = False


def get_thumbnail_url(data: dict) -> str:
    '''
    Get the URL of the thumbnail image, or return None if there is no
    thumbnail.  Takes a reddit subreddit link item.
    '''
    # Old style thumbnail data
    url = data.get('thumbnail')
    if url in ['default', 'self', 'nsfw']:
        return None

    # I think this is new style data
    preview_images = data.get('preview', {}).get('images', [])
    if preview_images:
        image = preview_images[0]
        # choose smallest height
        thumbs = sorted(image.get('resolutions', []),
                        key=lambda d: d.get('width'))
        if thumbs:
            url = thumbs[0]['url']

    if url.startswith('http'):
        return url

    return None


class LinkRow(Gtk.ListBoxRow):

    goto_comments = GObject.Signal('goto-comments')

    def __init__(self, api: RedditAPI, data):
        Gtk.ListBoxRow.__init__(self)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.get_style_context().add_class('link-row')
        self.data = data['data']
        self._msg = None
        self._api = api

        self._builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/row-link.ui')
        self._g = self._builder.get_object
        self.add(self._g('box'))

        read = get_read_controller().is_read(self.data['name'])
        if read:
            self.read()

        # Keep a reference so the GC doesn't collect them
        self._sbb = ScoreButtonBehaviour(
            self._api, self._g('score'), self.data)
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

        self._fetch_thumbnail()
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

    def _fetch_thumbnail(self):
        url = get_thumbnail_url(self.data)
        if url is not None:
            self._msg = self._api.download_thumb(
                url, self.__message_done_cb)

    def do_unrealize(self):
        if self._msg is not None:
            self._api.cancel(self._msg)

    def __message_done_cb(self, pixbuf):
        self._msg = None
        self._g('preview').props.pixbuf = pixbuf
        self._g('preview-button').show()
        self._g('preview-button').connect('clicked', self.__image_clicked_cb)

    def __image_clicked_cb(self, button):
        if self._preview_palette is None:
            self._preview_palette = get_preview_palette(
                self._api, self.data, relative_to=button)
        self._preview_palette.show()


class MessageRow(Gtk.ListBoxRow):

    def __init__(self, api: RedditAPI, data):
        Gtk.ListBoxRow.__init__(self)
        self.get_style_context().add_class('link-row')
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self._api = api
        self.data = data['data']

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
        content = newmarkdown.make_markdown_widget(self.data['body'])
        self._g('grid').attach(content, 0, 2, 3, 1)

        if is_comment_reply:
            self._g('type-private-message').props.visible = False
        else:
            self._g('type-comment-reply').props.visible = False

    def do_event(self, event):
        shortcuts = {
            'a': (self.get_toplevel().goto_sublist,
                  ['/u/{}'.format(self.data['author'])]),
        }
        if self.data.get('subreddit'):
            shortcuts['s'] = (
                self.get_toplevel().goto_sublist,
                ['/r/{}'.format(self.data['subreddit'])],
            )
        return process_shortcuts(shortcuts, event)

    def read(self):
        if 'new' in self.data and self.data['new']:
            self._api.read_message(self.data['name'])
            self.data['new'] = False
        self.get_style_context().add_class('read')
        self._g('unread').props.visible = False
