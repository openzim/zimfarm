import os
from pathlib import Path

from docker import DockerClient
import docker.errors
from .operation import Operation


class RunMWOffliner(Operation):
    """Run MWOffliner container with `config`
    """

    name = 'Generate Zim File with MWOffliner'

    def __init__(self, docker: DockerClient, config: {}, task_id: str, working_dir: Path, redis_container_name: str):
        super().__init__()
        self.docker = docker
        self.config = config
        self.task_id = task_id
        self.working_dir = working_dir
        self.redis_container_name = redis_container_name
        self.image_name = 'openzim/mwoffliner'

    def execute(self):
        try:
            volumes = {os.fspath(self.working_dir): {'bind': '/output', 'mode': 'rw'}}
            self.std_out = self.docker.containers.run(image=self.image_name,
                                                      command=self._get_command(self.config),
                                                      remove=True, volumes=volumes,
                                                      links={self.redis_container_name: 'redis'},
                                                      name='mwoffliner_{}'.format(self.task_id))
            self.success = True
        except docker.errors.APIError as e:
            self.success = False
            self.error_domain = 'docker.errors.APIError'
            self.error_code = e.status_code
            self.error_message = str(e)
        except:
            self.success = False

    def _get_command(self, config: {}):
        config['redis'] = 'redis://redis'
        config['outputDirectory'] = '/output'
        params: [str] = []
        for key, value in config.items():
            if isinstance(value, bool) and value == True:
                params.append('--{name}'.format(name=key))
            else:
                params.append('--{name}={value}'.format(name=key, value=value))
        return 'mwoffliner {}'.format(' '.join(params))