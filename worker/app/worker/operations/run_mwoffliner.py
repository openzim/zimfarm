from pathlib import Path

from docker import DockerClient
import docker.errors
from .base import Operation, Error


class RunMWOffliner(Operation):
    """Run MWOffliner container with `config`
    """

    name = 'Run Offliner'

    def __init__(self, docker_client: DockerClient, config: {}, short_task_id: str, working_dir_host: str,
                 redis_container_name: str):
        super().__init__()
        self.docker = docker_client
        self.config = config
        self.short_task_id = short_task_id
        self.working_dir_host = Path(working_dir_host)
        self.redis_container_name = redis_container_name
        self.image_name = 'openzim/mwoffliner:latest'

    def execute(self):
        """Run mwoffliner container

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        :raise: docker.errors.ContainerError
        """

        volumes = {self.working_dir_host.joinpath(self.short_task_id).absolute(): {'bind': '/output', 'mode': 'rw'}}
        self.std_out = self.docker.containers.run(image=self.image_name,
                                                  command=self._get_command(self.config),
                                                  remove=True, volumes=volumes,
                                                  links={self.redis_container_name: 'redis'},
                                                  name='mwoffliner_{}'.format(self.short_task_id))

    @staticmethod
    def _get_command(config: {}):
        config['redis'] = 'redis://redis'
        config['outputDirectory'] = '/output'
        params: [str] = []
        for key, value in config.items():
            if value is True:
                params.append('--{name}'.format(name=key))
            else:
                params.append('--{name}={value}'.format(name=key, value=value))
        return 'mwoffliner {}'.format(' '.join(params))
