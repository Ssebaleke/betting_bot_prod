import os
from django.core.wsgi import get_wsgi_application

# We simplified this from betting_bot.betting_bot.settings to just:
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "betting_bot.settings")

application = get_wsgi_application()