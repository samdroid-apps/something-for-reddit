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
from gi.repository import GObject

from redditisgtk.api import get_reddit_api


class SubmitWindow(GObject.GObject):

    done = GObject.Signal('done', arg_types=[str, str])

    def __init__(self, sub=''):
        GObject.GObject.__init__(self)

        self._b = Gtk.Builder.new_from_resource(
            '/today/sam/reddit-is-gtk/submit-window.ui')
        self._window = self._b.get_object('submit-window')

        self._b.get_object('sub-entry').props.text = sub
        self._b.get_object('submit-button').connect(
            'clicked', self.__submit_clicked_cb)

    def show(self):
        self._window.show()

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
            data['kind'] = 'link'
            buf = self._b.get_object('self-textview').props.buffer
            data['text'] = buf.get_text(buf.get_start_iter(),
                                        buf.get_end_iter(), False)
        get_reddit_api().submit(data, self.__submit_done_cb)

    def __submit_done_cb(self, data):
        # This response is the most dumb thing for an api I have ever seen.
        # It would be better if they put it in a bloody pdf document than
        # this weird thing.
        jquery = data['jquery']
        # It seems to be instructions for jquery, so hijack those to find
        # it it tells jquery to set an error text
        current_attr = None
        in_error = False
        error_text = None
        uri = None
        for i, i_plus_one, action, args in jquery:
            if action == 'attr':
                current_attr = args
            elif action == 'call':
                if current_attr == 'find' and '.error' in args[0]:
                    in_error = True
                elif in_error and current_attr == 'text':
                    error_text = args[0]
                    break
                elif current_attr == 'redirect':
                    uri = args[0]
                    if 'already_submitted=true' not in uri:
                        # Because for 1 error message they have a redirect :'(
                        break

        if error_text is not None:
            error = self._b.get_object('error-label')
            error.props.label = error_text
            error.show()

            submit = self._b.get_object('submit-button')
            submit.props.sensitive = True
            submit.props.label = 'Submit'
        elif uri is not None:
            self.done.emit(self._b.get_object('sub-entry').props.text,
                           uri)
            self._window.hide()
            self._window.destroy()
