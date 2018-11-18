import os
from typing import Union

import paramiko
from pathlib import Path

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

    def upload_file(self, category: str, file_path: Path):
        """Upload a file to warehouse.

        :param category: zim file category
        :param file_path: local path of file need to upload
        """
        working_dir = '/' + category
        with paramiko.SFTPClient.from_transport(self.transport) as client:
            try:
                client.chdir(working_dir)
            except IOError:
                client.mkdir(working_dir)
                client.chdir(working_dir)

            remote_path = file_path.parts[-1]
            client.put(localpath=file_path, remotepath=remote_path, confirm=True)

    def list_dir(self, path: str):
        with paramiko.SFTPClient.from_transport(self.transport) as client:
            return client.listdir(path)
