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
from gi.repository import GLib
from gi.repository import Soup
from gi.repository import WebKit2
from gi.repository import GObject

import os
import json
import time
import urllib.parse
from uuid import uuid4

from redditisgtk.readcontroller import get_data_file_path


class IdentityController(GObject.GObject):

    sign_in_status = GObject.Signal('sign-in-status', arg_types=[str, bool])
    token_changed = GObject.Signal('token-changed', arg_types=[object])

    def __init__(self):
        GObject.GObject.__init__(self)
        self._active = None
        self._tokens = {}
        # Stop recursive imports
        GLib.idle_add(self.load)

    def load(self):
        if os.path.isfile(get_data_file_path('identity')):
            with open(get_data_file_path('identity')) as f:
                j = json.load(f)
                self._tokens = j['tokens']
                self._active = j['active']
        self.token_changed.emit(None)
        if self._active is not None:
            self._refresh_token(self._active)

    def save(self):
        with open(get_data_file_path('identity'), 'w') as f:
            json.dump({'tokens': self._tokens,
                       'active': self._active}, f)

    def loop_names_ids_tuple(self):
        for id, data in self._tokens.items():
            yield data.get('username', '_wait_'), id

    def get_active(self):
        return self._active

    def get_token(self, id):
        return self._tokens[id]

    def switch_account(self, id):
        if self._active == id:
            return

        self._active = id
        if self._active is not None:
            self._refresh_token(self._active)
        else:
            self.token_changed.emit(None)
        self.save()

    def remove_account(self, id):
        if self._active == id:
            self._active = None
        del self._tokens[id]
        if self._active is not None:
            self.token_changed.emit(self._tokens[self._active])
        else:
            self.token_changed.emit(None)

    def sign_in_got_code(self, code, callback):
        id = str(uuid4())
        self._active = id
        self._call_access_token(dict(
            code=code,
            grant_type='authorization_code',
            redirect_uri='redditgtk://done'),
            id, callback=callback)

    def _refresh_token(self, id):
        self._call_access_token(dict(
            grant_type='refresh_token',
            refresh_token=self._tokens[id]['refresh_token']),
            id)

    def _call_access_token(self, data, id, callback=None):
        msg = Soup.Message.new(
            'POST', 'https://www.reddit.com/api/v1/access_token')
        msg.props.priority = Soup.MessagePriority.VERY_HIGH
        body = urllib.parse.urlencode(data)
        msg.set_request(
            'application/x-www-form-urlencoded',
            Soup.MemoryUse.COPY, bytes(body, 'utf8'))
        msg.props.request_headers.append(
            'Authorization', 'Basic V0NOM2pxb0oxLTByMFE6Cg==')

        # api imports us, so we must wait to import them
        from redditisgtk.api import get_reddit_api
        get_reddit_api().session.queue_message(
            msg, self.__message_done_cb, (id, callback))

    def __message_done_cb(self, session, msg, user_data):
        id, callback = user_data

        data = msg.props.response_body.data
        if id not in self._tokens:
            self._tokens[id] = {}
        # We must keep some things we only get the 1st time, eg.
        # the refresh token
        from redditisgtk.api import describe_soup_transport_error
        print(data, msg.props.status_code, describe_soup_transport_error(msg.props.status_code, msg))
        self._tokens[id].update(json.loads(data))
        self._tokens[id]['time'] = time.time()

        self.save()
        self.token_changed.emit(self._tokens[id])
        self.sign_in_status.emit('', True)

        if callback is not None:
            callback()

        if 'username' not in self._tokens[id]:
            # api imports us, so we must wait to import them
            from redditisgtk.api import get_reddit_api
            get_reddit_api().send_request(
                'GET', '/api/v1/me', self.__whoami_cb, user_data=id)

    def __whoami_cb(self, msg, id):
        self._tokens[id]['username'] = msg['name']
        self.save()
        self.token_changed.emit(self._tokens[id])


_id_ctrl = None
def get_identity_controller():
    global _id_ctrl
    if _id_ctrl is None:
        _id_ctrl = IdentityController()
    return _id_ctrl



class SignInWindow(Gtk.Window):

    got_code = GObject.Signal('got-code', arg_types=[object])
    error = GObject.Signal('error', arg_types=[str])

    def __init__(self):
        Gtk.Window.__init__(self)
        self.set_default_size(400, 400)
        self.set_title('Sign into Reddit')
        self._state = str(uuid4())

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
            ctrl = get_identity_controller()
            ctrl.sign_in_got_code(d['code'][0], self.__done_cb)
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


class IdentityButton(Gtk.MenuButton):
    def __init__(self):
        Gtk.MenuButton.__init__(self, popover=IdentityPopover())
        self.__token_cb(get_identity_controller(), None)
        get_identity_controller().token_changed.connect(self.__token_cb)

    def __token_cb(self, ctrl, token):
        if ctrl.get_active() is None:
            self.props.label = 'Anonymous'
        else:
            token = ctrl.get_token(ctrl.get_active())
            self.props.label = token.get('username', '...')


class IdentityPopover(Gtk.Popover):
    def __init__(self):
        Gtk.Popover.__init__(self)
        self.__token_cb(get_identity_controller(), None)
        get_identity_controller().token_changed.connect(self.__token_cb)

    def __token_cb(self, ctrl, token):
        if self.get_child() is not None:
            c = self.get_child()
            self.remove(c)
            c.destroy()

        listbox = Gtk.ListBox()
        self.add(listbox)
        listbox.show()

        anon = _AccountRow(None, 'Anonymous', removeable=False)
        listbox.add(anon)
        anon.show()
        if ctrl.get_active() is None:
            listbox.select_row(anon)

        for name, id in ctrl.loop_names_ids_tuple():
            row = _AccountRow(id, name)
            listbox.add(row)
            row.show()
            if id == ctrl.get_active():
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
        w = SignInWindow()
        w.show()

    def __row_selected_cb(self, listbox, row):
        if row is not None:
            get_identity_controller().switch_account(row.id)
            return True


class _AccountRow(Gtk.ListBoxRow):
    def __init__(self, id, name, removeable=True):
        Gtk.ListBoxRow.__init__(self)
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
        get_identity_controller().remove_account(self.id)
