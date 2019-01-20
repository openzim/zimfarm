import docker
import docker.errors
from pathlib import Path

from .base import Base
from ..operations import RunRedis, RunMWOffliner, Upload
from ..utils import Settings


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
            run_redis = RunRedis(docker_client=docker.from_env(), container_name=Settings.redis_name)
            run_redis.execute()

            run_mwoffliner = RunMWOffliner(
                docker_client=docker.from_env(), tag=offliner_image_tag, flags=offliner_flags,
                task_id=self.task_id, working_dir_host=Settings.working_dir_host,
                redis_container_name=Settings.redis_name)
            self.logger.info('{name}[{id}] -- Running MWOffliner, mwUrl: {mwUrl}'.format(
                name=self.name, id=self.task_id, mwUrl=offliner_flags['mwUrl']))
            run_mwoffliner.execute()

            stats = self.get_file_stats()

            upload = Upload(warehouse_path, working_dir=Settings.working_dir_container,
                            short_task_id=self.task_id)
            self.logger.info('{name}[{id}] -- Upload files'.format(name=self.name, id=self.task_id))
            upload.execute()

            return stats
        except docker.errors.APIError:
            pass
        except docker.errors.ImageNotFound:
            pass
        except docker.errors.ContainerError as error:
            # error.stderr
            pass

    def get_file_stats(self):
        stats = []
        working_dir = Path(Settings.working_dir_container).joinpath(self.task_id)
        for file in working_dir.iterdir():
            if file.is_dir():
                continue
            stats.append({'name': file.name, 'size': file.stat().st_size})
        return stats
