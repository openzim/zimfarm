from typing import Optional
from docker import DockerClient
from docker.models.containers import Container
import docker.errors
from .operation import Operation


class RunRedis(Operation):
    """Run redis container with `container_name` if no such container is already running.
    """

    name = 'Start Redis'

    def __init__(self, docker: DockerClient, container_name: str):
        super().__init__()
        self.docker = docker
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
        except docker.errors.APIError as e:
            self.success = False
            self.error_domain = 'docker.errors.APIError'
            self.error_code = e.status_code
            self.error_message = str(e)
        except Exception as e:
            self.success = False
            self.error_message = 'unknown error: {}'.format(e)

    def _get_container(self, container_name: str) -> Optional[Container]:
        try:
            return self.docker.containers.get(container_name)
        except docker.errors.NotFound:
            return None
