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

    def validate(self):
        if (getaddrinfo(self.host, self.port) !=
                getaddrinfo(find_docker_host(), self.port)):
            self.write("'HOST' points to a machine other than where Docker is")

    def is_port_exposed(self, image_id):
        info = self.docker.inspect_image(image_id)
        return self.internal_port in info.get('Config').get('ExposedPorts')

    def get_images(self):
        images = [i.get('Id') for i in self.docker.images()
                  if (self.image in i.get('RepoTags')
                      or self.image == i.get('Id'))
                  and self.is_port_exposed(i.get('Id'))]
        if not images:
            self.write("Image '%s' is not found. Trying to pull." % self.image)
            image_id = None
            for output in self.docker.pull(self.image, stream=True):
                if six.PY3:
                    output = output.decode('utf-8')
                output = loads(output)
                image_id = output.get('id', image_id)
                self.write(output.get('status'))
            if self.is_port_exposed(image_id):
                images = [image_id]
        return images

    def is_good_container(self, container_id, images):
        info = self.docker.inspect_container(container_id)

        if info.get('Image') not in images:
            return False

        port_bindings = info.get('HostConfig').get('PortBindings')
        port_binding = port_bindings.get(self.internal_port, None)
        if not port_binding:
            return False
        if port_binding[0].get('HostPort') != self.host_port:
            return False

        env = info.get('Config').get('Env')
        for var in self.env:
            if var not in env:
                return False
        return True

    def setup(self):
        self.validate()
        images = self.get_images()
        containers = [i for i in self.docker.containers(all=True)
                      if self.is_good_container(i.get('Id'), images)]
        online = [i for i in self.docker.containers()
                  if i in containers]
        if online:
            self.write("Container '%s' is already running. Nothing to do." %
                       online[0].get('Id'))
            return
        if containers:
            container = containers[0]
        else:
            self.write("Creating a new container...")
            port_bindings = {self.internal_port: self.host_port}
            host_config = create_host_config(port_bindings=port_bindings)
            container = self.docker.create_container(images[0],
                                                     environment=self.env,
                                                     host_config=host_config)
        container = container.get('Id')
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