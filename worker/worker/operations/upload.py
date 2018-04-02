import json
import ftplib
from time import sleep
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .operation import Operation, Error


class Upload(Operation):
    """Upload zim files to server
    """

    name = 'Upload Zim File'

    def __init__(self, zim_files_dir: Path, dispatcher_host: str, warehouse_host: str, warehouse_command_port: int,
                 username: str, password: str):
        super().__init__()
        self.zim_files_dir: Path = zim_files_dir

        self.dispatcher_host: str = dispatcher_host
        self.warehouse_host: str = warehouse_host
        self.warehouse_command_port: int = warehouse_command_port
        self.username: str = username
        self.password: str = password
        self.token = None

    def execute(self):
        try:
            self._get_token()
            for path in self.zim_files_dir.iterdir():
                if path.is_file() and path.suffix == '.zim':
                    self._upload(path)
                path.unlink()
            self.zim_files_dir.rmdir()
            self.success = True
        except HTTPError as e:
            self.success = False
            self.error = Error('upload.token.HTTPError', e.code, str(e))
        except ConnectionRefusedError as e:
            self.success = False
            self.error = Error('upload.ftp.ConnectionRefusedError', message=str(e))

    def _get_token(self):
        url = 'https://{host}/api/auth/authorize'.format(host=self.dispatcher_host)
        headers = {'username': self.username,
                   'password': self.password}
        request = Request(url, headers=headers, method='POST')

        with urlopen(request, timeout=30) as response:
            response_json = json.loads(response.read(), encoding='utf-8')
            self.token = response_json['access_token']

    def _upload(self, path: Path):
        with ftplib.FTP() as ftp:
            ftp.connect(self.warehouse_host, self.warehouse_command_port, timeout=30)
            ftp.login(self.username, self.token)
            with open(path, 'rb') as file:
                ftp.storbinary('STOR {}'.format(path.name), file)

        # retries = 3
        # while retries > 0:
        #     try:
        #
        #         break
        #     except ConnectionRefusedError as error:
        #         retries -= 1
        #         sleep(5)
        # else:
        #     raise error
