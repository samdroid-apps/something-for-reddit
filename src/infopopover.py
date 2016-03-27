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

from gi.repository import Gtk

from redditisgtk.comments import SaneLabel
from redditisgtk.markdownpango import markdown_to_pango
from redditisgtk.api import get_reddit_api

class VScrollingPopover(Gtk.Popover):
    def __init__(self, **kwargs):
        Gtk.Popover.__init__(self, vexpand=True, **kwargs)
        self._sw = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            height_request=400)
        self.add(self._sw)
        self._sw.show()

    def set_scrolled_child(self, child):
        '''
        Sets the child of the scrolled window.

        Destroys any child if it is already in the scrolled window
        '''
        c = self._sw.get_child()
        if c is not None:
            self._sw.remove(c)
            c.destroy()
        self._sw.add(child)

class InfoPalette(VScrollingPopover):
    def __init__(self, subreddit_name, **kwargs):
        '''
        Args:
            subreddit_name (str):  name like 'linux' or 'gnu',
                NOT with the /r/
        '''
        VScrollingPopover.__init__(self, **kwargs)
        spinner = Gtk.Spinner()
        self.set_scrolled_child(spinner)
        spinner.show()

        self._subreddit_name = subreddit_name
        get_reddit_api().get_subreddit_info(subreddit_name, self.__got_info_cb)

    def __got_info_cb(self, j):
        if j.get('error') is not None:
            error_text = str(j['error'])
            if j['error'] == 404:
                error_text = 'No information found (404)'

            label = SaneLabel(error_text)
            label.get_style_context().add_class('error-label')
            self.set_scrolled_child(label)
            label.show()
            return

        data = j['data']
        self._data = data

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_scrolled_child(box)
        box.show()

        self._image = Gtk.Image()
        if data.get('header_img') is not None:
            get_reddit_api().download_thumb(data['header_img'],
                                            self.__header_downloaded_cb)
        box.add(self._image)

        self._subscribe = Gtk.ToggleButton(active=data['user_is_subscriber'])
        self._set_subscribe_label(data['subscribers'])
        self._subscribe.connect('toggled', self.__subscribe_toggled_cb)
        box.add(self._subscribe)
        self._subscribe.show()

        body_pango = markdown_to_pango(data['description'])
        label = SaneLabel(body_pango)
        box.add(label)
        label.show()
        # WTF:  Allow hscrolling so that the label actually word wraps
        self.get_child().props.hscrollbar_policy = Gtk.PolicyType.AUTOMATIC
        self.get_child().props.width_request = 400

    def __header_downloaded_cb(self, pixbuf):
        self._image.props.pixbuf = pixbuf
        self._image.show()

    def _set_subscribe_label(self, subscribers):
        if self._subscribe.props.active:
            self._subscribe.props.label = \
                'Subscribed (with {} others)'.format(subscribers - 1)
        else:
            self._subscribe.props.label = \
                'Subscribe (join {} others)'.format(subscribers)

    def __subscribe_toggled_cb(self, toggle):
        self._subscribe.props.label = 'Subscribing...'  \
            if self._subscribe.props.active else 'Unsubscribing...'
        self._subscribe.props.sensitive = False

        get_reddit_api().set_subscribed(self._subreddit_name,
                                        self._subscribe.props.active,
                                        self.__subscribe_cb)

    def __subscribe_cb(self, j):
        if j.get('error') is None:
            self._subscribe.props.sensitive = True
            self._set_subscribe_label(self._data['subscribers'])
            get_reddit_api().update_subscriptions()
