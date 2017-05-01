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

- Clean up HTML using a very restricted set of allowed tags and
  attributes.
- Convert *some* tags (such as ``<span style="...">``, ``<b>`` and
  ``<i>``) into either ``<strong>`` or ``<em>`` (but never both).
- Normalize whitespace by removing repeated line breaks, empty
  paragraphs and other empty elements.
- Merge adjacent tags of the same type (such as several ``<strong>`` or
  ``<h3>`` directly after each other.
- Automatically remove redundant list markers inside ``<li>`` tags.
- Clean up some uglyness such as paragraphs inside paragraphs or list
  elements etc.

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

The default settings are::

    DEFAULT_SETTINGS = {
        'tags': {
            'a', 'h1', 'h2', 'h3', 'strong', 'em', 'p', 'ul', 'ol',
            'li', 'br', 'sub', 'sup', 'pre', 'hr',
        },
        'attributes': {
            'a': ('href', 'name', 'target', 'title', 'id'),
        },
        'empty': {'hr', 'a', 'br'},
        'separate': {'a', 'p', 'li'},
        'add_nofollow': False,
        # TODO 'autolink': ...
    }

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

.. _Django: https://www.djangoproject.com/
.. _FeinCMS: https://pypi.python.org/pypi/FeinCMS
.. _feincms-cleanse: https://pypi.python.org/pypi/feincms-cleanse
