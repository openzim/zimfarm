import docker
import docker.errors

from .base import Base, TaskFailed
from ..operations import RunRedis, PullContainer, RunMWOffliner, Upload
from ..utils import Settings

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
        operations = [
            RunRedis(docker_client=docker.from_env(), container_name=Settings.redis_name),
            PullContainer(docker_client=docker.from_env(), image_name='openzim/mwoffliner'),
            # RunMWOffliner(docker_client=docker.from_env(), config=offliner_config, short_task_id=self.short_task_id,
            #               working_dir_host=Settings.working_dir_host, redis_container_name=Settings.redis_name),
        ]

        for index, operation in enumerate(operations):
            self.logger.info('Task {}[{}] -- step {} of {}: {}'.format(
                self.name, self.short_task_id, index + 1, len(operations), operation.name))

            if isinstance(operation, RunMWOffliner):
                self.logger.info('{name}[{id}] -- Running MWOffliner, mwUrl: {mwUrl}'.format(
                    name=self.name, id=self.short_task_id, mwUrl=offliner_config['mwUrl']))

            try:
                operation.execute()
            except docker.errors.APIError:
                pass
            except docker.errors.ImageNotFound:
                pass


        # operations = [

        #     # Upload(zim_files_dir, Setting.dispatcher_host, Setting.warehouse_host,
        #     #        Setting.warehouse_command_port, Setting.username, Setting.password)
        # ]
        # logs = []
        # success = True
        #
        # for index, operation in enumerate(operations):
        #     self.logger.info('Step {} of {}: {}'.format(index+1, len(operations), operation.name))
        #     operation.execute()
        #     # log = operation.log
        #     # logs.append(log)
        #
        #     success = success and operation.success
        #     if not operation.success:
        #         break
        #
        # # self.send_event('task-logs', logs=logs)
        #
        # if not success:
        #     raise TaskFailed()
