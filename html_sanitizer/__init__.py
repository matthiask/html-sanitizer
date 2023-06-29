import contextlib


__version__ = "2.1.0"


with contextlib.suppress(ImportError):
    from .sanitizer import *  # noqa: F403
