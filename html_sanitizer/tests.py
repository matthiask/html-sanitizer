# coding=utf-8

from __future__ import unicode_literals

from contextlib import contextmanager
from unittest import TestCase

from .sanitizer import Sanitizer


class SanitizerTestCase(TestCase):
    if not hasattr(TestCase, "subTest"):

        @contextmanager
        def subTest(self, *args, **kwargs):
            yield

    def run_tests(self, entries, sanitizer=Sanitizer()):
        for before, after in entries:
            with self.subTest(before=before, after=after):
                after = before if after is None else after
                result = sanitizer.sanitize(before)
                self.assertEqual(
                    result,
                    after,
                    "Cleaning '%s', expected '%s' but got '%s'"
                    % (before, after, result),
                )

    def test_01_sanitize(self):
        entries = [
            ("<p>&nbsp;</p>", " "),
            ("<p>           </p>", " "),
            (
                '<span style="font-weight: bold;">Something</span><p></p>',
                "<strong>Something</strong>",
            ),
            (
                "<p>abc <span>def <em>ghi</em> jkl</span> mno</p>",
                "<p>abc def <em>ghi</em> jkl mno</p>",
            ),
            (
                '<span style="font-style: italic;">Something</span><p></p>',
                "<em>Something</em>",
            ),
            ('<h2 style="font-weight:bold">bla</h2>', "<h2>bla</h2>"),
            ('<h2 style="font-style:italic">bla</h2>', "<h2>bla</h2>"),
            ("<p>abc<br />def</p>", "<p>abc<br>def</p>"),
            ("<p><br/><br/><strong></strong>  <br/></p>", ""),
            ("<p><br/><strong></strong>  <br/> abc</p>", "<p> abc</p>"),
            ("<li><br>bla</li>", "<li>bla</li>"),
            (
                "<p><strong>just</strong> <em>testing</em></p>",
                "<p><strong>just</strong> <em>testing</em></p>",
            ),
            (
                "<p>Hallo<br>Welt<br><br>Hallo<br>Welt</p>",
                "<p>Hallo<br>Welt<br>Hallo<br>Welt</p>",
            ),
            (
                "<p><strong>Zeile 1</strong><br>Zeile 2<br>Zeile 3</p>",
                "<p><strong>Zeile 1</strong><br>Zeile 2<br>Zeile 3</p>",
            ),
            (
                "<p><strong>A</strong>, <strong>B</strong>"
                " und <strong>C</strong></p>",
                "<p><strong>A</strong>, <strong>B</strong>"
                " und <strong>C</strong></p>",
            ),
            ("<p><form>Zeile 1</form></p>", "<p>Zeile 1</p>"),
            # Suboptimal, should be cleaned further
            ("<form><p>Zeile 2</p></form>", "<p> Zeile 2 </p>"),
            ("1<p> </p>2", "1 2"),
            ("1<p></p>2", "12"),
            ("<p>son<strong>der</strong>bar</p>", "<p>son<strong>der</strong>bar</p>"),
            # Empty a tags are allowed...
            ("<a>  </a>", "<a> </a>"),
            # ...but breaks without any additional content are still removed
            ("<a><br />  </a>", "<a> </a>"),
        ]

        self.run_tests(entries)

    def test_02_a_tag(self):
        entries = (
            ('<a href="/foo">foo</a>', None),
            (
                '<a href="/foo" name="bar" target="some" title="baz"'
                ' cookies="yesplease">foo</a>',
                '<a href="/foo" name="bar" target="some" title="baz">foo</a>',
            ),
            ('<a href="http://somewhere.else">foo</a>', None),
            ('<a href="https://somewhere.else">foo</a>', None),
            ('<a href="javascript:alert()">foo</a>', '<a href="#">foo</a>'),
            ('<a href="javascript%3Aalert()">foo</a>', '<a href="#">foo</a>'),
            ('<a href="mailto:foo@bar.com">foo</a>', None),
            ('<a href="tel:1-234-567-890">foo</a>', None),
        )

        self.run_tests(entries)

    def test_03_merge(self):
        entries = (
            ("<h2>foo</h2><h2>bar</h2>", "<h2>foo bar</h2>"),
            ("<h2>foo  </h2>   <h2>   bar</h2>", "<h2>foo bar</h2> "),
        )

        self.run_tests(entries)

    def test_04_p_in_li(self):
        entries = (
            ("<li><p>foo</p></li>", "<li> foo </li>"),
            ("<li>&nbsp;<p>foo</p> &#160; </li>", "<li> foo </li>"),
            (
                "<li>foo<p>bar<strong>xx</strong>rab</p><strong>baz</strong>"
                "a<p>b</p>c</li>",
                "<li>foo bar <strong>xx</strong>rab<strong>baz</strong>a b" " c</li>",
            ),
        )

        self.run_tests(entries)

    def test_05_p_in_p(self):
        entries = (
            ("<p><p>foo</p></p>", "<p>foo</p>"),
            ("<p><p><p>&nbsp;</p> </p><p><br /></p></p>", " "),
            # This is actually correct as the second <p> implicitely
            # closes the first paragraph, and the trailing </p> is
            # deleted because it has no matching opening <p>
            ("<p>foo<p>bar</p>baz</p>", "<p>foo</p><p>bar</p>baz"),
            ("<p>bla <p>blub</p> blaaa</p>", "<p>bla </p><p>blub</p> blaaa"),
            (
                "<p>text1 <p>text2</p> tail2 <p>text3</p> tail3 </p>tail1",
                "<p>text1 </p><p>text2</p> tail2 <p>text3</p> tail3 tail1",
            ),
        )

        self.run_tests(entries)

    def test_06_allowlist(self):
        entries = (
            ('<script src="http://abc">foo</script>', ""),
            ('<script type="text/javascript">foo</script>', ""),
        )

        self.run_tests(entries)

    def test_07_configuration(self):
        sanitizer = Sanitizer(
            {"tags": ["h1", "h2"], "empty": (), "separate": (), "attributes": {}}
        )

        entries = (
            ("<h1>foo</h1>", None),
            ("<h1>foo</h1><h2>bar</h2><h3>baz</h3>", "<h1>foo</h1><h2>bar</h2>baz"),
        )

        self.run_tests(entries, sanitizer=sanitizer)

    def test_08_li_with_marker(self):
        entries = (
            ("<li> - foo</li>", "<li>foo</li>"),
            ("<li>* foo</li>", "<li>foo</li>"),
        )

        self.run_tests(entries)

    def test_09_empty_p_text_in_li(self):
        # this results in an empty p.text
        entries = (
            ("<li><p><strong>foo</strong></p></li>", "<li><strong>foo</strong></li>"),
            ("<li><p><em>foo</em></p></li>", "<li><em>foo</em></li>"),
        )

        self.run_tests(entries)

    def test_10_broken_html(self):
        entries = (
            ("<p><strong>bla", "<p><strong>bla</strong></p>"),
            ("<p><strong>bla<>/dsiad<p/", "<p><strong>bla&lt;&gt;/dsiad</strong></p>"),
        )

        self.run_tests(entries)

    def test_11_nofollow(self):
        sanitizer = Sanitizer({"add_nofollow": True})

        entries = (
            (
                '<p><a href="http://example.com/">example.com</a></p>',
                '<p><a href="http://example.com/"'
                ' rel="nofollow">example.com</a></p>',
            ),
        )

        self.run_tests(entries, sanitizer=sanitizer)

    def test_12_replacements(self):
        entries = (
            ("<b>Bla</b>", "<strong>Bla</strong>"),
            ("<i>Bla</i>", "<em>Bla</em>"),
        )

        self.run_tests(entries)

    def test_13_autolink(self):
        self.run_tests([("<p>https://github.com/</p>", "<p>https://github.com/</p>")])

        sanitizer = Sanitizer({"autolink": True})

        self.run_tests(
            [
                (
                    "<p>https://github.com/</p>",
                    '<p><a href="https://github.com/">https://github.com/</a></p>',
                ),
                (
                    # localhost is not autolinked by default by lxml
                    "<p>https://localhost/</p>",
                    "<p>https://localhost/</p>",
                ),
            ],
            sanitizer=sanitizer,
        )

        sanitizer = Sanitizer({"autolink": True, "add_nofollow": True})

        self.run_tests(
            [
                (
                    "<p>https://github.com/</p>",
                    '<p><a href="https://github.com/"'
                    ' rel="nofollow">https://github.com/</a></p>',
                )
            ],
            sanitizer=sanitizer,
        )

        sanitizer = Sanitizer({"autolink": {"avoid_hosts": []}})

        self.run_tests(
            [
                (
                    "<p>https://github.com/</p>",
                    '<p><a href="https://github.com/">https://github.com/</a></p>',
                ),
                (
                    "<p>https://localhost/</p>",
                    '<p><a href="https://localhost/">https://localhost/</a></p>',
                ),
            ],
            sanitizer=sanitizer,
        )

    def test_14_classes(self):
        """Class attributes should not be treated specially"""
        sanitizer = Sanitizer(
            {
                "tags": {"h1", "h2", "p", "a", "span"},
                "attributes": {
                    "a": ("href", "name", "target", "title", "id", "rel"),
                    "h1": ("class",),
                    "p": ("class",),
                    "span": ("class",),
                },
                "empty": set(),
                "separate": {"a", "p"},
            }
        )

        self.run_tests(
            [
                ('<p class="centered">Test</p>', '<p class="centered">Test</p>'),
                (
                    '<p class="centered">Test <span class="bla">span</span></p>',
                    '<p class="centered">Test <span class="bla">span</span></p>',
                ),
                (
                    '<p class="centered">Test <span class="bla">span</span>'
                    '<span class="blub">span</span></p>',
                    '<p class="centered">Test <span class="bla">span span</span></p>',
                ),
                ('<h1 class="centered">Test</h1>', '<h1 class="centered">Test</h1>'),
                ('<h2 class="centered">Test</h2>', "<h2>Test</h2>"),
            ],
            sanitizer=sanitizer,
        )

    def test_15_classes(self):
        """Class attributes may disable merging"""
        sanitizer = Sanitizer(
            {
                "tags": {"h1", "h2", "p", "a", "span"},
                "attributes": {
                    "a": ("href", "name", "target", "title", "id", "rel"),
                    "h1": ("class",),
                    "p": ("class",),
                    "span": ("class",),
                },
                "empty": set(),
                "separate": {"a", "p"},
                "is_mergeable": lambda e1, e2: e1.get("class") == e2.get("class"),
            }
        )

        self.run_tests(
            [
                (
                    '<p class="centered">Test <span class="bla">span</span>'
                    '<span class="blub">span</span></p>',
                    '<p class="centered">Test <span class="bla">span</span>'
                    '<span class="blub">span</span></p>',
                ),
                (
                    '<p class="centered">Test <span class="bla">span</span>'
                    '<span class="bla">span</span></p>',
                    '<p class="centered">Test <span class="bla">span span</span></p>',
                ),
            ],
            sanitizer=sanitizer,
        )

    def test_16_emoji(self):
        self.run_tests([("<p>😂</p>", "<p>😂</p>"), ("<p>💕</p>", "<p>💕</p>")])

    def test_target_blank(self):
        self.run_tests(
            [
                (
                    '<a href="#" target="_blank">test</a>',
                    '<a href="#" target="_blank" rel="noopener">test</a>',
                )
            ]
        )

    def test_remove_everything(self):
        sanitizer = Sanitizer(
            {"tags": {"__never"}, "attributes": {}, "empty": set(), "separate": set()}
        )

        self.run_tests(
            [
                (
                    '<span style="color:#000000;font-weight:bold">11:44:14</span>',
                    "11:44:14",
                )
            ],
            sanitizer=sanitizer,
        )

    def test_more_merging(self):
        self.run_tests(
            [
                ("<p><hr></p>", "<hr>"),
                ("<hr><hr><hr>", "<hr>"),
                (
                    '<a name="a"></a><a name="b"></a>',
                    '<a name="a"></a><a name="b"></a>',
                ),
            ]
        )

    def test_keep_consecutive_br_tags(self):
        sanitizer = Sanitizer({"whitespace": set(), "separate": {"br"}})
        self.run_tests(
            [
                ("<p>Hello<br><br>World</p>", "<p>Hello<br><br>World</p>"),
                ("<p>Hello<br><br></p>", "<p>Hello<br><br></p>"),
                ("<p><br><br>World</p>", "<p><br><br>World</p>"),
                ("<p><br><br></p>", "<p><br><br></p>"),
                ("<p><br></p><hr><br></p>", "<p><br></p><hr><br>"),
            ],
            sanitizer=sanitizer,
        )

    def test_custom_allowed_attribute(self):
        sanitizer = Sanitizer({"attributes": {"a": ("href", "custom")}})
        self.run_tests(
            [
                (
                    '<a href="http://example.com" custom="1" abc="2">Test</a>',
                    '<a href="http://example.com" custom="1">Test</a>',
                )
            ],
            sanitizer=sanitizer,
        )

    def test_blob(self):
        source = """\
<p class="western" style="margin-left: 0.39in; text-indent: -0.39in; margin-top: 0.25in; margin-bottom: 0in; line-height: 0.19in" lang="de-DE" align="justify">
<font style="font-size: 12pt" size="3"><b>1.2.	Definition des
Spesenbegriffs</b></font></p>
<p class="western" style="margin-left: 0.39in; margin-top: 0.13in; margin-bottom: 0in; line-height: 0.19in" lang="de-DE" align="justify">
<font style="font-size: 12pt" size="3">Als Spesen im Sinne dieses
Reglements gelten die Auslagen, die einem Mitarbeitenden im Interesse
des Arbeitgebers angefallen sind. Sämtliche Mitarbeitende sind
verpflichtet, ihre Spesen im Rahmen dieses Reglements möglichst tief
zu halten. Aufwendungen, die für die Arbeitsausführung nicht
notwendig waren, werden von der Firma nicht übernommen, sondern sind
von den Mitarbeitenden selbst zu tragen.</font></p>
<p class="western" style="margin-left: 0.39in; margin-top: 0.13in; margin-bottom: 0in; line-height: 0.19in" lang="de-DE" align="justify">
<font style="font-size: 12pt" size="3">Im Wesentlichen werden den
Mitarbeitenden folgende geschäftlich bedingten Auslagen ersetzt:</font></p>
<ul><li><p class="western" style="margin-top: 0.13in; margin-bottom: 0in; line-height: 0.19in" lang="de-DE" align="justify"> <font style="font-size: 12pt" size="3">-	Fahrtkosten					(nachfolgend 2.)</font></p> </li><li><p class="western" style="margin-bottom: 0in; line-height: 0.19in" lang="de-DE" align="justify"> <font style="font-size: 12pt" size="3">-	Verpflegungskosten			(nachfolgend 3.)</font></p> </li><li><p class="western" style="margin-bottom: 0in; line-height: 0.19in" lang="de-DE" align="justify"> <font style="font-size: 12pt" size="3">-	Übernachtungskosten			(nachfolgend 4.)</font></p> </li><li><p class="western" style="margin-bottom: 0in; line-height: 0.19in" lang="de-DE" align="justify"> <font style="font-size: 12pt" size="3">-	Übrige Kosten				(nachfolgend 5.)</font></p> </li></ul>"""  # noqa

        result = """\
<p> <strong>1.2. Definition des Spesenbegriffs</strong></p> <p> Als Spesen im Sinne dieses Reglements gelten die Auslagen, die einem Mitarbeitenden im Interesse des Arbeitgebers angefallen sind. Sämtliche Mitarbeitende sind verpflichtet, ihre Spesen im Rahmen dieses Reglements möglichst tief zu halten. Aufwendungen, die für die Arbeitsausführung nicht notwendig waren, werden von der Firma nicht übernommen, sondern sind von den Mitarbeitenden selbst zu tragen.</p> <p> Im Wesentlichen werden den Mitarbeitenden folgende geschäftlich bedingten Auslagen ersetzt:</p> <ul><li> - Fahrtkosten (nachfolgend 2.) </li><li> - Verpflegungskosten (nachfolgend 3.) </li><li> - Übernachtungskosten (nachfolgend 4.) </li><li> - Übrige Kosten (nachfolgend 5.) </li></ul>"""  # noqa

        # XXX An exact match isn't really required. Using Django's
        # assertHTMLEqual would be great but we'd have to depend on Django in
        # the test suite for this (not a big problem really, because then we
        # could also test html_sanitizer.django but I didn't yet *have* to do
        # this)
        self.run_tests([(source, result)])
