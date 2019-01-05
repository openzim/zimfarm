import logging
import shutil
from pathlib import Path

from .base import Operation
from ..utils.settings import Settings
from ..utils.sftp import SFTPClient


class Upload(Operation):

    logger = logging.getLogger(__name__)

    def __init__(self, remote_working_dir: str, working_dir: str, short_task_id: str):
        super().__init__()
        self.remote_working_dir = remote_working_dir
        self.short_task_id = short_task_id
        self.working_dir = Path(working_dir).joinpath(short_task_id)

    def execute(self):
        hostname = Settings.warehouse_hostname
        port = Settings.warehouse_port
        username = Settings.username
        private_key = Settings.private_key

        try:
            with SFTPClient(hostname, port, username, private_key) as client:
                for file in self.working_dir.iterdir():
                    if file.is_dir():
                        continue
                    client.upload_file(self.remote_working_dir, file)
        except Exception:
            pass

        shutil.rmtree(self.working_dir)
