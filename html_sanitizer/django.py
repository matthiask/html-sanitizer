from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core import checks
from django.core.exceptions import ImproperlyConfigured

from .sanitizer import Sanitizer

try:
    from functools import lru_cache
except ImportError:  # pragma: no cover
    # Django versions older than 3.0
    from django.utils.lru_cache import lru_cache


def _get_sanitizer(name="default"):
    sanitizers = getattr(settings, "HTML_SANITIZERS", {})
    if name in sanitizers:
        return Sanitizer(sanitizers[name])
    elif name == "default":
        return Sanitizer()
    raise ImproperlyConfigured(
        "Unknown sanitizer %r, did you define HTML_SANITIZERS[%r] in your"
        " Django settings module?" % (name, name)
    )


get_sanitizer = lru_cache(maxsize=None)(_get_sanitizer)


@checks.register()
def check_configuration(app_configs, **kwargs):
    errors = []
    sanitizers = ["default"] + list(getattr(settings, "HTML_SANITIZERS", {}))
    for name in sorted(set(sanitizers)):
        try:
            _get_sanitizer(name)
        except TypeError as exc:
            errors.append(
                checks.Error(
                    "Invalid sanitizer configuration '%s': %s" % (name, exc),
                    id="html_sanitizer.E001",
                )
            )

    return errors
