import os
from pathlib import Path
import docker

from .base import Base, TaskFailed
from operations import RunRedis, PullContainer, RunMWOffliner, Upload


class MWOffliner(Base):
    """MWOffliner zimfarm task. This task have four steps:

    - run redis
    - pull latest mwoffliner container
    - generate zim file using mwoffliner
    - upload generated zim file
    """

    name = 'mwoffliner'

    def __init__(self):
        super().__init__()
        self.redis_container_name: str = os.getenv('REDIS_NAME', 'zimfarm_redis')
        self.working_dir: Path = Path(os.getenv('HOST_WORKING_DIR'))

        self.dispatcher_host: str = os.getenv('DISPATCHER_HOST')
        self.warehouse_host: str = os.getenv('WAREHOUSE_HOST')
        self.username: str = os.getenv('USERNAME')
        self.password: str = os.getenv('PASSWORD')

    def run(self, config, *args, **kwargs):
        working_dir = self.working_dir.joinpath(self.request.id)
        operations = [
            RunRedis(docker=docker.from_env(), container_name=self.redis_container_name),
            PullContainer(docker=docker.from_env(), image_name='openzim/mwoffliner'),
            RunMWOffliner(docker=docker.from_env(), config=config, task_id=self.request.id,
                          working_dir=working_dir, redis_container_name=self.redis_container_name),
            Upload(Path(os.getenv('CONTAINER_WORKING_DIR')).joinpath(self.request.id), self.dispatcher_host, self.warehouse_host, self.username, self.password)
        ]
        results = []

        for index, operation in enumerate(operations):
            self.logger.info('Step {} of {}: {}'.format(index+1, len(operations), operation.name))
            operation.execute()
            results.append(operation.result)
            if not operation.success:
                raise TaskFailed(results)

        return results
