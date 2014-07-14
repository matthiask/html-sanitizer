#!/usr/bin/env python

import os
from setuptools import setup, find_packages


setup(
    name='feincms-cleanse',
    version='5',
    description='Default HTML cleansing in FeinCMS',
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Matthias Kestenholz',
    author_email='mk@feinheit.ch',
    url='http://github.com/feincms/feincms-cleanse/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=find_packages(),
    package_data={
        '': ['*.html', '*.txt'],
        'feincms_cleanse': [
            # 'locale/*/*/*.*',
            # 'static/email_registration/*.*',
            # 'static/email_registration/*/*.*',
            # 'templates/*.*',
            # 'templates/*/*.*',
            # 'templates/*/*/*.*',
            # 'templates/*/*/*/*.*',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
    ],
    install_requires=('lxml>=3', 'beautifulsoup4'),
)
