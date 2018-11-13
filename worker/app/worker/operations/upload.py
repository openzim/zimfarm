from pathlib import Path

from .operation import Operation
from ..utils.sftp import SFTPClient
from ..utils.settings import Settings


class Upload(Operation):
    def __init__(self, category: str, dir: Path):
        super().__init__()
        self.category = category
        self.dir = dir

    def execute(self):
        hostname = Settings.warehouse_hostname
        port = Settings.warehouse_port
        username = Settings.username
        private_key = Settings.private_key


        try:
            with Client(hostname, port, username, private_key) as client:


        with Client('farm.openzim.org', 1522, 'automactic', '/Users/chrisli/.ssh/id_rsa') as client:
            client.upload_file('wikipedia', '/Users/chrisli/Downloads/shields/I-93.png')