from db_quick_setup import find_docker_host
from test_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgresql_db',
        'USER': 'postgresql_db',
        'PASSWORD': 'postgresql_db_pass',
        'HOST': find_docker_host(),
        'PORT': 53307
    }
}
