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
from gi.repository import GObject

from redditisgtk.api import (RedditAPI, PREPEND_SUBS,
                             SPECIAL_SUBS, SORTING_TIMES)


SORTINGS = [
    'hot', 'new', 'random', 'top?t=all', 'controversial?t=all'
]

def clean_sub(sub):
    '''
    Normalize paths to have a leading slash and no trailing slash, like
        /hello/world

    And normalize /u/ -> /user/
    '''
    if sub.startswith('http://') or sub.startswith('https://'):
        return sub

    if sub.endswith('/'):
        sub = sub[:-1]
    if not sub.startswith('/'):
        sub = '/' + sub

    if sub.startswith('/u/'):
        sub = '/user/' + sub[len('/u/'):]

    return sub


def format_sub_for_api(sub):
    sub = clean_sub(sub)
    empty, *parts = sub.split('/')

    if len(parts) == 2 and parts[0] == 'user':  # /user/name
        parts.append('overview')

    if len(parts) == 2 and parts[0] == 'r': # /r/name
        parts.append('hot')
    if len(parts) == 1 and not parts[0]: # / --> /hot
        parts[0] = 'hot'

    return '/' + '/'.join(parts)


class SubEntry(Gtk.Box):
    '''
    The thing that goes in the middle of the header bar, and
    shows the current subreddit
    '''

    activate = GObject.Signal('reddit-activate', arg_types=[str])
    escape_me = GObject.Signal('escape-me')

    def __init__(self, api: RedditAPI, text='/r/all'):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)
        self.get_style_context().add_class('linked')

        self._entry = Gtk.Entry(text=text)
        self._entry.connect('event', self.__event_cb)
        self._entry.connect('changed', self.__changed_cb)
        self._entry.connect('activate', self.__activate_cb)
        self._entry.connect('focus-in-event', self.__focus_in_event_cb)
        self._entry.connect('focus-out-event', self.__focus_out_event_cb)
        self._entry.set_size_request(300, 0)
        self.add(self._entry)
        self._entry.show()

        self._palette = _ListPalette(api, self)
        self._palette.selected.connect(self.__selected_cb)

        show_palette = Gtk.MenuButton(popover=self._palette)
        show_palette.connect('toggled', self.__show_palette_toggled_cb)
        self.add(show_palette)
        show_palette.show()

    def focus(self):
        self._entry.grab_focus()

    # When the entry is unfocused, we should make the popover behave in a
    # normal way.  When it is focused, we make it not modal so that it can
    # behave as a suggestions list
    def __focus_in_event_cb(self, entry, event):
        self._palette.props.modal = False

    def __focus_out_event_cb(self, entry, event):
        self._palette.props.modal = True

    def __event_cb(self, entry, event):
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

    def __changed_cb(self, entry):
        if entry.is_focus():
            self._palette.popup()
            self._palette.set_filter(self.current_location)
            entry.grab_focus_without_selecting()

    def __show_palette_toggled_cb(self, button):
        if button.props.active:
            # When the user clicks on the button, ensure the palette is empty
            self._palette.set_filter(None)

    def _show_palette(self):
        self._palette.set_filter(None)
        self._palette.popup()

    def __selected_cb(self, palette, sub):
        self._entry.props.text = sub
        self.__activate_cb()

    def goto(self, sub):
        self._entry.props.text = sub

    @property
    def current_location(self):
        return clean_sub(self._entry.props.text)

    def __activate_cb(self, entry=None):
        text = self._entry.props.text
        if text.startswith('http://') or text.startswith('https://'):
            self.get_toplevel().goto_reddit_uri(text)
        else:
            formatted = format_sub_for_api(self._entry.props.text)
            self.activate.emit(formatted)
        self._palette.popdown()

        # If we don't override the selection, the whole text will be selected
        # This is confusing - as it makes the entry look :focused
        p = len(self._entry.props.text)
        self._entry.select_region(p, p)


class VScrollingPopover(Gtk.Popover):

    def __init__(self, **kwargs):
        Gtk.Popover.__init__(self, vexpand=True, **kwargs)
        self._sw = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER)
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

    def __init__(self, api: RedditAPI, parent, **kwargs):
        VScrollingPopover.__init__(self, **kwargs)
        self.get_style_context().add_class('subentry-palette')
        self._parent = parent
        self._filter = None

        self._api = api
        self._api.subs_changed.connect(self.__changed_cb)
        self._api.user_changed.connect(self.__changed_cb)
        self._rebuild()

    def __changed_cb(self, caller, *args):
        self._rebuild()

    def set_filter(self, filter):
        if filter is not None:
            if filter.startswith('https://') or filter.startswith('http://'):
                self._show_open_uri(filter)
                return

        if not filter:
            filter = None
        else:
            filter = clean_sub(filter)
        self._filter = filter
        self._rebuild()

    def _do_filter(self, sub_list):
        if self._filter is None:
            yield from sub_list
            return

        for sub in sub_list:
            if sub.lower().startswith(self._filter.lower()):
                yield sub

    def _show_open_uri(self, uri):
        button = Gtk.Button(label='Open this reddit.com URI')
        button.connect('clicked', self.__open_reddit_uri_cb, uri)
        self.set_scrolled_child(button)
        button.show()

    def __open_reddit_uri_cb(self, button, uri):
        self.get_toplevel().goto_reddit_uri(uri)
        self.hide()

    def _rebuild(self):
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_scrolled_child(self._box)
        self._box.show()

        self._add_subs(self._do_filter(PREPEND_SUBS))

        # If the user is typing for a subreddit, show them suggestions
        if self._filter:
            empty, *filter_parts = self._filter.split('/')
            # Only show suggestions if it is /r/aaa, not /r/aaa/sort
            if filter_parts[0] in ('', 'r') and len(filter_parts) <= 2:
                subs = list(self._do_filter(self._api.user_subs))
                if subs:
                    self._add_header('Searching Subscribed')
                    self._add_subs(subs)

        # Show sorting suggestions
        current_location = self._parent.current_location
        if current_location.startswith('/r/'):
            by_slash = current_location.split('/')
            name = by_slash[2]  # get the /r/[thing]/whatever part

            self._add_header('Sorting')
            self._add_subs([
                '/r/{}/{}'.format(name, x)
                for x in ['hot', 'new', 'random']
            ])
            for x in ['top', 'controversial']:
                self._add_expander_sub('/r/{}/{}'.format(name, x))

        # If there is no filter, show the subscribed subreddits
        if not self._filter:
            self._add_header('Subscribed')
            self._add_subs(self._api.user_subs)

        # Show user related stuff last
        # This should end up first if you are typing /u/...
        user_name = None
        if self._filter is not None:
            empty, *filter_parts = self._filter.split('/')
            if self._filter.startswith('/user'):
                user_name = self._filter.split('/')[2]
        else:
            user_name = self._api.user_name

        if user_name is not None:
            self._add_header('Profile')
            self._add_subs((x.replace('USER', user_name)
                            for x in SPECIAL_SUBS))

    def _add_header(self, header):
        l = Gtk.Label(xalign=0, justify=Gtk.Justification.LEFT)
        l.get_style_context().add_class('header')
        l.set_markup('<b>{}</b>'.format(header))
        self._box.add(l)
        l.show()

    def _add_subs(self, subs, to=None):
        for sub in subs:
            b = Gtk.Button(label=sub, xalign=0)
            b.get_style_context().add_class('full-width')
            b.connect('clicked', self.__sub_button_clicked)
            if to is None:
                self._box.add(b)
            else:
                to.add(b)
            b.show()

    def __sub_button_clicked(self, button):
        self.selected.emit(button.props.label)

    def _add_expander_sub(self, sub):
        btn = Gtk.ToggleButton(label=sub, xalign=0)
        btn.get_style_context().add_class('full-width')

        revealer = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        revealer.add(box)

        self._add_subs(('{}?t={}'.format(sub, x) for x in SORTING_TIMES),
                       to=box)

        btn.connect('toggled', self.__sub_expander_toggled_cb, revealer)

        self._box.add(btn)
        self._box.add(revealer)
        btn.show()
        revealer.show()
        box.show()

    def __sub_expander_toggled_cb(self, button, revealer):
        revealer.props.reveal_child = button.props.active
