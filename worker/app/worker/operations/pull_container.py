from docker import DockerClient

from .base import Operation


class PullContainer(Operation):

    name = 'pull_container'

    def __init__(self, docker_client: DockerClient, image_name: str):
        super().__init__()
        self.docker = docker_client
        self.image_name = image_name

    def execute(self):
        """Pull container with `image_name`, lagged 'latest'.

        :raise: docker.errors.APIError
        """
        self.docker.images.pull(self.image_name, tag='latest')
