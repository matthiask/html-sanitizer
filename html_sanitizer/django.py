from functools import lru_cache

from django.conf import settings
from django.core import checks
from django.core.exceptions import ImproperlyConfigured

from .sanitizer import Sanitizer


def _get_sanitizer(name="default"):
    sanitizers = getattr(settings, "HTML_SANITIZERS", {})
    if name in sanitizers:
        return Sanitizer(sanitizers[name])
    elif name == "default":
        return Sanitizer()
    raise ImproperlyConfigured(
        f"Unknown sanitizer {name!r}, did you define HTML_SANITIZERS[{name!r}] in your"
        " Django settings module?"
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
                    f"Invalid sanitizer configuration '{name}': {exc}",
                    id="html_sanitizer.E001",
                )
            )

    return errors
