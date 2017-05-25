from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import lru_cache

from .sanitizer import Sanitizer


@lru_cache.lru_cache(maxsize=None)
def get_sanitizer(name='default'):
    sanitizers = getattr(settings, 'HTML_SANITIZERS', {})
    if name in sanitizers:
        return Sanitizer(sanitizers[name])
    elif name == 'default':
        return Sanitizer()
    raise ImproperlyConfigured(
        'Unknown sanitizer %r, did you define HTML_SANITIZERS[%r] in your'
        ' Django settings module?' % (name, name)
    )
