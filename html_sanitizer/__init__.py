import contextlib


__version__ = "2.4.3"


with contextlib.suppress(ImportError):
    from .sanitizer import *  # noqa: F403
