import asyncio
from pathlib import Path

from docker import DockerClient
from docker.models.containers import Container

from .base import Operation, ContainerResult


class RunMWOffliner(Operation):
    """Run MWOffliner container with `config`"""

    def __init__(self, docker_client: DockerClient, tag: str, flags: {}, task_id: str, working_dir_host: str,
                 redis_container: Container, dns: str):
        tag = 'latest' if not tag else tag
        super().__init__()
        self.docker = docker_client
        self.command = self._get_command(flags)
        self.task_id = task_id
        self.working_dir_host = Path(working_dir_host).joinpath(self.task_id).absolute()
        self.redis_container = redis_container
        self.image_name = 'openzim/mwoffliner:{}'.format(tag)
        self.image_tag = tag
        self.dns = dns

    def execute(self) -> ContainerResult:
        """Pull and run mwoffliner"""

        # pull mwoffliner image
        self.docker.images.pull(self.image_name)

        # run mwoffliner
        volumes = {self.working_dir_host: {'bind': '/output', 'mode': 'rw'}}
        container: Container = self.docker.containers.run(
            image=self.image_name, command=self.command, volumes=volumes, detach=True,
            links={self.redis_container.name: 'redis'}, name=f'mwoffliner_{self.task_id}', dns=self.dns)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._wait_for_finish(container.id))

        container.reload()
        exit_code = container.attrs['State']['ExitCode']
        stdout = container.logs(stdout=True, stderr=False, tail=100).decode("utf-8")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
        result = ContainerResult(self.image_name, self.command, exit_code, stdout, stderr)

        container.remove()

        return result

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
                    params.append('--{name}="{value}"'.format(name=key, value=item))
            else:
                params.append('--{name}="{value}"'.format(name=key, value=value))
        return 'mwoffliner {}'.format(' '.join(params))
