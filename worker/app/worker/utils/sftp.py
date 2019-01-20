import logging
from pathlib import Path
from typing import Union

import paramiko

logger = logging.getLogger(__name__)


class SFTPClient:
    def __init__(self, hostname: str, port: int, username: str, private_key: Union[str, paramiko.RSAKey]):
        """Create an instance of SFTP client.

        :param hostname: address of SFTP server
        :param port: port of SFTP server
        """

        self.username = username
        self.transport = paramiko.Transport((hostname, port))
        if isinstance(private_key, str):
            self.private_key = paramiko.RSAKey.from_private_key_file(private_key)
        else:
            self.private_key = private_key

    def __enter__(self):
        self.transport.connect(username=self.username, pkey=self.private_key)
        return self

    def __exit__(self, *args, **kwargs):
        self.transport.close()

    def upload_file(self, remote_working_dir: str, file_path: Path):
        """Upload a file to warehouse.

        :param remote_working_dir: zim file category
        :param file_path: local path of file need to upload
        """

        with paramiko.SFTPClient.from_transport(self.transport) as client:
            # create remote working dir if it does not exist
            try:
                client.chdir(remote_working_dir)
            except IOError:
                client.mkdir(remote_working_dir)
                client.chdir(remote_working_dir)

            # check if file already exist
            file_name = file_path.parts[-1]
            try:
                client.stat(file_name)
                return
            except IOError:
                pass

            # upload file to remote dir as a tmp file
            file_name_tmp = file_name + '.tmp'
            client.put(localpath=file_path, remotepath=file_name_tmp, confirm=True)

            # rename file back to original name
            client.rename(file_name_tmp, file_name)

    def list_dir(self, path: str):
        with paramiko.SFTPClient.from_transport(self.transport) as client:
            return client.listdir(path)
