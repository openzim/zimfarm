from pathlib import Path

from docker import DockerClient

from .base import Operation


class RunMWOffliner(Operation):
    """Run MWOffliner container with `config`
    """

    name = 'Run Offliner'

    def __init__(self, docker_client: DockerClient, tag: str, flags: {}, task_id: str, working_dir_host: str,
                 redis_container_name: str):
        tag = 'latest' if not tag else tag
        super().__init__()
        self.docker = docker_client
        self.command = self._get_command(flags)
        self.task_id = task_id
        self.working_dir_host = Path(working_dir_host).joinpath(self.task_id).absolute()
        self.redis_container_name = redis_container_name
        self.image_name = 'openzim/mwoffliner:{}'.format(tag)

    def execute(self):
        """Pull and run mwoffliner

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        :raise: docker.errors.ContainerError
        """

        # pull mwoffliner image
        self.docker.images.pull(self.image_name)

        # run mwoffliner
        volumes = {self.working_dir_host: {'bind': '/output', 'mode': 'rw'}}
        self.std_out = self.docker.containers.run(image=self.image_name, command=self.command,
                                                  remove=True, volumes=volumes,
                                                  links={self.redis_container_name: 'redis'},
                                                  name='mwoffliner_{}'.format(self.task_id))

    @staticmethod
    def _get_command(flags: {}):
        flags['redis'] = 'redis://redis'
        flags['outputDirectory'] = '/output'
        params: [str] = []
        for key, value in flags.items():
            if value is True:
                params.append('--{name}'.format(name=key))
            elif isinstance(value, list):
                for item in value:
                    params.append('--{name}={value}'.format(name=key, value=item))
            else:
                params.append('--{name}={value}'.format(name=key, value=value))
        return 'mwoffliner {}'.format(' '.join(params))
