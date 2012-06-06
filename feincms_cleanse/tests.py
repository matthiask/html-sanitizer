from django.test import TestCase

from feincms_cleanse import cleanse_html


class CleanseTestCase(TestCase):
    def test_01_cleanse(self):

        entries = [
            (u'<p>&nbsp;</p>', u''),
            (u'<span style="font-weight: bold;">Something</span><p></p>',
                u'<strong>Something</strong>'),
            (u'<p>abc <span>def <em>ghi</em> jkl</span> mno</p>',
                u'<p>abc def <em>ghi</em> jkl mno</p>'),
            (u'<span style="font-style: italic;">Something</span><p></p>',
                u'<em>Something</em>'),
            (u'<p>abc<br />def</p>', u'<p>abc<br />def</p>'),
            (u'<p><p><p>&nbsp;</p> </p><p><br /></p></p>', u' '),
            ]

        for a, b in entries:
            self.assertEqual(cleanse_html(a), b)
