import logging
import shutil
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
            self.logger.info('Running MWOffliner, mwUrl: {mwUrl}'.format(mwUrl=flags['mwUrl']))
            self.logger.debug('Running MWOffliner, command: {command}'.format(command=run_mwoffliner.command))
            run_mwoffliner.execute()
            files, files_description = self.get_files(working_dir_container)

            # upload files
            upload = Upload(remote_working_dir=warehouse_path, working_dir=working_dir_container)
            self.logger.info('Uploading files, {}'.format(files_description))
            upload.execute()

            return files
        except docker.errors.APIError as e:
            raise self.retry(exc=e)
        except docker.errors.ContainerError as e:
            self.send_event('task-container_error', exit_code=e.exit_status,
                            command=e.command, stderr=e.stderr.decode("utf-8"))
            raise Exception from e

    @staticmethod
    def get_files(working_dir: Path):
        stats = []
        description = []
        for file in working_dir.iterdir():
            if file.is_dir():
                continue
            stats.append({'name': file.name, 'size': file.stat().st_size})
            description.append('{name} - {size}'.format(name=file.name, size=file.stat().st_size))

        return stats, ', '.join(description)

    def clean_up(self):
        working_dir = Path(Settings.working_dir_container).joinpath(self.task_id)
        shutil.rmtree(working_dir)

    def on_success(self, retval, task_id, args, kwargs):
        self.clean_up()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.clean_up()
