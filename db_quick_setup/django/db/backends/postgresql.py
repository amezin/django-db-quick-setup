from .docker import Backend as DockerBackend


class Backend(DockerBackend):
    image_setting = 'DOCKER_POSTGRES_IMAGE'
    image_default = 'postgres:latest'
    default_port = '5432'
    user_env = 'POSTGRES_USER'
    password_env = 'POSTGRES_PASSWORD'

    def validate(self):
        super(Backend, self).validate()

        if self.user != self.database:
            self.write("'NAME' should be the same as 'USER'. A database with "
                       "the name '{}' will be created instead.".
                       format(self.user))
