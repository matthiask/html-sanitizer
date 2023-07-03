import contextlib


__version__ = "2.2.0"


with contextlib.suppress(ImportError):
    from .sanitizer import *  # noqa: F403
