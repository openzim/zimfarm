from pathlib import Path

import docker
import docker.errors
from celery.utils.log import get_task_logger

from operations import RunRedis, RunMWOffliner
from utils import Settings
from .base import Base

logger = get_task_logger(__name__)


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
            # run mwoffliner
            with RunRedis(docker_client=docker.from_env(), task_id=self.task_id) as redis_container:
                run_mwoffliner = RunMWOffliner(
                    docker_client=docker.from_env(), tag=image_tag, flags=flags,
                    task_id=self.task_id, working_dir_host=Settings.working_dir_host,
                    redis_container=redis_container, dns=self.get_dns())
                logger.info(f'Running MWOffliner, mwUrl: {flags["mwUrl"]}')
                logger.debug(f'Running MWOffliner, dns={run_mwoffliner.dns}, command: {run_mwoffliner.command}')

                self.send_event('task-container_started', image=image, command=run_mwoffliner.command)
                result = run_mwoffliner.execute()
                logger.info(f'MWOffliner finished, mwUrl: {flags["mwUrl"]}, exit code: {result.exit_code}')
                self.send_event('task-container_finished', exit_code=result.exit_code,
                                stdout=result.stdout, stderr=result.stderr,
                                log=result.log)

            if not result.is_successful():
                raise Exception(str(result))

            # upload files
            files = self.upload_zims(remote_working_dir=warehouse_path, directory=working_dir_container)

            return files
        except docker.errors.APIError as e:
            raise self.retry(exc=e)
        except docker.errors.ContainerError as e:
            raise Exception from e
