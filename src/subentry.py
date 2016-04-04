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

from redditisgtk.api import get_reddit_api, PREPEND_SUBS, is_special_sub, \
                            SORTINGS, SPECIAL_SUBS


class SubEntry(Gtk.Entry):
    '''
    The thing that goes in the middle of the header bar, and
    shows the current subreddit
    '''

    activate = GObject.Signal('reddit-activate', arg_types=[str])

    def __init__(self):
        Gtk.Entry.__init__(
            self,
            text='/r/all',
            secondary_icon_name='go-down-symbolic',
            secondary_icon_sensitive=True,
            secondary_icon_tooltip_text='View List'
        )
        self.set_size_request(400, 0)
        self._palette = None

        # FIXME:  There is no do_icon_press by gobject
        self.connect('icon-press', SubEntry.do_icon_press)

    def do_event(self, event):
        if event.type != Gdk.EventType.KEY_PRESS:
            return
        if event.keyval == Gdk.KEY_Down:
            self._show_palette()

    def do_icon_press(self, position, event):
        self._show_palette()

    def _show_palette(self):
        if self._palette is None:
            self._palette = _ListPalette(self, relative_to=self)
            self._palette.selected.connect(self.__selected_cb)
            self._palette.show()
        else:
            self._palette.hide()
            self._palette.destroy()
            self._palette = None

    def __selected_cb(self, palette, sub):
        self.props.text = sub
        self.do_activate()

        self._palette.hide()
        self._palette.destroy()
        self._palette = None

    def get_real_sub(self):
        sub = self.props.text
        if sub.endswith('/'):
            sub = sub[:-1]
        if not sub.startswith('/'):
            sub = '/' + sub
        if sub.startswith('/u/'):
            sub = '/user/' + sub[len('/u/'):]
            if len(sub.split('/')) == 3: # []/[user]/[name]
                sub = sub + '/overview'
        if sub == '/inbox':
            sub = '/message/inbox'
        if not is_special_sub(sub):
            if not sub.startswith('/r/'):
                sub = '/r' + sub
        return sub

    def do_activate(self):
        self.activate.emit(self.get_real_sub())


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

        get_reddit_api().subs_changed.connect(self.__changed_cb)
        get_reddit_api().user_changed.connect(self.__changed_cb)
        self._parent.connect('activate', self.__changed_cb)
        self._rebuild()

    def __changed_cb(self, caller, *args):
        self._rebuild()

    def _rebuild(self):
        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_scrolled_child(self._box)
        self._box.show()

        self._add_subs(PREPEND_SUBS, first=True)

        sub = self._parent.get_real_sub()
        if sub.startswith('/r/'):
            name = sub.split('/')[2]  # get the /r/[thing]/whatever part
            self._add_header('Sorting')
            self._add_subs(('/r/{}/{}'.format(name, x) for x in SORTINGS))

        self._add_header('Subscribed')
        self._add_subs(get_reddit_api().user_subs)

        
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

    def _add_subs(self, subs, first=True):
        for sub in subs:
            b = Gtk.Button(label=sub)
            if first:
                b.grab_focus()
                first = False
            b.get_style_context().add_class('flat')
            b.props.xalign = 0
            b.connect('clicked', self.__sub_button_clicked)
            self._box.add(b)
            b.show()

    def __sub_button_clicked(self, button):
        self.selected.emit(button.props.label)
