from __future__ import absolute_import

from collections import Iterable
from socket import getaddrinfo
from json import loads

from django.conf import settings
from django.utils import six

from docker.client import Client
from docker.utils import kwargs_from_env, create_host_config

from db_quick_setup import find_docker_host


class Backend(object):

    def __init__(self, command, db_name, db_conf):
        super(Backend, self).__init__()
        self.command = command
        self.db_name = db_name
        self.db_conf = db_conf

        assert_host = getattr(settings, 'DOCKER_ASSERT_HOSTNAME', True)
        if not assert_host:
            self.write("Warning: DOCKER_ASSERT_HOSTNAME is disabled")
        self.docker = Client(**kwargs_from_env(assert_hostname=assert_host))

        self.image = getattr(settings, self.__class__.image_setting,
                             self.__class__.image_default)

        self.port = str(self.db_conf.get('PORT', ''))
        if not self.port:
            self.port = self.__class__.default_port
        self.port = int(self.port)

        self.host = self.db_conf.get('HOST')
        self.user = self.db_conf.get('USER')
        self.password = self.db_conf.get('PASSWORD')
        self.database = self.db_conf.get('NAME')

        self.env = []
        for var in ['user', 'password', 'database']:
            env_vars = getattr(self.__class__, var + '_env', [])
            if isinstance(env_vars, str):
                env_vars = [env_vars]
            for env in env_vars:
                self.env.append('{}={}'.format(env, getattr(self, var)))

        self.internal_port = str(self.__class__.default_port) + '/tcp'
        self.host_port = str(self.port) + '/tcp'

        self.docker_host = find_docker_host()
        if getaddrinfo(self.docker_host, None) == \
                getaddrinfo('127.0.0.1', None):
            self.host_port = ('127.0.0.1', self.host_port)

    def validate(self):
        if (getaddrinfo(self.host, self.port) !=
                getaddrinfo(self.docker_host, self.port)):
            self.write("'HOST' points to a machine other than where Docker is")

    def is_port_exposed(self, image_id):
        info = self.docker.inspect_image(image_id)
        return self.internal_port in info.get('Config').get('ExposedPorts')

    def get_images(self):
        return [i.get('Id') for i in self.docker.images()
                if (self.image in i.get('RepoTags') or
                    self.image == i.get('Id')) and
                self.is_port_exposed(i.get('Id'))]

    def get_images_or_pull(self):
        images = self.get_images()
        if not images:
            self.write("Image '%s' is not found. Trying to pull." % self.image)
            prev_status = None
            for output in self.docker.pull(self.image, stream=True):
                if six.PY3:
                    output = output.decode('utf-8')
                output = loads(output)
                status = output.get('status')
                if status != prev_status:
                    self.write(status)
                    prev_status = status
            images = self.get_images()
        return images

    def is_good_container(self, container_id, images, show_diff=False):
        info = self.docker.inspect_container(container_id)

        if info.get('Image') not in images:
            if show_diff:
                self.write("Image '{}' isn't in '{}'".format(info.get('Image'),
                                                             images))
            return False

        port_bindings = info.get('HostConfig').get('PortBindings')
        port_binding = port_bindings.get(self.internal_port, None)
        if not port_binding:
            if show_diff:
                self.write("Port binding doesn't exist!")
            return False
        host_port = self.host_port
        host_ip = None
        if isinstance(host_port, tuple):
            host_ip = host_port[0]
            host_port = host_port[1]
        real_host_port = port_binding[0].get('HostPort')
        if real_host_port != host_port:
            if show_diff:
                self.write("HostPort: '{}' != '{}'".format(real_host_port,
                                                           host_port))
            return False
        real_host_ip = port_binding[0].get('HostIp')
        if host_ip and real_host_ip != host_ip:
            if show_diff:
                self.write("HostIp: '{}' != '{}'".format(real_host_ip,
                                                         host_ip))
            return False

        env = info.get('Config').get('Env')
        for var in self.env:
            if var not in env:
                return False
        return True

    def setup(self):
        self.validate()
        images = self.get_images_or_pull()
        containers = [i.get('Id') for i in self.docker.containers(all=True)
                      if self.is_good_container(i.get('Id'), images)]
        online = [i.get('Id') for i in self.docker.containers()
                  if i.get('Id') in containers]
        if online:
            self.write("Container '%s' is already running. Nothing to do." %
                       online[0])
            return
        if containers:
            container = containers[0]
        else:
            self.write("Creating a new container...")
            port_bindings = {self.internal_port: self.host_port}
            privileged = getattr(settings, 'DOCKER_PRIVILEGED', False)
            host_config = create_host_config(port_bindings=port_bindings,
                                             privileged=privileged)
            container = self.docker.create_container(images[0],
                                                     environment=self.env,
                                                     host_config=host_config)
            container = container.get('Id')
            if not self.is_good_container(container, images, True):
                self.write("Container %s isn't good!" % container)
                return False
        self.write("Starting container '%s'..." % container)
        self.docker.start(container)

        info = self.docker.inspect_container(container)
        if info.get('State').get('Running') != True:
            self.write("Container '%s' didn't start." % container)
            error = info.get('State').get('Error')
            if error:
                self.write("Error: %s" % error)

    def write(self, message):
        self.command.stderr.write("Database {}: {}".format(self.db_name,
                                                           message))

    def close(self):
        if self.docker:
            self.docker.close()
