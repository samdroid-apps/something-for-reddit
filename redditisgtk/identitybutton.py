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

import urllib.parse
from uuid import uuid4

from gi.repository import Gtk
from gi.repository import WebKit2

from redditisgtk.identity import IdentityController


class IdentityButton(Gtk.MenuButton):

    def __init__(self, ic: IdentityController):
        Gtk.MenuButton.__init__(self, popover=_IdentityPopover(ic))
        self.__token_cb(ic)
        ic.token_changed.connect(self.__token_cb)

    def __token_cb(self, ctrl):
        token = ctrl.active_token
        self.props.label = token.user_name


class _IdentityPopover(Gtk.Popover):

    def __init__(self, ic: IdentityController):
        Gtk.Popover.__init__(self)
        self.__token_cb(ic)
        ic.token_changed.connect(self.__token_cb)
        self._ic = ic

    def __token_cb(self, ctrl):
        if self.get_child() is not None:
            c = self.get_child()
            self.remove(c)
            c.destroy()

        listbox = Gtk.ListBox()
        self.add(listbox)
        listbox.show()

        anon = _AccountRow(ctrl, None, 'Anonymous', removeable=False)
        listbox.add(anon)
        anon.show()
        if ctrl.active_token.is_anonymous:
            listbox.select_row(anon)

        for id, token in ctrl.all_tokens:
            row = _AccountRow(ctrl, id, token.user_name)
            listbox.add(row)
            row.show()
            if token == ctrl.active_token:
                listbox.select_row(row)

        add = Gtk.Button(label='Add new account',
                         always_show_image=True)
        add.connect('clicked', self.__add_clicked_cb)
        add.add(Gtk.Image.new_from_icon_name(
            'list-add-symbolic', Gtk.IconSize.MENU))
        add.get_style_context().add_class('flat')
        listbox.add(add)
        add.show()

        listbox.connect('row-selected', self.__row_selected_cb)

    def __add_clicked_cb(self, button):
        w = SignInWindow(self._ic)
        w.show()

    def __row_selected_cb(self, listbox, row):
        if row is not None:
            self._ic.switch_account(row.id)
            return True


class _AccountRow(Gtk.ListBoxRow):

    def __init__(self, ic, id, name, removeable=True):
        Gtk.ListBoxRow.__init__(self)
        self._ic = ic
        self.id = id
        self.name = name

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(box)
        box.add(Gtk.Label(label=name))

        if removeable:
            remove = Gtk.Button()
            remove.connect('clicked', self.__remove_cb)
            remove.get_style_context().add_class('flat')
            remove.add(Gtk.Image.new_from_icon_name(
                'edit-delete-symbolic', Gtk.IconSize.MENU))
            box.pack_end(remove, False, False, 0)
        self.show_all()

    def __remove_cb(self, button):
        self._ic.remove_account(self.id)


class SignInWindow(Gtk.Window):

    def __init__(self, ic: IdentityController):
        Gtk.Window.__init__(self)
        self.set_default_size(400, 400)
        self.set_title('Sign into Reddit')
        self._state = str(uuid4())
        self._ic = ic

        ctx = WebKit2.WebContext.get_default()
        ctx.register_uri_scheme('redditgtk', self.__uri_scheme_cb)

        self._web = WebKit2.WebView()
        self._web.load_uri(
            'https://www.reddit.com/api/v1/authorize.compact?{end}'.format(
                end=urllib.parse.urlencode(dict(
                    redirect_uri='redditgtk://done',
                    state=self._state,
                    client_id='WCN3jqoJ1-0r0Q',
                    response_type='code',
                    duration='permanent',
                    scope=('edit history identity mysubreddits privatemessages'
                           ' submit subscribe vote read save')))
            ))
        self.add(self._web)
        self.show_all()

    def __uri_scheme_cb(self, request):
        uri = urllib.parse.urlparse(request.get_uri())
        d = urllib.parse.parse_qs(uri.query)

        self._show_label()

        if d['state'][0] != self._state:
            self._label.set_markup(
                'Reddit did not return the same state in OAuth flow')
            self._close.show()
            return

        if d.get('code'):
            self._ic.sign_in_got_code(d['code'][0], self.__done_cb)
            self._label.set_markup('Going down the OAuth flow')
            self._spinner.show()
        else:
            self._label.set_markup(
                'Reddit OAuth Error {}'.format(d['error']))
            self._close.show()

    def __done_cb(self):
        self.destroy()

    def _show_label(self):
        self._web.hide()
        self.remove(self._web)
        self._web.destroy()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box)
        box.show()
        self._label = Gtk.Label()
        box.add(self._label)
        self._label.show()
        self._spinner = Gtk.Spinner()
        box.add(self._spinner)

        self._close = Gtk.Button(label='Close')
        self._close.get_style_context().add_class('primary-action')
        self._close.connect('clicked', self.destroy)
        box.add(self._close)
