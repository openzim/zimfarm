import os

from paramiko import sftp, SFTPServer, SFTPServerInterface, SFTPAttributes, SFTPHandle


class SFTPHandler(SFTPServerInterface):
    root: str = '/Volumes/Data/ZimFiles'

    def __init__(self, *args, **kwargs):
        print('SFTPServer init')
        super().__init__(*args, **kwargs)

    def canonicalize(self, path):
        if os.path.isabs(path):
            path = self.root + path
        else:
            path = self.root + '/' + path
        return os.path.normpath(path)

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