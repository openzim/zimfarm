import os
import paramiko

def upload():
    key = paramiko.RSAKey.from_private_key_file('/Users/chrisli/.ssh/id_rsa')
    transport = paramiko.Transport(('farm.openzim.org', 1522))
    transport.connect(username='automactic', pkey=key)

    sftp_client = paramiko.SFTPClient.from_transport(transport)
    dir = sftp_client.listdir('/')
    print(dir)

    sftp_client.mkdir('/wikipedia')
    sftp_client.chdir('/wikipedia')
    sftp_client.listdir()

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
        working_dir = '/' + category
        with paramiko.SFTPClient.from_transport(self.transport) as client:
            try:
                client.chdir(working_dir)
            except IOError:
                client.mkdir(working_dir)
                client.chdir(working_dir)

            remote_path = os.path.basename(os.path.normpath(file_path))
            client.put(localpath=file_path, remotepath=remote_path)


if __name__ == '__main__':
    with Client('farm.openzim.org', 1522, 'automactic', '/Users/chrisli/.ssh/id_rsa') as client:
        client.upload_file('wikipedia', '/Users/chrisli/Downloads/shields/I-93.png')
