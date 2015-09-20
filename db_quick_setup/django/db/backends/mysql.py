from .docker import Backend as DockerBackend


class Backend(DockerBackend):
    image_setting = 'DOCKER_MYSQL_IMAGE'
    image_default = 'mysql:latest'
    default_port = '3306'
    user_env = 'MYSQL_USER'
    password_env = ['MYSQL_PASSWORD', 'MYSQL_ROOT_PASSWORD']
    database_env = 'MYSQL_DATABASE'
