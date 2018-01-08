import os
import sys
import logging
import urllib.request
from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


class Authorizer(DummyAuthorizer):
    def __init__(self, token_validation_url: str, file_storage_dir: str):
        super().__init__()
        self.token_validation_url = token_validation_url
        self.file_storage_dir = file_storage_dir

    def validate_authentication(self, username, token, handler):
        """
        Upon receiving the authentication request, the ftp server contact zimfarm dispatcher to validate user's token.
        If dispatcher return HTTP 200, the token is valid

        :param username:
        :param token:
        :param handler:
        :raises AuthenticationFailed: if token is not valid or cannot contact zimfarm dispatcher
        """

        headers = {'token': token}
        request = urllib.request.Request(self.token_validation_url, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(request) as response:
                if response.code == 200:
                    return None
        except Exception:
            raise AuthenticationFailed("Authentication failed.")
    
    def get_home_dir(self, username):
        """
        All users share the same home dir path

        :param username:
        :return: home dir path in ftp server file system
        """
        return self.file_storage_dir
    
    def has_user(self, username):
        """
        We assume user always exist, since auth is handled by `validate_authentication`

        :param username:
        :return:
        """
        return True
    
    def has_perm(self, username, perm, path=None):
        """
        User can only access his or her home dir.

        :param username:
        :param perm:
        :param path:
        :return:
        """

        return perm in self.get_perms(username) and self._issubpath(path, '/')
    
    def get_perms(self, username):
        """
        User can only use `STOR` or `STOU` to store a file on the server.
        For all possible values of `perm`, see http://pyftpdlib.readthedocs.io/en/latest/api.html#pyftpdlib.authorizers.DummyAuthorizer.add_user

        :param username:
        :return:
        """
        return "w"

    def get_msg_login(self, username):
        return "Hi, there!"
    
    def get_msg_quit(self, username):
        return "Bye!"


class FatalError(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return 'Error: {}'.format(self.message)


if __name__ == '__main__':
    try:
        ftp_command_port = os.getenv('FTP_COMMAND_PORT', 21)
        if ftp_command_port is None:
            raise FatalError('FTP_COMMAND_PORT needs to be provided as environment variable.')
        else:
            ftp_command_port = int(ftp_command_port)

        ftp_data_port_range = os.getenv('FTP_DATA_PORT_RANGE', '28011-28090')
        if ftp_data_port_range is None:
            raise FatalError('FTP_DATA_PORT_RANGE needs to be provided as environment variable.')
        else:
            parts = ftp_data_port_range.split('-')
            ftp_data_port_range = range(int(parts[0]), int(parts[1]) + 1)

        token_validation_url = os.getenv('TOKEN_VALIDATION_URL')
        if token_validation_url is None:
            raise FatalError('TOKEN_VALIDATION_URL needs to be provided as environment variable.')

        file_storage_dir = os.getenv('FILE_STORAGE_DIR', '/files')

        if os.getenv('DEBUG', False):
            logging.basicConfig(level=logging.DEBUG)

        FTPHandler.banner = "Welcome to Zimfarm Warehouse."
        FTPHandler.authorizer = Authorizer(token_validation_url, file_storage_dir)
        FTPHandler.passive_ports = ftp_data_port_range

        masquerade_address = os.getenv('MASQUERADE_ADDRESS')
        if masquerade_address is not None:
            FTPHandler.masquerade_address = masquerade_address

        server = FTPServer(('0.0.0.0', ftp_command_port), FTPHandler)
        server.max_cons = 256
        server.max_cons_per_ip = 10
        server.serve_forever()
    except FatalError as e:
        sys.exit(e)
