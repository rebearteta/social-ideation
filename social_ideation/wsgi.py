"""
WSGI config for social_ideation project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

#path='/home/ubuntu/participa/social-ideation'

#if path not in sys.path:
#    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_ideation.settings")

application = get_wsgi_application()
