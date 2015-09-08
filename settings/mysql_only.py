from db_quick_setup import find_docker_host
from test_settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mysql_db',
        'USER': 'mysql_db',
        'PASSWORD': 'mysql_db_pass',
        'HOST': find_docker_host(),
        'PORT': 53308
    }
}
