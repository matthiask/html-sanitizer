==============
HTML sanitizer
==============

.. image:: https://travis-ci.org/matthiask/html-sanitizer.svg?branch=master
    :target: https://travis-ci.org/matthiask/html-sanitizer

This is a whitelist-based and very opinionated HTML sanitizer that
can be used both for untrusted and trusted sources. It attempts to clean
up the mess made by various rich text editors and or copy-pasting to
make styling of webpages simpler and more consistent.

It had its humble beginnings as ``feincms.utils.html.cleanse.cleanse_html``
and feincms-cleanse_, and while it's still humble its name has been
changed to HTML sanitizer to underline the fact that it has absolutely
no dependency on either Django_ or FeinCMS_.

Goals
=====

HTML sanitizer goes further than e.g. bleach_ in that it not only
ensures that content is safe and tags and attributes conform to a given
whitelist, but also applies additional transforms to HTML fragments. A
short list of goals follows:

- Clean up HTML fragments using a very restricted set of allowed tags
  and attributes.
- Convert *some* tags (such as ``<span style="...">``, ``<b>`` and
  ``<i>``) into either ``<strong>`` or ``<em>`` (but never both).
- Absolutely disallow all inline styles.
- Normalize whitespace by removing repeated line breaks, empty
  paragraphs and other empty elements.
- Merge adjacent tags of the same type (such as several ``<strong>`` or
  ``<h3>`` directly after each other.
- Automatically remove redundant list markers inside ``<li>`` tags.
- Clean up some uglyness such as paragraphs inside paragraphs or list
  elements etc.
- Normalize unicode.

Usage
=====

    >>> from html_sanitizer import Sanitizer
    >>> sanitizer = Sanitizer()  # default configuration
    >>> sanitizer.sanitize('<span style="font-weight:bold">some text</span>')
    '<strong>some text</strong>'

Settings
========

- ``span`` elements will always be removed from the tree, but only after
  inspecting their style tags (bold spans are converted into ``strong``
  tags, italic spans into ``em`` tags)
- ``b`` and ``i`` tags will always be converted into ``strong`` and
  ``em`` (if ``strong`` and ``em`` are allowed at all)
- Inline styles and scripts will always be dropped.
- A ``div`` element is used to wrap the HTML fragment for the parser,
  therefore ``div`` tags are not allowed.

The default settings are::

    DEFAULT_SETTINGS = {
        'tags': {
            'a', 'h1', 'h2', 'h3', 'strong', 'em', 'p', 'ul', 'ol',
            'li', 'br', 'sub', 'sup', 'hr',
        },
        'attributes': {
            'a': ('href', 'name', 'target', 'title', 'id'),
        },
        'empty': {'hr', 'a', 'br'},
        'separate': {'a', 'p', 'li'},
        'add_nofollow': False,
        'autolink': False,
        'element_filters': [],
        'sanitize_href': html_sanitizer.sanitizer.sanitize_href,
    }

The keys' meaning is as follows:

- ``tags``: A ``set()`` of allowed tags.
- ``attributes``: A ``dict()`` mapping tags to their allowed attributes.
- ``empty``: Tags which are allowed to be empty. By default, empty tags
  (containing no text or only whitespace) are dropped.
- ``separate``: Tags which are not merged if they appear as siblings. By
  default, tags of the same type are merged.
- ``add_nofollow``: Whether to add ``rel="nofollow"`` to all links.
- ``autolink``: Enable lxml_'s autolinker_. May be either a boolean or a
  dictionary; a dictionary is passed as keyword arguments to
  ``autolink``.
- ``element_filters``: Additional filters that are called on all
  elements in the tree. The tree is processed in reverse depth-first
  order. Under certain circumstances elements are processed more than
  once (search the code for ``backlog.append``)
- ``sanitize_href``: A callable that gets anchor's ``href`` value and
  returns a sanitized version. The default implementation checks whether
  links start with a few allowed prefixes, and if not, returns a single
  hash (``#``).

Settings can be specified partially when initializing a sanitizer
instance, but are still checked for consistency (e.g. it's not allowed
to have tags in ``empty`` that are not in ``tags``, that is, tags that
are allowed to be empty but at the same time not allowed at all). An
example for an even more restricted configuration might be::

    >>> from html_sanitizer import Sanitizer
    >>> sanitizer = Sanitizer({
    ...     'tags': ('h1', 'h2', 'p'),
    ...     'attributes': {},
    ...     'empty': set(),
    ...     'separate': set(),
    ... })

The rationale for such a restricted set of allowed tags (e.g. no
images) is documented in the `design decisions`_ section of
django-content-editor_'s documentation.

Django
======

HTML sanitizer does not depend on Django, but ships with a module which
makes configuring sanitizers using Django settings easier. Usage is as
follows::

    >>> from html_sanitizer.django import get_sanitizer
    >>> sanitizer = get_sanitizer([name=...])

Different sanitizers can be configured. The default configuration is
aptly named ``'default'``. Example settings follow::

    HTML_SANITIZERS = {
        'default': {
        'tags': ...,
        ...
    }

The ``'default'`` configuration is special: If it isn't explicitly
defined, the default configuration above is used instead.


.. _bleach: https://bleach.readthedocs.io/
.. _Django: https://www.djangoproject.com/
.. _django-content-editor: http://django-content-editor.readthedocs.io/
.. _FeinCMS: https://pypi.python.org/pypi/FeinCMS
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse
.. _design decisions: http://django-content-editor.readthedocs.io/en/latest/#design-decisions
.. _lxml: http://lxml.de/
.. _autolinker: http://lxml.de/api/lxml.html.clean-module.html
