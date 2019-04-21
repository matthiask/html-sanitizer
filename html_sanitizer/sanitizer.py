from __future__ import unicode_literals

import re
import unicodedata
from collections import deque

import lxml.html
import lxml.html.clean


__all__ = ("Sanitizer",)
only_whitespace_re = re.compile(r"^\s*$")
whitespace_re = re.compile(r"\s+")


def sanitize_href(href):
    """
    Verify that a given href is benign and allowed.

    This is a stupid check, which probably should be much more elaborate
    to be safe.
    """
    if href.startswith(("/", "mailto:", "http:", "https:", "#", "tel:")):
        return href
    return "#"


def normalize_overall_whitespace(html):
    # remove all sorts of newline and nbsp characters
    whitespace = [
        "\n",
        "&#10;",
        "&#xa;",
        "\r",
        "&#13;",
        "&#xd;",
        "\xa0",
        "&nbsp;",
        "&#160;",
        "&#xa0",
    ]
    for ch in whitespace:
        html = html.replace(ch, " ")
    html = re.sub(r"(?u)\s+", " ", html)
    return html


def bold_span_to_strong(element):
    if element.tag == "span" and "bold" in element.get("style", ""):
        element.tag = "strong"
    return element


def italic_span_to_em(element):
    if element.tag == "span" and "italic" in element.get("style", ""):
        element.tag = "em"
    return element


def tag_replacer(from_, to_):
    def replacer(element):
        if element.tag == from_:
            element.tag = to_
        return element

    return replacer


def target_blank_noopener(element):
    if (
        element.tag == "a"
        and element.attrib.get("target") == "_blank"
        and "noopener" not in element.attrib.get("rel", "")
    ):
        element.attrib["rel"] = " ".join(
            part for part in (element.attrib.get("rel", ""), "noopener") if part
        )
    return element


def normalize_whitespace_in_text_or_tail(element):
    if element.text:
        while True:
            text = whitespace_re.sub(" ", element.text)
            if element.text == text:
                break
            element.text = text

    if element.tail:
        while True:
            text = whitespace_re.sub(" ", element.tail)
            if element.tail == text:
                break
            element.tail = text

    return element


DEFAULT_SETTINGS = {
    "tags": {
        "a",
        "h1",
        "h2",
        "h3",
        "strong",
        "em",
        "p",
        "ul",
        "ol",
        "li",
        "br",
        "sub",
        "sup",
        "hr",
    },
    "attributes": {"a": ("href", "name", "target", "title", "id", "rel")},
    "empty": {"hr", "a", "br"},
    "separate": {"a", "p", "li"},
    "whitespace": {"br"},
    "add_nofollow": False,
    "autolink": False,
    "sanitize_href": sanitize_href,
    "element_preprocessors": [
        # convert span elements into em/strong if a matching style rule
        # has been found. strong has precedence, strong & em at the same
        # time is not supported
        bold_span_to_strong,
        italic_span_to_em,
        tag_replacer("b", "strong"),
        tag_replacer("i", "em"),
        tag_replacer("form", "p"),
        target_blank_noopener,
    ],
    "element_postprocessors": [],
}


class Sanitizer(object):
    def __init__(self, settings=None):
        self.__dict__.update(DEFAULT_SETTINGS)
        self.__dict__.update(settings or {})

        # Allow iterables of any kind, not just sets.
        self.tags = set(self.tags)
        self.empty = set(self.empty)
        self.separate = set(self.separate)
        self.whitespace = set(self.whitespace)

        # Validate the settings.
        if not self.tags:
            raise TypeError(
                "Empty list of allowed tags is not supported by the underlying"
                " lxml cleaner. If you really do not want to pass any tags"
                " pass a made-up tag name which will never exist in your"
                " document."
            )
        if not self.tags.issuperset(self.empty):
            raise TypeError(
                'Tags in "empty", but not allowed: %r' % (self.empty - self.tags,)
            )
        if not self.tags.issuperset(self.separate):
            raise TypeError(
                'Tags in "separate", but not allowed: %r' % (self.separate - self.tags,)
            )
        if not self.tags.issuperset(self.attributes.keys()):
            raise TypeError(
                'Tags in "attributes", but not allowed: %r'
                % (set(self.attributes.keys()) - self.tags,)
            )

        anchor_attributes = self.attributes.get("a", ())
        if "target" in anchor_attributes and "rel" not in anchor_attributes:
            raise TypeError(
                'Always allow "rel" when allowing "target" as anchor' " attribute"
            )

    @staticmethod
    def is_mergeable(e1, e2):
        """
        Decide if the adjacent elements of the same type e1 and e2 can be
        merged. This can be overriden to honouring distinct classes etc.
        """
        return True

    def sanitize(self, html):
        """
        Clean HTML code from ugly copy-pasted CSS and empty elements

        Removes everything not explicitly allowed in ``self.allowed_tags``.

        Requires ``lxml`` and, for especially broken HTML, ``beautifulsoup4``.
        """

        html = normalize_overall_whitespace(html)
        html = "<div>%s</div>" % html
        try:
            doc = lxml.html.fromstring(html)
            lxml.html.tostring(doc, encoding="utf-8")
        except Exception:  # We could and maybe should be more specific...
            from lxml.html import soupparser

            doc = soupparser.fromstring(html)

        lxml.html.clean.Cleaner(
            remove_unknown_tags=False,
            # Remove style *tags*
            style=True,
            # Do not strip out style attributes; we still need the style
            # information to convert spans into em/strong tags
            safe_attrs_only=False,
            inline_style=False,
            # Do not strip all form tags; we will filter them below
            forms=False,
        )(doc)

        # walk the tree recursively, because we want to be able to remove
        # previously emptied elements completely
        backlog = deque(doc.iterdescendants())
        while True:
            try:
                element = backlog.pop()
            except IndexError:
                break

            for processor in self.element_preprocessors:
                element = processor(element)

            element = normalize_whitespace_in_text_or_tail(element)

            # remove empty tags if they are not explicitly allowed
            if (
                (not element.text or only_whitespace_re.match(element.text))
                and element.tag not in self.empty
                and not len(element)
            ):
                element.drop_tag()
                continue

            # remove tags which only contain whitespace and/or <br>s
            if (
                element.tag not in self.empty
                and only_whitespace_re.match(element.text or "")
                and {e.tag for e in element} <= self.whitespace
                and all(only_whitespace_re.match(e.tail or "") for e in element)
            ):
                element.drop_tree()
                continue

            if element.tag in {"li", "p"}:
                # remove p-in-li and p-in-p tags
                for p in element.findall("p"):
                    if getattr(p, "text", None):
                        p.text = " " + p.text + " "
                    p.drop_tag()

                # remove list markers, maybe copy-pasted from word or whatever
                if element.text:
                    element.text = re.sub(
                        r"^(\&nbsp;|\&#160;|\s)*(-|\*|&#183;)(\&nbsp;|\&#160;|\s)+",  # noqa
                        "",
                        element.text,
                    )

            elif element.tag in self.whitespace:
                # Drop the next element if
                # 1. it is a <br> too and 2. there is no content in-between
                nx = element.getnext()
                if (
                    nx is not None
                    and nx.tag == element.tag
                    and (not element.tail or only_whitespace_re.match(element.tail))
                ):
                    nx.drop_tag()
                    continue

            if not element.text:
                # No text before first child and first child is a <br>: Drop it
                first = list(element)[0] if list(element) else None
                if first is not None and first.tag in self.whitespace:
                    first.drop_tag()
                    # Maybe we have more than one <br>
                    backlog.append(element)
                    continue

            if element.tag in (self.tags - self.separate):
                # Check whether we should merge adjacent elements of the same
                # tag type
                nx = element.getnext()
                if (
                    only_whitespace_re.match(element.tail or "")
                    and nx is not None
                    and nx.tag == element.tag
                    and self.is_mergeable(element, nx)
                ):
                    # Yes, we should. Tail is empty, that is, no text between
                    # tags of a mergeable type.
                    if nx.text:
                        if len(element):
                            list(element)[-1].tail = "%s %s" % (
                                list(element)[-1].tail or "",
                                nx.text,
                            )
                        else:
                            element.text = "%s %s" % (element.text or "", nx.text)

                    for child in nx:
                        element.append(child)

                    # tail is merged with previous element.
                    nx.drop_tree()

                    # Process element again
                    backlog.append(element)
                    continue

            for processor in self.element_postprocessors:
                element = processor(element)

            # remove all attributes which are not explicitly allowed
            allowed = self.attributes.get(element.tag, [])
            for key in element.keys():
                if key not in allowed:
                    del element.attrib[key]

            # Clean hrefs so that they are benign
            href = element.get("href")
            if href is not None:
                element.set("href", self.sanitize_href(href))

            element = normalize_whitespace_in_text_or_tail(element)

        if self.autolink is True:
            lxml.html.clean.autolink(doc)
        elif isinstance(self.autolink, dict):
            lxml.html.clean.autolink(doc, **self.autolink)

        # Run cleaner again, but this time with even more strict settings
        lxml.html.clean.Cleaner(
            allow_tags=self.tags,
            remove_unknown_tags=False,
            safe_attrs_only=False,  # Our attributes allowlist is sufficient.
            add_nofollow=self.add_nofollow,
            forms=False,
        )(doc)

        html = lxml.html.tostring(doc, encoding="unicode")

        # add a space before the closing slash in empty tags
        html = re.sub(r"<([^/>]+)/>", r"<\1 />", html)

        # remove wrapping tag needed by XML parser
        html = re.sub(r"^<div>|</div>$", "", html)

        # normalize unicode
        html = unicodedata.normalize("NFKC", html)

        return html
