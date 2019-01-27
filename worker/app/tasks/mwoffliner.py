import logging
from pathlib import Path

import docker
import docker.errors

from operations.base import OfflinerError, UploadError
from .base import Base
from operations import RunRedis, RunMWOffliner, Upload
from utils import Settings

logger = logging.getLogger(__name__)


class MWOffliner(Base):
    """MWOffliner zimfarm task. This task have four steps:

    - run redis
    - generate zim file using mwoffliner
    - upload generated zim file

    Steps will be executed one after another.
    """

    name = 'offliner.mwoffliner'

    def run(self, offliner: dict, warehouse_path: str, *args, **kwargs):
        """Run MWOffliner based offliner tasks.

        :param offliner: offliner config
        :param warehouse_path: path appending to files when uploading
        :return:
        """

        offliner_image_tag = offliner.get('image_tag', 'latest')
        offliner_flags = offliner.get('flags', {})

        try:
            # run redis
            run_redis = RunRedis(docker_client=docker.from_env(), container_name=Settings.redis_name)
            run_redis.execute()

            # run mwoffliner
            run_mwoffliner = RunMWOffliner(
                docker_client=docker.from_env(), tag=offliner_image_tag, flags=offliner_flags,
                task_id=self.task_id, working_dir_host=Settings.working_dir_host,
                redis_container_name=Settings.redis_name)
            self.logger.info('{name}[{id}] -- Running MWOffliner, mwUrl: {mwUrl}'.format(
                name=self.name, id=self.task_id, mwUrl=offliner_flags['mwUrl']))
            self.logger.debug('{name}[{id}] -- Running MWOffliner, command: {command}'.format(
                name=self.name, id=self.task_id, command=run_mwoffliner.command))
            offliner_stdout = run_mwoffliner.execute()
            self.send_event('offliner_finished', offliner_stdout)

            # get stats of generated files
            working_dir_container = Path(Settings.working_dir_container).joinpath(self.task_id)
            stats = self.get_file_stats(working_dir_container)

            # upload files
            upload = Upload(remote_working_dir=warehouse_path, working_dir=working_dir_container)
            self.logger.info('{name}[{id}] -- Upload files'.format(name=self.name, id=self.task_id))
            upload.execute()

            return stats
        except OfflinerError as e:
            self.send_event('offliner_failed', e)
            raise e
        except UploadError as e:
            self.send_event('upload_failed', e)
            raise

    @staticmethod
    def get_file_stats(working_dir: Path):
        stats = []
        for file in working_dir.iterdir():
            if file.is_dir():
                continue
            stats.append({'name': file.name, 'size': file.stat().st_size})
        return stats
