from __future__ import unicode_literals

from bs4 import BeautifulSoup
import lxml.html
import lxml.html.clean
import re
import unicodedata


VERSION = (1, 0, 0)
__version__ = '.'.join(map(str, VERSION))

__all__ = ('Sanitizer',)


DEFAULT_SETTINGS = {
    'tags': {
        'a',
        'h1',
        'h2',
        'h3',
        'strong',
        'em',
        'p',
        'ul',
        'ol',
        'li',
        'span',
        'br',
        'sub',
        'sup',
        'pre',
        'hr',
    },
    'attributes': {
        'a': ('href', 'name', 'target', 'title', 'id'),
    },
    'empty': {'hr', 'a', 'br'},
    'separate': {'a', 'p', 'li'},
}


class Sanitizer(object):
    def __init__(self, settings=None):
        self.__dict__.update(DEFAULT_SETTINGS)
        self.__dict__.update(settings or {})

        # Validate the settings.
        if not self.tags.issuperset(self.empty):
            raise TypeError('Tags in "empty", but not allowed: %r' % (
                self.empty - self.tags,
            ))
        if not self.tags.issuperset(self.separate):
            raise TypeError('Tags in "separate", but not allowed: %r' % (
                self.separate - self.tags,
            ))
        if not self.tags.issuperset(self.attributes.keys()):
            raise TypeError('Tags in "attributes", but not allowed: %r' % (
                set(self.attributes.keys()) - self.tags,
            ))

    def validate_href(self, href):
        """
        Verify that a given href is benign and allowed.

        This is a stupid check, which probably should be much more elaborate
        to be safe.
        """
        return href.startswith(
            ('/', 'mailto:', 'http:', 'https:', '#', 'tel:'))

    def clean(self, element):
        """ Hook for your own clean methods. """
        return element

    def sanitize(self, html):
        """
        Clean HTML code from ugly copy-pasted CSS and empty elements

        Removes everything not explicitly allowed in ``self.allowed_tags``.

        Requires ``lxml`` and ``beautifulsoup``.
        """

        html = '<anything>%s</anything>' % html
        doc = lxml.html.fromstring(html)
        try:
            lxml.html.tostring(doc, encoding='utf-8')
        except UnicodeDecodeError:
            # fall back to slower BeautifulSoup if parsing failed
            from lxml.html import soupparser
            doc = soupparser.fromstring(html)

        cleaner = lxml.html.clean.Cleaner(
            allow_tags=list(self.tags) + ['anything'],
            remove_unknown_tags=False,  # preserve surrounding 'anything' tag
            # Remove style *tags*
            style=True,
            # Do not strip out style attributes; we still need the style
            # information to convert spans into em/strong tags
            safe_attrs_only=False,
            inline_style=False,
        )

        cleaner(doc)

        # walk the tree recursively, because we want to be able to remove
        # previously emptied elements completely
        for element in reversed(list(doc.iterdescendants())):
            if element.tag == 'style':
                element.drop_tree()
                continue

            # convert span elements into em/strong if a matching style rule
            # has been found. strong has precedence, strong & em at the same
            # time is not supported
            elif element.tag == 'span':
                style = element.attrib.get('style')
                if style:
                    if 'bold' in style:
                        element.tag = 'strong'
                    elif 'italic' in style:
                        element.tag = 'em'

                if element.tag == 'span':  # still span
                    # remove tag, but preserve children and text
                    element.drop_tag()
                    continue

            # remove empty tags if they are not <br />
            elif (not element.text and
                  element.tag not in self.empty and
                  not len(element)):
                element.drop_tag()
                continue

            elif element.tag == 'li':
                # remove p-in-li tags
                for p in element.findall('p'):
                    if getattr(p, 'text', None):
                        p.text = ' ' + p.text + ' '
                    p.drop_tag()

            # Hook for custom filters:
            element = self.clean(element)

            # remove all attributes which are not explicitly allowed
            allowed = self.attributes.get(element.tag, [])
            for key in element.attrib.keys():
                if key not in allowed:
                    del element.attrib[key]

            # Clean hrefs so that they are benign
            href = element.attrib.get('href', None)
            if href is not None and not self.validate_href(href):
                element.attrib['href'] = ''

        # just to be sure, run cleaner again, but this time with even more
        # strict settings
        cleaner = lxml.html.clean.Cleaner(
            allow_tags=list(self.tags) + ['anything'],
            remove_unknown_tags=False,  # preserve surrounding 'anything' tag
            safe_attrs_only=True,
        )

        cleaner(doc)

        html = lxml.html.tostring(doc, method='xml').decode('utf-8')

        # remove all sorts of newline characters
        html = html.replace('\n', ' ').replace('\r', ' ')
        html = html.replace('&#10;', ' ').replace('&#13;', ' ')
        html = html.replace('&#xa;', ' ').replace('&#xd;', ' ')

        # remove elements containing only whitespace or linebreaks
        whitespace_re = re.compile(
            r'<([a-z0-9]+)>(<br\s*/>|\&nbsp;|\&#160;|\s)*</\1>')
        while True:
            new = whitespace_re.sub('', html)
            if new == html:
                break
            html = new

        # merge tags
        for tag in (self.tags - self.separate):
            merge_str = '\s*</%s>\s*<%s>\s*' % (tag, tag)
            while True:
                new = re.sub(merge_str, ' ', html)
                if new == html:
                    break
                html = new

        # fix p-in-p tags
        p_in_p_start_re = re.compile(r'<p>(\&nbsp;|\&#160;|\s)*<p>')
        p_in_p_end_re = re.compile('</p>(\&nbsp;|\&#160;|\s)*</p>')

        for tag in (self.tags - self.separate):
            merge_start_re = re.compile(
                '<p>(\\&nbsp;|\\&#160;|\\s)*<%s>(\\&nbsp;|\\&#160;|\\s)*<p>'
                % tag)
            merge_end_re = re.compile(
                '</p>(\\&nbsp;|\\&#160;|\\s)*</%s>(\\&nbsp;|\\&#160;|\\s)*</p>'
                % tag)

            while True:
                new = merge_start_re.sub('<p>', html)
                new = merge_end_re.sub('</p>', new)
                new = p_in_p_start_re.sub('<p>', new)
                new = p_in_p_end_re.sub('</p>', new)

                if new == html:
                    break
                html = new

        # remove list markers with <li> tags before them
        html = re.sub(
            r'<li>(\&nbsp;|\&#160;|\s)*(-|\*|&#183;)(\&nbsp;|\&#160;|\s)+',
            '<li>',
            html)

        # add a space before the closing slash in empty tags
        html = re.sub(r'<([^/>]+)/>', r'<\1 />', html)

        # remove wrapping tag needed by XML parser
        html = re.sub(r'</?anything( /)?>', '', html)

        # nicify entities and normalize unicode
        html = '%s' % BeautifulSoup(html, 'lxml')
        html = unicodedata.normalize('NFKC', html)
        html = re.sub(r'^<html><body>', '', html)
        html = re.sub(r'</body></html>$', '', html)

        # add a space before the closing slash in empty tags
        html = re.sub(r'<([^/>]+)/>', r'<\1 />', html)

        return html
