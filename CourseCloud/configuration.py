from django.core.exceptions import ImproperlyConfigured


def parse_debug(value):
    """Accept boolean settings and the host's non-debug build mode."""
    text = str(value).strip().lower()
    if text in ('true', '1', 'yes', 'on'):
        return True
    if text in ('false', '0', 'no', 'off', '', 'release'):
        return False
    raise ImproperlyConfigured('LEARNORBIT_DEBUG must be True or False.')
