from docker import DockerClient
import docker.errors
from .operation import Operation


class PullContainer(Operation):
    """Pull container with `image_name`.
    """

    name = 'Pull Container'

    def __init__(self, docker: DockerClient, image_name: str, ):
        super().__init__()
        self.docker = docker
        self.image_name = image_name

    def execute(self):
        try:
            self.docker.images.pull(self.image_name, tag='latest')
            self.success = True
        except docker.errors.APIError as e:
            self.success = False
            self.error_domain = 'docker.errors.APIError'
            self.error_code = e.status_code
            self.error_message = str(e)
        except Exception as e:
            self.success = False
            self.error_message = 'unknown error: {}'.format(e)
