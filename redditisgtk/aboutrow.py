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

from gi.repository import Gtk

from redditisgtk import newmarkdown
from redditisgtk.buttons import SubscribeButtonBehaviour
from redditisgtk import submit
from redditisgtk.api import RedditAPI


class AboutRow(Gtk.ListBoxRow):
    '''
    Abstract base class for AboutRows
    '''

    def __init__(self, **kwargs):
        Gtk.ListBoxRow.__init__(self, **kwargs)


class _SubredditAboutRow(AboutRow):

    def __init__(self, api: RedditAPI, subreddit_name: str):
        super().__init__(selectable=False)

        self._subreddit_name = subreddit_name
        self._api = api
        self._loaded = False

        self._builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/subreddit-about.ui')
        self._g = self._builder.get_object

        self.add(self._g('box'))
        self._g('subreddit').props.label = self._subreddit_name
        self._sbb = SubscribeButtonBehaviour(
            self._api, self._g('subscribe'), self._subreddit_name)
        self._g('submit').connect('clicked', self.__submit_clicked_cb)
        self._g('expander').connect(
            'notify::expanded', self.__notify_expanded_cb)

    def __submit_clicked_cb(self, button):
        w = submit.SubmitWindow(self._api, sub=self._subreddit_name)
        w.show()

    def __notify_expanded_cb(self, expander, pspec):
        if not self._loaded:
            self._api.get_subreddit_info(
                self._subreddit_name, self.__got_info_cb)
            self._loaded = True

    def __got_info_cb(self, data):
        expander = self._g('expander')
        child = expander.get_child()
        if child is not None:
            expander.remove(ch)
            ch.destroy()

        markdown = data['data']['description']
        expander.add(newmarkdown.make_markdown_widget(markdown))


class _UserAboutRow(AboutRow):

    def __init__(self, api: RedditAPI, name: str):
        super().__init__(selectable=False)

        self._name = name

        self._builder = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/user-about.ui')
        self._g = self._builder.get_object

        self.add(self._g('box'))
        self._g('name').props.label = self._name

        api.get_user_info(
            self._name, self.__got_info_cb)

    def __got_info_cb(self, data):
        data = data['data']
        self._g('karma').props.label = \
            '{link_karma}l / {comment_karma}c'.format(**data)


def get_about_row(api: RedditAPI, sub: str):
    # Disregard leading slash
    url_parts = sub.strip('/').split('/')

    # Show if it is like /r/sub
    if len(url_parts) >= 2 and url_parts[0] == 'r' and url_parts[1] != 'all':
        return _SubredditAboutRow(api, url_parts[1])

    # Eg. /user/name(/*)
    if len(url_parts) >= 2 and url_parts[0] in ('user', 'u'):
        return _UserAboutRow(api, url_parts[1])

    return None
