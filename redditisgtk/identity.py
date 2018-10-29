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
from gi.repository import GLib
from gi.repository import Soup
from gi.repository import WebKit2
from gi.repository import GObject

import os
import json
import urllib.parse
from uuid import uuid4

from redditisgtk.readcontroller import get_data_file_path
from redditisgtk.api import (AnonymousTokenManager, OAuthTokenManager,
                             TokenManager)


class IdentityController(GObject.GObject):

    token_changed = GObject.Signal('token-changed', arg_types=[])

    def __init__(self, session: Soup.Session):
        super().__init__()

        self._session = session
        self._active = None
        self._tokens = {}
        self._anon = AnonymousTokenManager()

        self.load()

    @property
    def active_token(self) -> TokenManager:
        if self._active is None:
            return self._anon
        else:
            return self._tokens[self._active]

    def load(self):
        if os.path.isfile(get_data_file_path('identity')):
            with open(get_data_file_path('identity')) as f:
                j = json.load(f)

                self._tokens = {}
                for id_, data in j['tokens'].items():
                    token  = OAuthTokenManager(
                            self._session,
                            token=data,
                    )
                    token.value_changed.connect(self._token_value_changed_cb)
                    self._tokens[id_] = token
                self._active = j['active']

        self.token_changed.emit()

    def _token_value_changed_cb(self, token):
        if token == self.active_token:
            self.token_changed.emit()
        self.save()

    def save(self):
        with open(get_data_file_path('identity'), 'w') as f:
            json.dump({
                'tokens': \
                    {k: v.serialize() for k, v in self._tokens.items()},
               'active': self._active,
            }, f)

    @property
    def all_tokens(self):
        yield from self._tokens.items()

    def switch_account(self, id):
        if self._active == id:
            return

        self._active = id
        if self._active is not None:
            self._tokens[self._active].refresh(lambda: self.token_changed.emit())
        else:
            self.token_changed.emit()
        self.save()

    def remove_account(self, id):
        if self._active == id:
            self._active = None
        del self._tokens[id]
        self.token_changed.emit()

    def sign_in_got_code(self, code, callback):
        id = str(uuid4())

        def done_cb():
            self._active = id
            self.token_changed.emit()
            callback()

        self._tokens[id] = OAuthTokenManager(
                self._session,
                code=code,
                ready_callback=done_cb)
        self._tokens[id].value_changed.connect(self._token_value_changed_cb)
