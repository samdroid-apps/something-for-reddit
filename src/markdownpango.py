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

import re
import markdown

from gi.repository import Gtk


def markdown_to_pango(text):
    '''
    Convert a string of reddit markdown to a string
    of pango markup.

    How?

    Super bad     - we just go markdown->html and then use regex to
                    convert most of the stuff to pango (subset of html)
    '''
    if text is None:
        return ''

    text = markdown.markdown(text, extensions=['urlize'])
    text = text.replace('<p>', '').replace('</p>', '\n\n')
    text = text.replace('<br />', '\n')
    text = text.replace('<hr />', '—'*15)
    text = text.replace('<em>', '<i>').replace('</em>', '</i>')
    text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
    text = text.replace('<h1>', '<span font-size="x-large">').replace('</h1>', '</span>')
    text = re.sub('<h[2-6]>', '<big>', text)
    text = re.sub('</h[2-6]>', '</big>', text)
    text = text.replace('<pre>', '<tt>').replace('</pre>', '</tt>')
    text = text.replace('<code>', '<tt>').replace('</code>', '</tt>')

    # Worlds best list processing
    text = text.replace('<ul>', '').replace('<ol>', '') \
               .replace('</ul>', '').replace('</ol>', '') \
               .replace('<li>', '∙ ').replace('</li>', '')
    # sometimes they end up on another line
    text = re.sub('∙\s+', '∙ ', text, flags=re.MULTILINE)

    return text.strip()


class SaneLabel(Gtk.Label):
    '''
    A GtkLabel that is mulit-line and left aligned.

    Args:
        markup (str): Gtk markup
    '''

    def __init__(self, markup):
        Gtk.Label.__init__(self)
        self.props.xalign = 0
        self.props.justify = Gtk.Justification.LEFT
        self.set_line_wrap(True)
        self.set_markup(markup)

    def do_activate_link(self, uri):
        window = self.get_toplevel()
        window.load_uri_from_label(uri)
