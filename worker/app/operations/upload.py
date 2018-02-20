import ftplib
from time import sleep
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .operation import Operation


class Upload(Operation):
    """Upload zim files to server
    """

    name = 'Upload Zim File'

    def __init__(self, working_dir: Path, dispatcher_host: str, warehouse_host: str, username: str, password: str):
        super().__init__()
        self.working_dir: Path = working_dir

        self.dispatcher_host: str = dispatcher_host
        self.warehouse_host: str = warehouse_host
        self.username: str = username
        self.password: str = password
        self.token = None

    def execute(self):
        try:
            self._get_token()
            for path in self.working_dir.iterdir():
                if path.is_file() and path.suffix == '.zim':
                    self._upload(path)
                path.unlink()
            self.working_dir.rmdir()
            self.success = True
            print(self.token, flush=True)
        except HTTPError as e:
            self.success = False
            self.error_domain = 'operations.upload.token.HTTPError'
            self.error_code = e.code
            self.error_message = str(e)
        except FileUploadError as e:
            self.success = False
            self.error_domain = 'operations.upload.FileUploadError'
            self.error_message = str(e)

    def _get_token(self):
        url = 'https://{host}/api/auth/authorize'.format(host=self.dispatcher_host)
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
        payload = 'username={username}&password={password}'.format(username=self.username, password=self.password)
        request = Request(url, payload.encode('utf-8'), headers, method='POST')

        with urlopen(request, timeout=30) as response:
            self.token = response.read().decode('utf-8')

    def _upload(self, path: Path):
        print(str(path), flush=True)
        retries = 3
        while retries > 0:
            try:
                with ftplib.FTP(self.warehouse_host, self.username, self.token) as ftp:
                    with open(path, 'rb') as file:
                        ftp.storbinary('STOR {}'.format(path.name), file)
                break
            except ConnectionRefusedError:
                sleep(5)
                retries -= 1
        else:
            raise FileUploadError(path)


class FileUploadError(Exception):
    def __init__(self, path: Path):
        super().__init__()
        self.path = path

    def __str__(self):
        return "Unable to upload file {}.".format(self.path.name)