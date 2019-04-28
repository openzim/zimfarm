import logging
from pathlib import Path

import docker
import docker.errors

from operations import RunRedis, RunMWOffliner, Upload
from utils import Settings
from .base import Base

logger = logging.getLogger(__name__)


class MWOffliner(Base):
    """MWOffliner zimfarm task. This task have four steps:

    - run redis
    - generate zim file using mwoffliner
    - upload generated zim file

    Steps will be executed one after another.
    """

    name = 'offliner.mwoffliner'

    def run(self, flags: dict, image: dict, warehouse_path: str, *args, **kwargs):
        """Run MWOffliner based offliner tasks.

        :param flags: offliner flags
        :param image: offliner image name and tag
        :param warehouse_path: path appending to files when uploading
        :return:
        """

        image_tag = image.get('tag', 'latest')
        working_dir_container = Path(Settings.working_dir_container).joinpath(self.task_id)

        try:
            # run redis
            run_redis = RunRedis(docker_client=docker.from_env(), container_name=Settings.redis_name)
            run_redis.execute()

            # run mwoffliner
            run_mwoffliner = RunMWOffliner(
                docker_client=docker.from_env(), tag=image_tag, flags=flags,
                task_id=self.task_id, working_dir_host=Settings.working_dir_host,
                redis_container_name=Settings.redis_name)
            self.logger.info(f'Running MWOffliner, mwUrl: {flags["mwUrl"]}')
            self.logger.debug(f'Running MWOffliner, command: {run_mwoffliner.command}')
            self.send_event('task-command', command=run_mwoffliner.command)

            result = run_mwoffliner.execute()
            self.logger.info(f'MWOffliner finished, mwUrl: {flags["mwUrl"]}, exit code: {result.exit_code}')
            self.send_event('task-container_finished', exit_code=result.exit_code, stdout=result.stdout,
                            stderr=result.stderr)

            if not result.is_successful():
                raise Exception(result)

            # upload files
            files, files_description = self.get_files(working_dir_container)
            self.logger.info('Uploading files, {}'.format(files_description))
            upload = Upload(remote_working_dir=warehouse_path, working_dir=working_dir_container)
            upload.execute()

            return files
        except docker.errors.APIError as e:
            raise self.retry(exc=e)
        except docker.errors.ContainerError as e:
            raise Exception from e
