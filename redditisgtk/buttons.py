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

import arrow
from gi.repository import Gtk

from redditisgtk.palettebutton import connect_palette
from redditisgtk.markdownpango import SaneLabel
from redditisgtk.api import RedditAPI

'''
So you come here and you ask, why are these ButtonBehaviours rather
than simple Gtk.Button subclasses?  The answer is simple: we make
the uis via Gtk.Builder, and I can't seem to get Gtk.Builder.expose_object
to work from python.  Also, if we use custom widgets, it will annoy
Glade probably.
'''


class ScoreButtonBehaviour():

    def __init__(self, api: RedditAPI, button, data):
        self._api = api
        self._button = button
        self._data = data
        self._p = connect_palette(button, self._make_score_palette)
        self._update_score_button()

    def _make_score_palette(self):
        bb = Gtk.ButtonBox(orientation=Gtk.Orientation.VERTICAL,
                           layout_style=Gtk.ButtonBoxStyle.EXPAND)
        upvote = Gtk.RadioToolButton(label='⇧')
        upvote.get_style_context().add_class('upvote')
        bb.add(upvote)
        novote = Gtk.RadioToolButton(label='○', group=upvote)
        bb.add(novote)
        downvote = Gtk.RadioToolButton(label='⇩', group=upvote)
        downvote.get_style_context().add_class('downvote')
        bb.add(downvote)
        bb.show_all()

        if self._data.get('likes') is True:
            upvote.props.active = True
        elif self._data.get('likes') is False:
            downvote.props.active = True
        else:
            novote.props.active = True

        upvote.connect('toggled', self.__vote_toggled_cb, +1)
        novote.connect('toggled', self.__vote_toggled_cb, 0)
        downvote.connect('toggled', self.__vote_toggled_cb, -1)

        palette = Gtk.Popover()
        palette.add(bb)
        return palette

    def vote(self, direction):
        self._api.vote(self._data['name'], direction)

        new_score = self._data['score'] + direction
        if self._data['likes'] is True:
            new_score -= 1  # Undo the previous like
        elif self._data['likes'] is False:
            new_score += 1
        if direction == 0:
            likes = None
        elif direction == +1:
            likes = True
        elif direction == -1:
            likes = False

        self._data['likes'] = likes
        self._data['score'] = new_score
        self._update_score_button()

    def __vote_toggled_cb(self, toggle, direction):
        if toggle.props.active:
            self.vote(direction)

    def _update_score_button(self):
        score = self._data['score']
        likes = self._data['likes']
        hidden = self._data.get('score_hidden')

        score_string = 'score hidden' if hidden else '{} points'.format(score)
        self._button.props.label = score_string

        ctx = self._button.get_style_context()
        ctx.remove_class('upvoted')
        ctx.remove_class('downvoted')
        if likes is True:
            ctx.add_class('upvoted')
        elif likes is False:
            ctx.add_class('downvoted')

        if self._data.get('gilded') > 0:
            gold = '★{} '.format(self._data.get('gilded'))
            gold_label = Gtk.Label(label=gold)
            gold_label.get_style_context().add_class('gilded')

            label = self._button.get_child()
            self._button.remove(label)
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.add(gold_label)
            box.add(label)
            self._button.add(box)
            box.show_all()

class AuthorButtonBehaviour():

    def __init__(self, button, data, original_poster=None,
                 show_flair=False):
        button.props.label = data['author']
        button.connect('clicked', self.__name_clicked_cb)

        disti = data['distinguished']
        is_op = data['author'] == original_poster
        flair = data['author_flair_text'] if show_flair else None
        if disti is not None or is_op or flair is not None:
            label = button.get_child()
            button.remove(label)
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

            if disti is not None:
                l = Gtk.Label()
                l.props.label = {
                    'moderator': 'MOD',
                    'admin': 'ADM',
                    'special': 'SP'
                }[disti]
                l.get_style_context().add_class(disti)
                box.add(l)

            if is_op:
                l = Gtk.Label(label='OP')
                l.get_style_context().add_class('op')
                box.add(l)

            box.add(label)
            if flair is not None:
                l = Gtk.Label(label=flair)
                l.get_style_context().add_class('flair')
                box.add(l)

            button.add(box)
            box.show_all()

    def __name_clicked_cb(self, button):
        window = button.get_toplevel()
        window.goto_sublist('/u/{}/'.format(button.props.label))


class SubButtonBehaviour():

    def __init__(self, button, data):
        button.props.label = data['subreddit']
        button.connect('clicked', self.__sub_clicked_cb)

    def __sub_clicked_cb(self, button):
        window = button.get_toplevel()
        window.goto_sublist('/r/{}'.format(button.props.label))


class TimeButtonBehaviour():

    def __init__(self, button, data):
        self.data = data
        time = arrow.get(self.data['created_utc'])
        button.props.label = time.humanize()
        self._p = connect_palette(button, self._make_time_palette,
                                  modalify=True)

    def _make_time_palette(self):
        t = _TimePalette(self.data)
        t.get_child().show_all()
        return t


class _TimePalette(Gtk.Popover):

    def __init__(self, data, **kwargs):
        Gtk.Popover.__init__(self, **kwargs)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box)
        box.show()

        created = arrow.get(data['created_utc'])
        s = 'Created {} ({})'.format(created.format('hh:mm a, MMM YY'),
                                     created.humanize())
        if data.get('edited') is True:
            s = s + '\nEdited ages ago'
        elif data.get('edited'):
            edited = arrow.get(data['edited'])
            s = s + '\nEdited {} ({})'.format(edited.format('hh:mm a, MMM YY'),
                                              edited.humanize())
        label = SaneLabel(s)
        box.add(label)
        label.show()

        if data.get('permalink') is not None:
            uri = data['permalink']
        elif data.get('link_id') is not None:
            uri = '/r/{}/comments/{}//{}'.format(
                data['subreddit'], data['link_id'][len('t3_'):], data['id'])
        else:
            uri = '/r/{}/comments/{}'.format(
                data['subreddit'], data['id'])
        lb = Gtk.LinkButton(uri='https://www.reddit.com' + uri,
                            label='Permalink in External Browser')
        box.add(lb)
        lb.show()


class SubscribeButtonBehaviour():

    def __init__(self, api: RedditAPI, button, subreddit_name):
        self._api = api
        self._button = button
        self._subreddit_name = subreddit_name

        self._button.props.active = \
            '/r/{}/'.format(subreddit_name.lower()) \
            in self._api.lower_user_subs
        self._button.connect('toggled', self.__toggled_cb)
        self._set_label()

    def _set_label(self):
        self._button.props.label = 'Subscribed' \
            if self._button.props.active else 'Subscribe'

    def __toggled_cb(self, toggle):
        self._button.props.label = 'Subscribing...'  \
            if self._button.props.active else 'Unsubscribing...'
        self._button.props.sensitive = False

        self._api.set_subscribed(self._subreddit_name,
                                 self._button.props.active,
                                 self.__subscribe_cb)

    def __subscribe_cb(self, j):
        self._button.props.sensitive = True
        self._set_label()
        self._api.update_subscriptions()
