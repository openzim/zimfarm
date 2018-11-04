import logging
import socket
import threading
import time
from typing import Optional

import paramiko

from warehouse import sftp


class Thread(threading.Thread):
    logger = logging.getLogger(__name__)

    def __init__(self, socket: socket.socket, address: (str, int), host_key: paramiko.RSAKey):
        super().__init__()
        self.daemon = True
        self.socket = socket
        self.address = address
        self.host_key = host_key
        self.channel: Optional[paramiko.Channel, None] = None

    def run(self):
        self.logger.info('Received incoming connection -- {}:{}'.format(self.address[0], self.address[1]))
        try:
            with paramiko.Transport(self.socket) as transport:
                transport.add_server_key(self.host_key)
                transport.set_subsystem_handler(name="sftp", handler=paramiko.SFTPServer, sftp_si=sftp.Handler)
                transport.start_server(server=sftp.Server())
                self.channel = transport.accept(timeout=90)

                while transport.is_active():
                    time.sleep(1)
        except paramiko.SSHException as e:
            self.logger.error(e)
