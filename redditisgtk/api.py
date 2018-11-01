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

import os
import re
import json
import time
import urllib.parse
import warnings
import typing

from gi.repository import Soup
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import GdkPixbuf

USER_AGENT = 'GNU:something-for-reddit:v0.2 (by /u/samtoday)'
PREPEND_SUBS = ['/r/all', '/inbox']
DEFAULT_SUBS = ['/r/gnome', '/r/gnu+linux']
SPECIAL_SUBS = [
    '/message/inbox', '/message/unread', '/message/sent',
    '/user/USER/overview', '/user/USER/submitted', '/user/USER/commented',
    '/user/USER/upvoted', '/user/USER/downvoted', '/user/USER/hidden',
    '/user/USER/saved', '/user/USER/gilded'
]
SORTINGS = [
    'hot', 'new', 'random', 'top?t=all', 'controversial?t=all'
]
SORTING_TIMES = [
    'hour', 'day', 'week', 'month', 'year', 'all'
]
DEBUG = 'REDDIT_IS_GTK_DEBUG' in os.environ


def is_special_sub(sub):
    for s in SPECIAL_SUBS:
        if s == sub or re.match(s.replace('USER', '.+'), sub):
            return True
    return False


# macro from
# https://developer.gnome.org/libsoup/stable/libsoup-2.4-soup-status.html#SOUP-STATUS-IS-TRANSPORT-ERROR:CAPS
def SOUP_STATUS_IS_TRANSPORT_ERROR(status):
    return 0 < status < 100

_SOME_SOUP_ERRORS = {
    Soup.Status.CANCELLED: 'WTF Message locally (THIS IS A BUG - REPORT IT)',
    Soup.Status.MALFORMED: 'Malformed data (Probably a bug, please report)',
    Soup.Status.CANT_RESOLVE: 'Can not resolve host name',
    Soup.Status.CANT_RESOLVE_PROXY: 'Can not resolve proxy host name',
    Soup.Status.CANT_CONNECT: 'Can not connect to the host',
    Soup.Status.CANT_CONNECT_PROXY: 'Can not connect to the proxy host',
    Soup.Status.IO_ERROR: 'IO Error (aka turn your WiFi back on)',
    Soup.Status.TOO_MANY_REDIRECTS: 'Too many redirects'
}


def describe_soup_transport_error(code, msg):
    start = 'General Transport Error ({})'.format(code)
    if code == Soup.Status.SSL_FAILED:
        start = 'TLS Error {}'.format(msg.props.tls_errors)
    if code in _SOME_SOUP_ERRORS:
        start = _SOME_SOUP_ERRORS[code]
    uri = msg.props.uri
    return '{}\n Message {} {}'.format(start, msg.props.method,
                                       uri.to_string(False))


class TokenManager(GObject.GObject):
    '''
    This class manages a single account token.
    '''

    value_changed = GObject.Signal('value-changed')
    user_name = None
    is_anonymous = False

    def __init__(self):
        super().__init__()

    def refresh(self, done_callback: typing.Callable[[], typing.Any]):
        '''
        Request a refresh of the token, if applicable to this type of account
        '''
        raise NotImplementedError()

    def wrap_path(self, path: str) -> str:
        '''
        Take a path and put the domain part in front of it
        '''
        raise NotImplementedError()

    def add_message_headers(self, msg: Soup.Message):
        '''
        Mutate the soup message and add any required headers to signify
        this token
        '''
        raise NotImplementedError()
    
    def serialize(self) -> dict:
        raise NotImplementedError()


class AnonymousTokenManager(TokenManager):
    user_name = 'Anonymous'
    is_anonymous = True

    def refresh(self, done_callback):
        done_callback()

    def wrap_path(self, path: str) -> str:
        return 'https://api.reddit.com' + path

    def add_message_headers(self, msg: Soup.Message):
        pass


class OAuthTokenManager(TokenManager):

    def __init__(
            self, session: Soup.Session,
            token: dict = None, code: str = None,
            ready_callback: typing.Callable[[], typing.Any] = None):
        super().__init__()
        self._token = token or {}
        self._session = session
        if code is not None:
            self._call_access_token(dict(
                code=code,
                grant_type='authorization_code',
                redirect_uri='redditgtk://done'),
                callback=ready_callback)
        else:
            if ready_callback is not None:
                ready_callback()

    def _call_access_token(self, data, callback=None):
        msg = Soup.Message.new(
            'POST', 'https://www.reddit.com/api/v1/access_token')
        msg.props.priority = Soup.MessagePriority.VERY_HIGH
        body = urllib.parse.urlencode(data)
        msg.set_request(
            'application/x-www-form-urlencoded',
            Soup.MemoryUse.COPY, bytes(body, 'utf8'))
        msg.props.request_headers.append(
            'Authorization', 'Basic V0NOM2pxb0oxLTByMFE6Cg==')

        self._session.queue_message(
            msg, self.__message_done_cb, callback)

    def __message_done_cb(self, session, msg, user_data):
        callback = user_data

        data = msg.props.response_body.data
        if data is None:
            # TODO:  Show this error to the user
            print('Token refresh failed')
            print(data,
                  msg.props.status_code,
                  describe_soup_transport_error(msg.props.status_code, msg))
            return

        # We must keep some things we only get the 1st time, eg.
        # the refresh token
        self._token.update(json.loads(data))
        self._token['time'] = time.time()

        self.value_changed.emit()

        if callback is not None:
            callback()

    def set_user_name(self, name: str):
        self._token['username'] = name
        self.value_changed.emit()

    @property
    def user_name(self):
        return self._token.get('username', '**loading username**')

    def refresh(self, done_callback):
        self._call_access_token(
            dict(
                grant_type='refresh_token',
                refresh_token=self._token['refresh_token'],
            ),
            callback=done_callback)

    def wrap_path(self, path: str) -> str:
        return 'https://oauth.reddit.com' + path

    def add_message_headers(self, msg: Soup.Message):
        token = self._token['access_token']
        msg.props.request_headers.append(
            'Authorization',
            'bearer {}'.format(token))

    def serialize(self):
        return self._token


class RedditAPI(GObject.GObject):

    subs_changed = GObject.Signal('subs-changed')
    user_changed = GObject.Signal('user-changed')
    user_subs = DEFAULT_SUBS
    lower_user_subs = [x.lower() for x in DEFAULT_SUBS]

    '''
    Emitted after request fail due to no network connection,
    reddit api error, etc.

    Args:
        msg (object):  message that failed to send, pass it to `resend_message`
            to send it again
        issue (str):  human description of the issue
    '''
    request_failed = GObject.Signal('request-failed', arg_types=[object, str])

    def __init__(self, session: Soup.Session, token: TokenManager):
        '''
        Args:
            session (Soup.Session): dependency
            token (TokenManager): token to use
        '''
        GObject.GObject.__init__(self)
        self._token = token

        self.session = session
        self.session.props.user_agent = USER_AGENT

        if self._token.is_anonymous:
            self.user_changed.emit()
            self.user_subs = DEFAULT_SUBS
            self.lower_user_subs = [x.lower() for x in self.user_subs]
            self.subs_changed.emit()
        else:
            self.update_subscriptions()
            self.send_request('GET', '/api/v1/me', self.__whoami_cb)

    @property
    def user_name(self):
        return self._token.user_name

    def __whoami_cb(self, msg):
        self._token.set_user_name(msg['name'])
        self.user_changed.emit()

    def update_subscriptions(self):
        '''Begin the process of checking what subs you're subscribed to'''
        self.send_request('GET', '/subreddits/mine/subscriber?limit=100',
                          self.__collect_subs_cb)

    def __collect_subs_cb(self, msg, subs=None):
        if subs is None:
            subs = []
        for sub in msg['data']['children']:
            subs.append(sub['data']['url'])

        if msg.get('after') is not None:
            self.send_request(
                'GET',
                ('/subreddits/mine/subscriber'
                 '?limit=100&after={}'.format(msg.get('after'))),
                self.__collect_subs_cb, user_data=subs)
        else:
            self.user_subs = subs
            self.lower_user_subs = [x.lower() for x in self.user_subs]
            self.subs_changed.emit()

    def resend_message(self, message):
        '''
        Resend a failed message

        Args:
            message (object):  what got emitted in the request-failed signal
        '''
        # Message is really just a tuple of arguments :)
        self.send_request(*message)

    def send_request(self, method, path, callback, post_data=None,
                     handle_errors=True, user_data=None):
        '''
        Send a request to the reddit api

        Args:
            method (str):  HTTP Method
            path (str):  path of the request to send to reddit, eg. '/r/linux'
            callback (function): function to take the data with the signature,
                callback(json_response) or callback(json_response, user_data)

        Kwargs:
            post_data (dict):  data to POST to the reddit api
            handle_errors (bool):  if True, reddit api errors will be processed
                automatically rather than going to the callback
            user_data (object):  user data to pass to the callback (optional)
        '''
        if DEBUG:
            print(method, path)
        using_oauth = self._token is not None
        my_args = (method, path, callback, post_data, handle_errors, user_data)

        if path[0] != '/':
            path = '/' + path
        msg = Soup.Message.new(method, self._token.wrap_path(path))
        if post_data is not None:
            msg.set_request(
                'application/x-www-form-urlencoded',
                Soup.MemoryUse.COPY,
                bytes(urllib.parse.urlencode(post_data), 'utf8'))
        self._token.add_message_headers(msg)
        self.session.queue_message(msg, self.__message_done_cb, my_args)
        return msg

    def __message_done_cb(self, session, msg, my_args):
        method, path, callback, post_data, handle_errors, user_data = my_args
        if DEBUG:
            print('> DONE', method, path)
        if msg.props.status_code == Soup.Status.CANCELLED:
            return
        if SOUP_STATUS_IS_TRANSPORT_ERROR(msg.props.status_code):
            self.request_failed.emit(
                my_args, describe_soup_transport_error(msg.props.status_code,
                                                       msg))
            return

        data = msg.props.response_body.flatten().get_data()
        if not data:
            self.request_failed.emit(
                my_args,
                'No response body, status {}'.format(msg.props.status_code))

        j = json.loads(str(data, 'utf8'))
        if ('error' in j) and handle_errors:
            if DEBUG:
                print(j)
            if j['error'] == 401:
                def callback():
                    self.resend_message(my_args)
                self._token.refresh(callback)
                return

            self.request_failed.emit(
                my_args, 'Reddit Error: {}'.format(j['error']))
            return

        if callback is not None:
            if user_data is not None:
                callback(j, user_data)
            else:
                callback(j)

    def get_subreddit_info(self, subreddit_name, callback):
        '''
        Args:
            subreddit_name (str):  name like 'linux' or 'gnu',
                NOT with the /r/
            callback (def(json_decoded_data))
        '''
        return self.send_request(
            'GET', '/r/{}/about'.format(subreddit_name), callback)

    def get_user_info(self, name, callback):
        '''
        Args:
            name (str):  name like 'person', or 'samtoday'
            callback (def(json_decoded_data))
        '''
        return self.send_request(
            'GET', '/user/{}/about'.format(name), callback)

    def get_list(self, sub, callback):
        '''
        Get a list of posts from a subreddit, formatted like:

            /r/gnome
            /r/all
            /r/frontpage
            /r/funny  (note the implicit boolean NOT operator)
        '''
        return self.send_request('GET', sub, callback)

    def vote(self, thing_id, direction):
        return self.send_request('POST', '/api/vote', None,
                                 post_data={'id': thing_id, 'dir': direction})

    def set_subscribed(self, subreddit_name, subscribed, callback):
        '''
        Args:
            subreddit_name (str):  name like 'linux' or 'gnu',
                NOT with the /r/
            subscribed (bool):  value to set
            callback (def(json_decoded_data))
        '''
        action = 'sub' if subscribed else 'unsub'
        return self.send_request(
            'POST', '/api/subscribe', callback,
            post_data={'sr_name': subreddit_name, 'action': action})

    def reply(self, thing_id, text, callback):
        return self.send_request('POST', '/api/comment', callback,
                                 post_data={'thing_id': thing_id,
                                            'text': text,
                                            'api_type': 'json'})

    def set_saved(self, thing_id, new_value, callback):
        uri = '/api/save' if new_value else '/api/unsave'
        return self.send_request('POST', uri, callback,
                                 post_data={'id': thing_id})

    def submit(self, data, callback):
        data['api_type'] = 'json'
        return self.send_request('POST', '/api/submit', callback,
                                 post_data=data, handle_errors=False)

    def cancel(self, message):
        self.session.cancel_message(message, Soup.Status.CANCELLED)

    def read_message(self, name):
        return self.send_request('POST', '/api/read_message', None,
                                 post_data={'id': name})

    def load_more(self, link_name, more_children, callback):
        '''
        Args:
            link_name (str):  fullname of the link
            more_children (dict):  more comments object reddit gave you
            callback (func):  same kind of callback as rest of api
        '''
        data = urllib.parse.urlencode({
            'api_type': 'json',
            'children': ','.join(more_children['children']),
            'link_id': link_name
        })
        return self.send_request('GET', '/api/morechildren?' + data,
                                 self.__load_more_cb, user_data=callback)

    def __load_more_cb(self, data, callback):
        '''
        Ok, so reddit here returns the comments as a list, rather than being
        nested like normally.  This is really annoying.  Since it is such
        a special case, we will fix up the data here and the view code
        can assume that it is normal data.

        We need to connect the comments via their 'parent_id'->'name'.  We
        also know that the list will be sorted.  So basically, we make a stack
        which stores the last comment we added.  Then:

        * If the parent_id matches the top of the stack's name, add it in
            (and add myself to the top of the stack)
        * Otherwise, remove the top of the stack and retry step #1
        * If we reach the bottom of the stack, just add a root level comment
            (and of course add myself to the top of the stack)
        '''
        comments = data['json']['data']['things']
        new_comments = []
        stack = [None]

        for c in comments:
            while True:
                top = stack[-1]
                if top is None:
                    new_comments.append(c)
                    stack.append(new_comments[-1])
                    # print('Adding to end')
                    break
                if top['data']['name'] == c['data']['parent_id']:
                    # Why don't you use null reddit???
                    if top['data']['replies'] == '':
                        top['data']['replies'] = \
                            {'data': {'children': []}}
                    kids = top['data']['replies']['data']['children']
                    kids.append(c)
                    stack.append(kids[-1])
                    # print('Adding as child')
                    break
                else:
                    stack.pop(-1)
                    # print('Popping stack')
        callback(new_comments)

    def download_thumb(self, url, callback):
        '''
        Args:
            url (str)
            callback (function) - takes Gtk.Pixbuf
        '''
        msg = Soup.Message.new('GET', url)
        msg.props.priority = Soup.MessagePriority.LOW
        return self.session.queue_message(msg, self.__dl_thumb_cb, callback)

    def __dl_thumb_cb(self, session, msg, callback):
        pbl = GdkPixbuf.PixbufLoader()
        try:
            pbl.write(msg.props.response_body.flatten().get_data())
        except GLib.Error as e:
            print(e)
            pass
        pbl.close()
        callback(pbl.get_pixbuf())


class APIFactory(GObject.GObject):
    '''
    Get an api given a token

    Given the same token, the api will be the same
    '''

    def __init__(self, session: Soup.Session):
        super().__init__()
        self._session = session
        self._apis = {}

    def get_for_token(self, token: TokenManager) -> RedditAPI:
        if token not in self._apis:
            self._apis[token] = RedditAPI(self._session, token)
        return self._apis[token]
