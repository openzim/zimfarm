import shutil
import signal
from pathlib import Path

import docker
from celery.task import Task
from celery.signals import task_revoked
from celery.utils.log import get_task_logger

from utils import Settings
from operations import Upload
from utils.docker import get_ip_address, remove_existing_container
from operations.run_dnscache import RunDNSCache

logger = get_task_logger(__name__)


class Base(Task):
    """Base class for all zimfarm celery tasks.
    """

    abstract = True
    resultrepr_maxsize = 1024000

    @property
    def task_id(self) -> str:
        return self.request.id

    def __init__(self):
        super().__init__()

    def set_up(self):
        # start a dnscache instance
        try:
            self.run_dnscache = RunDNSCache(docker_client=docker.from_env(),
                                            task_id=self.task_id)
            self.run_dnscache.execute()
            logger.info(f'Running DNSCache at {self.get_dns()[-1]}')
        except docker.errors.APIError as e:
            raise self.retry(exc=e)
        except (docker.errors.ContainerError, docker.errors.ImageNotFound) as e:
            raise Exception from e

    def get_dns(self):
        """list of DNS IPs to feed `dns` on scrappers with: [<dnscache_ip>]"""
        if not hasattr(self, 'run_dnscache') or self.task_id not in self.run_dnscache._container_name:
            self.set_up()

        return [get_ip_address(docker.from_env(), self.run_dnscache._container_name)]

    def clean_up(self):
        # ensure dnscache is stopped
        if self.run_dnscache:
            self.run_dnscache.stop()

        # remove working_dir
        working_dir = Path(Settings.working_dir_container).joinpath(self.task_id)
        shutil.rmtree(working_dir, ignore_errors=True)

    def on_success(self, retval, task_id, args, kwargs):
        self.clean_up()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.clean_up()

    def upload_zims(self, remote_working_dir: str, directory: Path = None):
        return Upload.upload_directory_content(f'/zim{remote_working_dir}', directory)


@task_revoked.connect
def on_revoked_task(sender=None, **kwargs):
    if not getattr(sender, 'name').startswith('offliner.'):
        return

    if not kwargs.get('signum') == signal.SIGTERM:
        return

    task_id = getattr(kwargs.get('request'), 'id')
    if task_id is None:
        return

    logger.info(f'on_revoked_task for #{task_id}')
    remove_existing_container(docker.from_env(), name=f'dnscache_{task_id}')
