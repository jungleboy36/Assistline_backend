from django.test import TestCase
from django.db import connection
from django.conf import settings

# Ensure settings are correctly loaded before database connection
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'demelo',
                'USER': 'root',
                'PASSWORD': '',
                'HOST': '127.0.0.1',
                'PORT': '3306',
                'OPTIONS': {'charset': 'utf8mb4'},
            }
        }
    )

class DatabaseConnectionTest(TestCase):
    def test_connection(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print('Database connected successfully!')
        except Exception as e:
            self.fail(f"Database connection test failed: {e}")
