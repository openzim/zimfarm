import shutil
from pathlib import Path

from celery.task import Task
from celery.utils.log import get_task_logger

from utils import Settings
from operations import Upload

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

    def clean_up(self):
        working_dir = Path(Settings.working_dir_container).joinpath(self.task_id)
        shutil.rmtree(working_dir)

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

    def on_success(self, retval, task_id, args, kwargs):
        self.clean_up()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.clean_up()

    def upload_zims(self, remote_working_dir: str, files: list = None, directory: Path = None):
        return Upload.upload(f'/zim{remote_working_dir}', files, directory)
