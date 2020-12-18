VERSION = (1, 9, 1)
__version__ = ".".join(map(str, VERSION))


try:
    from .sanitizer import *  # noqa
except ImportError:  # pragma: no cover
    pass
