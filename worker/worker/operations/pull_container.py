from docker import DockerClient
import docker.errors
from .operation import Operation, Error


class PullContainer(Operation):
    """Pull container with `image_name`.
    """

    name = 'Pull Container'

    def __init__(self, docker_client: DockerClient, image_name: str):
        super().__init__()
        self.docker = docker_client
        self.image_name = image_name

    def execute(self):
        try:
            self.docker.images.pull(self.image_name, tag='latest')
            self.success = True
        except docker.errors.APIError as e:
            self.success = False
            self.error = Error('docker.errors.APIError', e.status_code, str(e))
