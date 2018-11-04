import json
import os
import threading
import urllib.request

import paramiko
from paramiko import sftp, SFTPServer, SFTPAttributes, SFTPHandle


class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def get_allowed_auths(self, username: str):
        """Return allowed auth methods

        :param username:
        :return:
        """
        return "publickey"

    def check_auth_publickey(self, username, key: paramiko.PKey):
        url = 'https://farm.openzim.org/api/auth/validate/ssh_key'
        data = {
            'username': username,
            'key': key.get_base64()
        }
        data = json.dumps(data).encode()
        headers = {'content-type': 'application/json'}
        request = urllib.request.Request(url, data, headers, method='POST')
        with urllib.request.urlopen(request) as response:
            if response.code < 300:
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        else:
            return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


class Handler(paramiko.SFTPServerInterface):
    root: str = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def canonicalize(self, path):
        path = super().canonicalize(path)
        if path.startswith(self.root):
            return path
        else:
            return self.root + path

    def chattr(self, path, attr):
        """
        Not allow change attribute of a file.
        """

        return sftp.SFTP_OP_UNSUPPORTED

    def list_folder(self, path):
        """
        List files
        """

        path = self.canonicalize(path)
        if not path.startswith(self.root):
            return sftp.SFTP_PERMISSION_DENIED

        contents = []
        for file_name in os.listdir(path):
            attr = SFTPAttributes.from_stat(os.stat(os.path.join(path, file_name)))
            attr.filename = file_name
            contents.append(attr)
        return contents

    def lstat(self, path):
        """
        Get attribute of a path
        """

        path = self.canonicalize(path)

        if not path.startswith(self.root):
            return sftp.SFTP_PERMISSION_DENIED

        return SFTPAttributes.from_stat(os.stat(path))

    def mkdir(self, path, attr):
        return sftp.SFTP_OP_UNSUPPORTED

    def open(self, path, flags, attr: SFTPAttributes):
        path = self.canonicalize(path)

        if not path.startswith(self.root):
            return sftp.SFTP_PERMISSION_DENIED

        # get a file descriptor
        try:
            if attr.st_mode is None:
                file_descriptor = os.open(path, flags, 0o666)
            else:
                file_descriptor = os.open(path, flags, attr.st_mode)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

        # update file attribute (?)
        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            SFTPServer.set_file_attr(path, attr)

        # set mode
        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                mode = 'ab'
            else:
                mode = 'wb'
        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                mode = 'a+b'
            else:
                mode = 'r+b'
        else:
            # O_RDONLY (== 0)
            mode = 'rb'

        # open file object
        try:
            file = os.fdopen(file_descriptor, mode)
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

        # create sftp handle
        handle = SFTPHandle(flags)
        handle.filename = path
        handle.readfile = file
        handle.writefile = file

        return handle

    def posix_rename(self, oldpath, newpath):
        return sftp.SFTP_OP_UNSUPPORTED

    def readlink(self, path):
        return sftp.SFTP_OP_UNSUPPORTED

    def remove(self, path):
        return sftp.SFTP_OP_UNSUPPORTED

    def rename(self, oldpath, newpath):
        return sftp.SFTP_OP_UNSUPPORTED

    def rmdir(self, path):
        return sftp.SFTP_OP_UNSUPPORTED

    def stat(self, path):
        return self.lstat(path)

    def symlink(self, target_path, path):
        return sftp.SFTP_OP_UNSUPPORTED