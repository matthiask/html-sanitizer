#!/usr/bin/env python

import os
from setuptools import find_packages, setup


setup(
    name="html-sanitizer",
    version=__import__("html_sanitizer").__version__,
    description="HTML sanitizer",
    long_description=open(os.path.join(os.path.dirname(__file__), "README.rst")).read(),
    author="Matthias Kestenholz",
    author_email="mk@feinheit.ch",
    url="https://github.com/matthiask/html-sanitizer/",
    license="BSD License",
    platforms=["OS Independent"],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development",
    ],
    install_requires=("lxml>=3.6.1", "beautifulsoup4"),
    test_suite="html_sanitizer.tests",
)
