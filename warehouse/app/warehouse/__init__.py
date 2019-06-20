import logging
import os
import socket
import sys

import paramiko

from . import errors, sftp
from .threading import Thread


class Warehouse:
    logger = logging.getLogger(__name__)

    def __init__(self):
        pass

    def start(self):
        self.logger.info('Welcome to Zimfarm warehouse')

        self._configure_root_dir()
        key = self._get_private_key()
        sock = self._bind_socket()

        while True:
            try:
                client, address = sock.accept()
                thread = Thread(client, address, key)
                thread.start()
            except Exception as e:
                self.logger.error('Failed to accept incoming connection: %s', e)

    def _get_private_key(self) -> paramiko.RSAKey:
        try:
            path = os.getenv('RSA_KEY')
            if path is None:
                raise errors.MissingEnvironmentalVariable('RSA_KEY')

            key = paramiko.RSAKey(filename=path)
            self.logger.info('Using private key -- {}'.format(path))
            return key
        except (errors.MissingEnvironmentalVariable, FileNotFoundError, paramiko.SSHException) as e:
            self.logger.error(e)
            sys.exit(1)

    def _bind_socket(self) -> socket.socket:
        try:
            port = os.getenv('PORT', 22)
            if port is None:
                raise errors.MissingEnvironmentalVariable('PORT')
        except errors.MissingEnvironmentalVariable as e:
            self.logger.error(e)
            sys.exit(1)

        try:
            port = int(port)
        except ValueError:
            self.logger.error('Socket binding failed -- {} cannot be converted to integer'.format(port))
            sys.exit(1)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', port))
            sock.listen(10)
            self.logger.info('Listening on port {}'.format(port))
            return sock
        except Exception as e:
            self.logger.error('Socket binding failed -- {}'.format(e))
            sys.exit(1)

    @staticmethod
    def _configure_root_dir():
        """Create root dir if not exist and set root in `sftp.Handler`
        :return:
        """
        root = os.getenv('ROOT_PATH', '/files')

        for subdir_name in ('zim', 'logs'):
            subdir = os.path.join(root, subdir_name)
            if os.path.exists(subdir):
                if not os.path.isdir(subdir):
                    os.remove(subdir)
                    os.makedirs(subdir)
            else:
                os.makedirs(subdir)

        sftp.Handler.root = root
