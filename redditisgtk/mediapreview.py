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
from gi.repository import Gdk

import subprocess
from tempfile import mkstemp
import urllib.parse
from html.parser import HTMLParser

from redditisgtk.api import RedditAPI
from redditisgtk.webviews import FullscreenableWebview


def _unescape(s):
    return urllib.parse.unquote(
        s.replace('&lt;', '<').replace('&gt;', '>')
        .replace('&amp;', '&'))


class _IframeSrcGetter(HTMLParser):
    src = None

    def handle_starttag(self, tag, attrs):
        if tag == 'iframe':
            for k, v in attrs:
                if k == 'src':
                    self.src = v


def get_preview_palette(api: RedditAPI, listing, **kwargs):
    if 'content' in listing.get('media_embed', {}):
        embed = listing['media_embed']
        parser = _IframeSrcGetter()
        parser.feed(_unescape(embed['content']))
        return WebViewPopover(
            uri=parser.src,
            width=embed['width'], height=embed['height'],
            **kwargs)
    elif len(listing.get('preview', {}).get('images', [])):
        uri = listing['preview']['images'][0]['source']['url']
        return _ImagePreviewPalette(
            api, uri, **kwargs)
    return None


class WebViewPopover(Gtk.Popover):

    def __init__(self, uri, width, height, **kwargs):
        if uri.startswith('//'):
            uri = 'https:' + uri

        Gtk.Popover.__init__(self, **kwargs)
        self._wv = FullscreenableWebview()
        self._wv.load_uri(uri)
        self._wv.set_size_request(width, height)
        self.add(self._wv)
        self._wv.show()


class _ImagePreviewPalette(Gtk.Popover):
    # TODO:  Scrolling and scaling

    def __init__(self, api: RedditAPI, uri, **kwargs):
        Gtk.Popover.__init__(self, **kwargs)
        overlay = Gtk.Overlay()
        self.add(overlay)
        overlay.show()

        self._image = _RemoteImage(api, uri)
        win_w, win_h = self.get_toplevel().get_size()
        max_w, max_h = win_w / 2, win_h / 2
        self._image.set_size_request(min(Gdk.Screen.width() / 3, max_w),
                                     min(Gdk.Screen.height() / 3, max_h))
        overlay.add(self._image)
        self._image.show()

        self._eog = Gtk.Button(halign=Gtk.Align.END,
                               valign=Gtk.Align.START,
                               label='EoG')
        self._eog.connect('clicked', self.__eog_clicked_cb)
        overlay.add_overlay(self._eog)
        self._eog.show()

    def __eog_clicked_cb(self, button):
        fd, path = mkstemp()
        self._image.save_to(path)
        subprocess.call(['eog', '--fullscreen', path])


class _RemoteImage(Gtk.Bin):
    # TODO:  Reload on error

    def __init__(self, api: RedditAPI, uri):
        # TODO: this really shouldn't need a reddit api.  Maybe just a soup
        # session?  This feels like a bad DI pattern right now
        Gtk.Bin.__init__(self)

        self._spinner = Gtk.Spinner()
        self.add(self._spinner)
        self._spinner.show()

        self._image = Gtk.Image()
        self.add(self._image)
        api.download_thumb(uri, self.__message_done_cb)

    def __message_done_cb(self, pixbuf):
        old_sr = self.get_size_request()
        self._image.props.pixbuf = pixbuf
        self.remove(self.get_child())
        self.add(self._image)
        self._image.show()
        self._image.set_size_request(*old_sr)

    def save_to(self, path):
        self._image.props.pixbuf.savev(path, 'png', [], [])
