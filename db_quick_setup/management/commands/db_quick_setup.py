from __future__ import absolute_import

from importlib import import_module
from sys import exc_info
from traceback import format_exc

from django.core.management.base import BaseCommand, CommandError
from django.utils.six import iteritems
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):

    requires_system_checks = False

    def handle(self, *args, **options):
        basepath = apps.get_app_config('db_quick_setup').module.__name__

        failed = False
        for name, conf in iteritems(settings.DATABASES):
            try:
                backend_name = '{}.{}'.format(basepath, conf.get('ENGINE'))
                backend = import_module(backend_name).Backend(self, name, conf)
                try:
                    backend.setup()
                finally:
                    backend.close()
            except:
                failed = True
                self.stderr.write("Setting up database '{}' failed: {}".
                                  format(name, format_exc()))
        if failed:
            raise CommandError("Setting up databases failed")
