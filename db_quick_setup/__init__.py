from __future__ import absolute_import

from docker.utils import kwargs_from_env
from django.utils import six
from socket import getaddrinfo


def find_docker_host():
    url = kwargs_from_env().get('base_url', None)
    if url is None:
        return '127.0.0.1'

    host = six.moves.urllib.urlparse(url).hostname
    if not host:
        return '127.0.0.1'
    return getaddrinfo(host, None)[4][0]
