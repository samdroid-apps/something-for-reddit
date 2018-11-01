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
from gi.repository import GObject

from redditisgtk.api import RedditAPI


class SubmitWindow(GObject.GObject):

    done = GObject.Signal('done', arg_types=[str, str])

    def __init__(self, api: RedditAPI, sub=''):
        GObject.GObject.__init__(self)
        self._api = api

        self._b = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/submit-window.ui')
        self.window = self._b.get_object('submit-window')

        self._b.get_object('sub-entry').props.text = sub
        self._b.get_object('submit-button').connect(
            'clicked', self.__submit_clicked_cb)

    def show(self):
        self.window.show()

    def __submit_clicked_cb(self, button):
        submit = self._b.get_object('submit-button')
        submit.props.label = 'Submitting...'
        submit.props.sensitive = False

        data = {'title': self._b.get_object('title-entry').props.text,
                'sr': self._b.get_object('sub-entry').props.text}
        stack = self._b.get_object('link-self-stack')
        if stack.props.visible_child_name == 'link':
            data['kind'] = 'link'
            data['url'] = self._b.get_object('link-entry').props.text
        else:
            data['kind'] = 'self'
            buf = self._b.get_object('self-textview').props.buffer
            data['text'] = buf.get_text(buf.get_start_iter(),
                                        buf.get_end_iter(), False)
        self._api.submit(data, self.__submit_done_cb)

    def __submit_done_cb(self, data):
        data = data['json']
        if data.get('errors'):
            errors = data['errors']
            error_name, error_text, error_name_lower = errors[0]

            error = self._b.get_object('error-label')
            error.props.label = error_text
            error.show()

            submit = self._b.get_object('submit-button')
            submit.props.sensitive = True
            submit.props.label = 'Submit'
        else:
            uri = data['data']['url']
            self.done.emit(self._b.get_object('sub-entry').props.text,
                           uri)
            self.window.hide()
            self.window.destroy()
