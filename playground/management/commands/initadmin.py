from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
import dotenv
from playground.models import Preferences, DateTimeCheck
from datetime import datetime, timedelta

dotenv_file = os.path.join(settings.BASE_DIR, ".env")
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

User = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **options):

        if User.objects.filter(is_superuser=True).count() == 0:
            
            username = os.environ['ADMIN_NAME']
            password = os.environ['ADMIN_PASSWORD']
            print('Creating account for %s' % (username))
            admin = User.objects.create_superuser(
                username=username, password=password, is_active=True)
        else:
            print('Admin accounts can only be initialized if no Accounts exist')
            
        if Preferences.objects.all().count() == 0:
            print("creating preferance obj")
            Preferences.objects.create()
        else:
            print('Preferance can only be initialized if no Preferance exist')

        if DateTimeCheck.objects.all().count() == 0:
            print("creating datetime obj")
            DateTimeCheck.objects.create(dateCheck=(datetime.now() - timedelta(hours=12, minutes=30)).date())
        else:
            print('DateTimeCheck can only be initialized if no DateTimeCheck obj exist')



