import os

import paramiko


class Client:
    def __init__(self, hostname: str, port: int, username: str, private_key: str):
        """Create an instance of SFTP client.

        :param hostname: address of SFTP server
        :param port: port of SFTP server
        """

        self.username = username
        self.private_key = paramiko.RSAKey.from_private_key_file(private_key)
        self.transport = paramiko.Transport((hostname, port))

    def __enter__(self):
        self.transport.connect(username=self.username, pkey=self.private_key)
        return self

    def __exit__(self, *args, **kwargs):
        self.transport.close()

    def upload_file(self, category: str, file_path: str):
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

            remote_path = os.path.basename(os.path.normpath(file_path))
            client.put(localpath=file_path, remotepath=remote_path)
