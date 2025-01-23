"""
Minimal file so Sphinx can work with Django for autodocumenting.

Location: /docs/django_settings.py
"""

# SECRET_KEY for the documentation
SECRET_KEY = 'docs-super-secret'

GDAL_LIBRARY_PATH = None
GEOS_LIBRARY_PATH = None

# INSTALLED_APPS with these apps is necessary for Sphinx to build without warnings & errors
# Depending on your package, the list of apps may be different
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'haystack',
    # custom apps:
    "apps.deed",
    "apps.parcel",
    "apps.plat",
    "apps.zoon",
]

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr/tester',
    }
}