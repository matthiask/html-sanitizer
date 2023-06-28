import contextlib


__version__ = "1.9.3"


with contextlib.suppress(ImportError):
    from .sanitizer import *  # noqa: F403
