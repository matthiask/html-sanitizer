import contextlib


VERSION = (1, 9, 3)
__version__ = ".".join(map(str, VERSION))


with contextlib.suppress(ImportError):
    from .sanitizer import *  # noqa: F403
