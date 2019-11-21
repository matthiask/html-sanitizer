from __future__ import unicode_literals


VERSION = (1, 8, 0)
__version__ = ".".join(map(str, VERSION))


try:
    from .sanitizer import *  # noqa
except ImportError:  # noqa
    pass
