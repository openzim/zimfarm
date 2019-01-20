import logging
import shutil
from pathlib import Path
from paramiko.ssh_exception import SSHException

from .base import Operation
from ..utils.settings import Settings
from ..utils.sftp import SFTPClient


class Upload(Operation):

    logger = logging.getLogger(__name__)

    def __init__(self, remote_working_dir: str, working_dir: Path):
        """Initializer for upload operation

        :param remote_working_dir: path in warehouse to upload files
        :param working_dir: path to the dir containing zim files to upload inside container
        """

        super().__init__()
        self.remote_working_dir = remote_working_dir
        self.working_dir = working_dir

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
        except SSHException as e:
            pass

        shutil.rmtree(self.working_dir)
