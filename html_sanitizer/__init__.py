import contextlib


__version__ = "2.3.1"


with contextlib.suppress(ImportError):
    from .sanitizer import *  # noqa: F403
