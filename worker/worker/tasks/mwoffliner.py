import docker

from .base import Base, TaskFailed
from ..operations import RunRedis, PullContainer, RunMWOffliner, Upload
from ..utils import Setting


class MWOffliner(Base):
    """MWOffliner zimfarm task. This task have four steps:

    - run redis
    - pull latest mwoffliner container
    - generate zim file using mwoffliner
    - upload generated zim file

    Steps will be executed one after another.
    """

    name = 'mwoffliner'

    def run(self, offliner_config):
        if Setting.interactive:
            zim_files_dir = Setting.working_dir.joinpath(self.request.id)
        else:
            zim_files_dir = Setting.container_inside_files_dir.joinpath(self.request.id)

        operations = [
            RunRedis(docker_client=docker.from_env(), container_name=Setting.redis_name),
            PullContainer(docker_client=docker.from_env(), image_name='openzim/mwoffliner'),
            RunMWOffliner(docker_client=docker.from_env(), config=offliner_config, task_id=self.request.id,
                          working_dir=Setting.working_dir, redis_container_name=Setting.redis_name),
            # Upload(zim_files_dir, Setting.dispatcher_host, Setting.warehouse_host,
            #        Setting.warehouse_command_port, Setting.username, Setting.password)
        ]
        logs = [] 
        success = True

        for index, operation in enumerate(operations):
            self.logger.info('Step {} of {}: {}'.format(index+1, len(operations), operation.name))
            operation.execute()
            log = operation.log
            logs.append(log)

            success = success and operation.success
            if not operation.success:
                break

        self.send_event('task-logs', logs=logs)

        if not success:
            raise TaskFailed()
