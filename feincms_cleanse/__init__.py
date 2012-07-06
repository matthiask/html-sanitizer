VERSION = (1, 0, 0)
__version__ = '.'.join(map(str, VERSION))

import re
import unicodedata

__all__ = ('cleanse_html', )

cleanse_html_allowed = {
    'a': ('href', 'name', 'target', 'title'),
    'h2': (),
    'h3': (),
    'strong': (),
    'em': (),
    'p': (),
    'ul': (),
    'ol': (),
    'li': (),
    'span': (),
    'br': (),
    'sub': (),
    'sup': (),
    'anything': (),
    }

cleanse_html_allowed_empty_tags = ('br',)

cleanse_html_merge = ('h2', 'h3', 'strong', 'em', 'ul', 'ol', 'sub', 'sup')
# ------------------------------------------------------------------------
def _validate_href(href):
    """
    Verify that a given href is benign and allowed.
    """
    # TODO: Implement me! This should ensure that the href is either a
    # path without a protocol, or the protocol is known and http/https.
    # Perhaps also add an option to allow/forbid off-site hrefs?
    return True

# ------------------------------------------------------------------------
def cleanse_html(html,
                 allowed_tags=cleanse_html_allowed,
                 allowed_empty_tags=cleanse_html_allowed_empty_tags,
                 merge_tags=cleanse_html_merge):
    """
    Clean HTML code from ugly copy-pasted CSS and empty elements

    Removes everything not explicitly allowed in ``cleanse_html_allowed``.

    Requires ``lxml`` and ``beautifulsoup``.
    """
    from BeautifulSoup import BeautifulSoup
    import lxml.html
    import lxml.html.clean

    doc = lxml.html.fromstring('<anything>%s</anything>' % html)
    try:
        lxml.html.tostring(doc, encoding=unicode)
    except UnicodeDecodeError:
        # fall back to slower BeautifulSoup if parsing failed
        from lxml.html import soupparser
        doc = soupparser.fromstring(u'<anything>%s</anything>' % html)

    cleaner = lxml.html.clean.Cleaner(
        allow_tags=allowed_tags.keys() + ['style'],
        remove_unknown_tags=False, # preserve surrounding 'anything' tag
        style=False, safe_attrs_only=False, # do not strip out style
                                            # attributes; we still need
                                            # the style information to
                                            # convert spans into em/strong
                                            # tags
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

            if element.tag == 'span': # still span
                element.drop_tag() # remove tag, but preserve children and text
                continue

        # remove empty tags if they are not <br />
        elif (not element.text and
              element.tag not in allowed_empty_tags and
              not len(element)):
            element.drop_tag()
            continue

        # remove all attributes which are not explicitly allowed
        allowed = allowed_tags.get(element.tag, [])
        for key in element.attrib.keys():
            if key not in allowed:
                del element.attrib[key]

        # Clean hrefs so that they are benign
        href = element.attrib.get('href', None)
        if href is not None and not _validate_href(href):
            del element.attrib['href']

    # just to be sure, run cleaner again, but this time with even more
    # strict settings
    cleaner = lxml.html.clean.Cleaner(
        allow_tags=allowed_tags.keys(),
        remove_unknown_tags=False, # preserve surrounding 'anything' tag
        style=True, safe_attrs_only=True
        )

    cleaner(doc)

    html = lxml.html.tostring(doc, method='xml')

    # remove wrapping tag needed by XML parser
    html = re.sub(r'</?anything>', '', html)

    # remove all sorts of newline characters
    html = html.replace('\n', ' ').replace('\r', ' ')
    html = html.replace('&#10;', ' ').replace('&#13;', ' ')
    html = html.replace('&#xa;', ' ').replace('&#xd;', ' ')

    # remove elements containing only whitespace or linebreaks
    whitespace_re = re.compile(r'<([a-z0-9]+)>(<br\s*/>|\&nbsp;|\&#160;|\s)*</\1>')
    while True:
        new = whitespace_re.sub('', html)
        if new == html:
            break
        html = new

    # merge tags
    for tag in merge_tags:
        merge_str = u'\s*</%s>\s*<%s>\s*' % (tag, tag)
        while True:
            new = re.sub(merge_str, u' ', html)
            if new == html:
                break
            html = new

    # fix p-in-p tags
    p_in_p_start_re = re.compile(r'<p>(\&nbsp;|\&#160;|\s)*<p>')
    p_in_p_end_re = re.compile('</p>(\&nbsp;|\&#160;|\s)*</p>')

    for tag in merge_tags:
        merge_start_re = re.compile('<p>(\\&nbsp;|\\&#160;|\\s)*<%s>(\\&nbsp;|\\&#160;|\\s)*<p>' % tag)
        merge_end_re = re.compile('</p>(\\&nbsp;|\\&#160;|\\s)*</%s>(\\&nbsp;|\\&#160;|\\s)*</p>' % tag)

        while True:
            new = merge_start_re.sub('<p>', html)
            new = merge_end_re.sub('</p>', new)
            new = p_in_p_start_re.sub('<p>', new)
            new = p_in_p_end_re.sub('</p>', new)

            if new == html:
                break
            html = new

    # remove list markers with <li> tags before them
    html = re.sub(r'<li>(\&nbsp;|\&#160;|\s)*(-|\*|&#183;)(\&nbsp;|\&#160;|\s)*', '<li>', html)

    # remove p-in-li tags
    html = re.sub(r'<li>(\&nbsp;|\&#160;|\s)*<p>', '<li>', html)
    html = re.sub(r'</p>(\&nbsp;|\&#160;|\s)*</li>', '</li>', html)

    # add a space before the closing slash in empty tags
    html = re.sub(r'<([^/>]+)/>', r'<\1 />', html)

    # nicify entities and normalize unicode
    html = unicode(BeautifulSoup(html, convertEntities='xml'))
    html = unicodedata.normalize('NFKC', html)

    return html
