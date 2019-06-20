import re
import lzma
import tempfile
import logging
from pathlib import Path

from paramiko.ssh_exception import SSHException

from utils.settings import Settings
from utils.sftp import SFTPClient
from .base import Operation, UploadError

MAX_UPLOAD_LOG_LINES = 10 ** 6
logger = logging.getLogger(__name__)


class Upload(Operation):
    def __init__(self, remote_working_dir: str, files: [Path], delete: bool = False):
        """Initializer for upload operation

        :param remote_working_dir: path in warehouse to upload files
        :param files: list of paths to upload
        :param delete: whether to delete source file after upload
        """

        super().__init__()

        if not re.match(r'^/(zim|logs)/.*$', remote_working_dir):
            raise ValueError("can't upload elsewhere than /zim/ or /logs/")

        self.remote_working_dir = remote_working_dir
        self.files = files
        self.delete = delete

    def execute(self):
        hostname = Settings.warehouse_hostname
        port = Settings.warehouse_port
        username = Settings.username
        private_key = Settings.private_key

        try:
            with SFTPClient(hostname, port, username, private_key) as client:
                for file in self.files:
                    if file.is_dir():
                        continue
                    client.upload_file(self.remote_working_dir, file)

                    if self.delete:
                        file.unlink()
        except SSHException as e:
            raise UploadError(code='paramiko.Error', message=str(e))

    @staticmethod
    def upload_files(remote_working_dir: str, files: list = None, delete: bool = False):
        """upload either a list of files (Path) or all files of a directory (Path)"""

        stats = [{'name': file.name, 'size': file.stat().st_size} for file in files]
        files_desc = ','.join(['{name} - {size}'.format(**stat) for stat in stats])
        logger.info(f'Uploading files, {files_desc}')

        upload = Upload(remote_working_dir=remote_working_dir, files=files)
        upload.execute()

        return stats

    @staticmethod
    def upload_directory_content(remote_working_dir: str, directory: Path = None, delete: bool = False):
        """upload either a list of files (Path) or all files of a directory (Path)"""

        files = [file for file in directory.iterdir() if not file.is_dir()]

        return Upload.upload_files(remote_working_dir=remote_working_dir, files=files, delete=delete)

    @staticmethod
    def upload_log(container):
        """fetch, compress and upload the container's stdout to the warehouse"""

        # compress log output (using a 1M lines buffer to prevent swap)
        archive = Path(tempfile.gettempdir()).joinpath(container.name + '.log.xz')
        with lzma.open(archive, 'wb') as f:
            buff, count = (b'', 0)
            for line in container.logs(stdout=True, stderr=True, stream=True):
                buff += line
                count += 1
                if count > MAX_UPLOAD_LOG_LINES:
                    f.write(buff)
                    buff, count = (b'', 0)
            f.write(buff)

        # upload compressed file
        return Upload.upload_files('/logs/', files=[archive], delete=True)[-1]
