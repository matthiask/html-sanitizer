from django.test import TestCase

from feincms_cleanse import cleanse_html


class CleanseTestCase(TestCase):
    def run_tests(self, entries, **kwargs):
        for before, after in entries:
            after = before if after is None else after
            result = cleanse_html(before, **kwargs)
            self.assertEqual(result, after, u"Cleaning '%s', expected '%s' but got '%s'" % (before, after, result))

    def test_01_cleanse(self):

        entries = [
            (u'<p>&nbsp;</p>', u''),
            (u'<p>           </p>', u''),
            (u'<span style="font-weight: bold;">Something</span><p></p>',
                u'<strong>Something</strong>'),
            (u'<p>abc <span>def <em>ghi</em> jkl</span> mno</p>',
                u'<p>abc def <em>ghi</em> jkl mno</p>'),
            (u'<span style="font-style: italic;">Something</span><p></p>',
                u'<em>Something</em>'),
            (u'<p>abc<br />def</p>', u'<p>abc<br />def</p>'),
            ]

        self.run_tests(entries)

    def test_02_a_tag(self):
        entries = (
                    ('<a href="/foo">foo</a>', None),
                    ('<a href="/foo" target="some" name="bar" title="baz" cookies="yesplease">foo</a>', '<a href="/foo" target="some" name="bar" title="baz">foo</a>'),
                    ('<a href="http://somewhere.else">foo</a>', None),
                    ('<a href="https://somewhere.else">foo</a>', None),
                    ('<a href="javascript:alert()">foo</a>', '<a href="">foo</a>'),
                    ('<a href="javascript%2Dalert()">foo</a>', '<a href="">foo</a>'),
                  )

        self.run_tests(entries)

    def test_03_merge(self):
        entries = (
                   ('<h2>foo</h2><h2>bar</h2>', '<h2>foo bar</h2>'),
                   ('<h2>foo  </h2>   <h2>   bar</h2>', '<h2>foo bar</h2>'),
                  )

        self.run_tests(entries)

    def test_04_p_in_li(self):
        entries = (
                   ('<li><p>foo</p></li>', '<li>foo</li>'),
                   ('<li>&nbsp;<p>foo</p> &#160; </li>', '<li>foo</li>'),
                   ('<li>foo<p>bar</p>baz</li>', '<li>foo bar baz</li>'),
                  )

        self.run_tests(entries)

    def test_05_p_in_p(self):
        entries = (
                   (u'<p><p><p>&nbsp;</p> </p><p><br /></p></p>', u' '),
                   ('<p>foo<p>bar</p>baz</p>', '<p>foo bar baz</p>'),
                  )

        self.run_tests(entries)

    def test_06_whitelist(self):
        entries = (
                   (u'<script src="http://abc">foo</script>', u''),
                   (u'<script type="text/javascript">foo</script>', u''),
                  )

        self.run_tests(entries)

    def test_07_configuration(self):
        entries = (
                   ('<h1>foo</h1>', None),
                   ('<h1>foo</h1><h2>bar</h2><h3>baz</h3>', '<h1>foo</h1><h2>bar</h2>baz'),
                  )

        allowed_tags = { 'h1': (), 'h2': () }

        self.run_tests(entries, allowed_tags=allowed_tags)
