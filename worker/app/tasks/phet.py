from pathlib import Path

import docker
import docker.errors
from celery.utils.log import get_task_logger

from operations import RunPhet
from utils import Settings
from .base import Base

logger = get_task_logger(__name__)


class Phet(Base):
    """Phet zimfarm task. This task have two steps:

    - generate zim files using phet (for all languages at once)
    - upload generated zim files

    Steps will be executed one after another.
    """

    name = 'offliner.phet'

    def run(self, flags: dict, image: dict, warehouse_path: str, *args, **kwargs):
        """Run Phet based offliner tasks.

        :param flags: offliner flags (phet has none)
        :param image: offliner image name and tag
        :param warehouse_path: folder to upload files into
        :return:
        """

        image_tag = image.get('tag', 'latest')
        working_dir_container = Path(Settings.working_dir_container).joinpath(self.task_id)

        try:
            # run phet
            run_phet = RunPhet(
                docker_client=docker.from_env(), tag=image_tag, flags=flags,
                task_id=self.task_id, working_dir_host=Settings.working_dir_host)
            logger.info(f'Running Phet')
            logger.debug(f'Running Phet, command: {run_phet.command}')
            self.send_event('task-container_started', image=image, command=run_phet.command)

            result = run_phet.execute()
            logger.info(f'Phet finished, exit code: {result.exit_code}')
            self.send_event('task-container_finished', exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr)

            if not result.is_successful():
                raise Exception(str(result))

            # upload files
            files = self.upload_zims(remote_working_dir=warehouse_path, directory=working_dir_container)

            return files
        except docker.errors.APIError as e:
            raise self.retry(exc=e)
        except (docker.errors.ContainerError, docker.errors.ImageNotFound) as e:
            raise Exception from e
