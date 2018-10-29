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

import re
import markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern, SimpleTagPattern

from gi.repository import Gtk
from gi.repository import Pango


_URI_RE = r'(https?://[^ \r\t\n]+)'


class _URIPattern(Pattern):

    def handleMatch(self, match):
        uri = match.group(2)
        el = markdown.util.etree.Element('a')
        el.set('href', uri)
        el.text = markdown.util.AtomicString(uri)
        return el


class _URIRegex(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns['uriregex'] = _URIPattern(_URI_RE, md)


class _StrikeThroughRegex(Extension):
    def extendMarkdown(self, md, md_globals):
        s_tag = SimpleTagPattern('(~~)([^~]+)~~', 's')
        md.inlinePatterns.add('s', s_tag, '>not_strong')


MDX_CONTEXT = markdown.Markdown(extensions=[_URIRegex(),
                                            _StrikeThroughRegex()])


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

    text = MDX_CONTEXT.convert(text)
    text = text.replace('<p>', '').replace('</p>', '\n\n')
    text = text.replace('<br />', '\n')
    text = text.replace('<hr />', '—' * 15)
    text = text.replace('<em>', '<i>').replace('</em>', '</i>')
    text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
    text = text.replace(
        '<h1>', '<span font-size="x-large">').replace('</h1>', '</span>')
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
        set_markup_sane(self, markup)


def set_markup_sane(label, markup):
    label.props.xalign = 0
    label.props.justify = Gtk.Justification.LEFT
    label.props.wrap = True
    label.props.wrap_mode = Pango.WrapMode.WORD_CHAR
    label.set_markup(markup)
    label.connect('activate-link', __activate_link_cb)


def __activate_link_cb(label, uri):
    window = label.get_toplevel()
    window.load_uri_from_label(uri)
    return True
