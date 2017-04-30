==============
html sanitizer
==============

.. image:: https://travis-ci.org/matthiask/html-sanitizer.svg?branch=master
    :target: https://travis-ci.org/matthiask/html-sanitizer

This is the FeinCMS HTML cleansing function which lived under the name of
``feincms.utils.html.cleanse.cleanse_html``, and has been moved to
its own repository now to be usable in other projects, and to not set a
precedent for a particular HTML cleaning technique in FeinCMS anymore.

Usage is simple::

    >>> from html_sanitizer import Sanitizer
    >>> sanitizer = Sanitizer()  # default configuration
    >>> sanitizer.sanitize('<span style="font-weight:bold">some text</span>')
    '<strong>some text</strong>'
