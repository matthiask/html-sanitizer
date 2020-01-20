from __future__ import unicode_literals


VERSION = (1, 9, 0)
__version__ = ".".join(map(str, VERSION))


try:
    from .sanitizer import *  # noqa
except ImportError:  # pragma: no cover
    pass
