from typing import Optional
from docker import DockerClient
from docker.models.containers import Container
import docker.errors
from .operation import Operation, Error


class RunRedis(Operation):
    """Run redis container with `container_name` if no such container is already running.
    """

    name = 'Start Redis'

    def __init__(self, docker_client: DockerClient, container_name: str):
        super().__init__()
        self.docker = docker_client
        self.container_name = container_name

    def execute(self):
        try:
            container = self._get_container(self.container_name)
            if container is not None:
                if container.status == 'running':
                    self.success = True
                    return
                else:
                    container.remove()

            self.docker.images.pull('redis', tag='latest')
            self.docker.containers.run('redis', detach=True, name=self.container_name)
            self.success = True
        except docker.errors.ImageNotFound as e:
            self.success = False
            self.error = Error('docker.errors.ImageNotFound', e.status_code, message=str(e))
        except docker.errors.APIError as e:
            self.success = False
            self.error = Error('docker.errors.APIError', e.status_code, message=str(e))

    def _get_container(self, container_name: str) -> Optional[Container]:
        try:
            return self.docker.containers.get(container_name)
        except docker.errors.NotFound:
            return None
