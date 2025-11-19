"""
ASGI config for Recipe API project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()

# ============================================================================
# Uvicorn/Daphne Configuration
# ============================================================================
# To run with Uvicorn:
#   uvicorn config.asgi:application --host 0.0.0.0 --port 8000
#
# To run with Daphne (for WebSocket support):
#   daphne -b 0.0.0.0 -p 8000 config.asgi:application
#
# For production with Uvicorn:
#   uvicorn \
#     --workers 4 \
#     --host 0.0.0.0 \
#     --port 8000 \
#     config.asgi:application