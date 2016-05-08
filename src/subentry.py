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
from gi.repository import Gdk
from gi.repository import GObject

from redditisgtk.api import (get_reddit_api, PREPEND_SUBS, is_special_sub,
                             SORTINGS, SPECIAL_SUBS, SORTING_TIMES)


def _clean_sub(sub):
    if sub == '/r/' or sub == '/r' or sub == '/':
        return None
    if sub.endswith('/'):
        sub = sub[:-1]
    if not sub.startswith('/'):
        sub = '/' + sub
    if sub.startswith('/u/'):
        sub = '/user/' + sub[len('/u/'):]
        if len(sub.split('/')) == 3:  # []/[user]/[name]
            sub = sub + '/overview'
    if sub == '/inbox':
        sub = '/message/inbox'
    if not is_special_sub(sub):
        if not sub.startswith('/r/'):
            sub = '/r' + sub
    return sub


class SubEntry(Gtk.Entry):
    '''
    The thing that goes in the middle of the header bar, and
    shows the current subreddit
    '''

    activate = GObject.Signal('reddit-activate', arg_types=[str])
    escape_me = GObject.Signal('escape-me')

    def __init__(self):
        Gtk.Entry.__init__(
            self,
            text='/r/all',
            secondary_icon_name='go-down-symbolic',
            secondary_icon_sensitive=True,
            secondary_icon_tooltip_text='View List'
        )
        self.set_size_request(400, 0)
        self._palette = _ListPalette(self, relative_to=self)
        self._palette.selected.connect(self.__selected_cb)

        # FIXME:  There is no do_icon_press by gobject
        self.connect('icon-press', SubEntry.do_icon_press)
        self.connect('notify::text', self.__notify_text_cb)

    def do_event(self, event):
        if event.type != Gdk.EventType.KEY_PRESS:
            return
        if event.keyval == Gdk.KEY_Down:
            if self._palette.props.visible:
                self._palette.grab_focus()
            else:
                self._show_palette()
            return True
        if event.keyval == Gdk.KEY_Escape:
            self.escape_me.emit()

    def __notify_text_cb(self, entry, pspec):
        if self.is_focus():
            self._palette.show()
            self._palette.set_filter(entry.props.text)
            self.grab_focus_without_selecting()

    def do_icon_press(self, position, event):
        self._show_palette()

    def _show_palette(self):
        self._palette.set_filter(None)
        self._palette.show()

    def __selected_cb(self, palette, sub):
        self.props.text = sub
        self.do_activate()

    def get_real_sub(self):
        sub = self.props.text
        return _clean_sub(sub)

    def do_activate(self):
        self.activate.emit(self.get_real_sub())
        self._palette.hide()


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


class _ListPalette(VScrollingPopover):
    '''
    A nice list of subreddits with headers for different sections
    '''

    selected = GObject.Signal('selected', arg_types=[str])
    
    def __init__(self, parent, **kwargs):
        VScrollingPopover.__init__(self, **kwargs)
        self._parent = parent
        self._filter = None

        get_reddit_api().subs_changed.connect(self.__changed_cb)
        get_reddit_api().user_changed.connect(self.__changed_cb)
        self._parent.connect('activate', self.__changed_cb)
        self._rebuild()

    def __changed_cb(self, caller, *args):
        self._rebuild()

    def set_filter(self, filter):
        if not filter:
            filter = None
        else:
            filter = _clean_sub(filter)
        self._filter = filter
        self._rebuild()

    def _do_filter(self, sub_list):
        if self._filter is None:
            # Flake8 says F999, but I don't care
            return sub_list

        for sub in sub_list:
            if sub.lower().startswith(self._filter.lower()):
                yield sub

    def _rebuild(self):
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_scrolled_child(self._box)
        self._box.show()

        self._add_subs(self._do_filter(PREPEND_SUBS))

        # Only show suggestions if it is /r/aaa, not /r/aaa/sort
        if self._filter and len(self._filter.split('/')) == 3:
            subs = list(self._do_filter(get_reddit_api().user_subs))
            if subs:
                self._add_header('Searching Subscribed')
                self._add_subs(subs)

        sub = self._filter or self._parent.get_real_sub() or ''
        if sub.startswith('/r/'):
            by_slash = sub.split('/')
            name = by_slash[2]  # get the /r/[thing]/whatever part
            if len(by_slash) == 4:  # /r/subreddit/top?=whatever
                sort = by_slash[3]
                if '?' in sort and len(sort.split('?')) == 2:
                    type, time = sort.split('?')
                    self._add_header('Sorting Times')
                    self._add_subs(('/r/{}/{}?t={}'.format(name, type, x)
                                    for x in SORTING_TIMES))

            self._add_header('Sorting')
            self._add_subs(('/r/{}/{}'.format(name, x) for x in SORTINGS))

        if not self._filter:
            self._add_header('Subscribed')
            self._add_subs(get_reddit_api().user_subs)

        user_name = None
        if self._filter is not None:
            if self._filter.startswith('/user'):
                user_name = self._filter.split('/')[2]
        else:
            user_name = get_reddit_api().user_name

        if user_name is not None:
            self._add_header('Profile')
            self._add_subs((x.replace('USER', user_name)
                           for x in SPECIAL_SUBS))

    def _add_header(self, header):
        l = Gtk.Label(xalign=0, justify=Gtk.Justification.LEFT)
        l.set_markup('<b>{}</b>'.format(header))
        self._box.add(l)
        l.show()

    def _add_subs(self, subs):
        for sub in subs:
            b = Gtk.Button(label=sub)
            b.get_style_context().add_class('flat')
            b.props.xalign = 0
            b.connect('clicked', self.__sub_button_clicked)
            self._box.add(b)
            b.show()

    def __sub_button_clicked(self, button):
        self.selected.emit(button.props.label)
