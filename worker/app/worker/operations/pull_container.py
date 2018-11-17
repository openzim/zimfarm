from docker import DockerClient
import docker.errors
from .base import Operation, Error


class PullContainer(Operation):
    """Pull container with `image_name`.
    """

    name = 'pull_container'

    def __init__(self, docker_client: DockerClient, image_name: str):
        super().__init__()
        self.docker = docker_client
        self.image_name = image_name

    def execute(self):
        """

        :raise: docker.errors.APIError
        """
        self.docker.images.pull(self.image_name, tag='latest')
