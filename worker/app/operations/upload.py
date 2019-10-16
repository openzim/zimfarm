import os
import re
import lzma
import logging
from pathlib import Path

import docker

from .base import Operation, UploadError
from utils.settings import Settings

MAX_UPLOAD_LOG_LINES = 10 ** 6
logger = logging.getLogger(__name__)


class Upload(Operation):
    def __init__(self, remote_working_dir: str, files: [Path], delete: bool = False):
        """Initializer for upload operation

        :param remote_working_dir: path in warehouse to upload files
        :param files: list of paths to upload
        :param delete: whether to delete source file after upload
        """

        super().__init__()

        if not re.match(r'^/(zim|logs)/.*$', remote_working_dir):
            raise ValueError("can't upload elsewhere than /zim/ or /logs/")

        self.remote_working_dir = remote_working_dir
        self.files = files
        self.delete = delete
        self.image_name = 'openzim/uploader'

    def get_private_key_host_path(self):
        """ private key path on host by inspecting current container """
        container_id = os.getenv("HOSTNAME", "zimfarm_worker")
        api_client = docker.APIClient(base_url=f'unix://{Settings.docker_socket}')
        try:
            for mount in api_client.inspect_container(container_id)["Mounts"]:
                if mount["Destination"] == str(Settings.private_key):
                    return mount["Source"]
        except Exception as exc:
            logger.exception(exc)
            raise ValueError("unable to find RSA private key path on host")

    def execute(self):
        docker_client = docker.from_env()
        docker_client.images.pull(self.image_name)

        working_dir_host = Path(Settings.working_dir_host)
        working_dir_container = Path(Settings.working_dir_container)
        working_dir_target = Path("/output")  # working-dir mount point in target
        private_key = self.get_private_key_host_path()  # private key path on host

        # mount working-dir and private key to uploader
        volumes = {working_dir_host: {'bind': str(working_dir_target), 'mode': 'rw'},
                   private_key: {'bind': '/etc/ssh/keys/id_rsa', 'mode': 'ro'}}
        # prepare non-file-specific uploader args
        base_args = ['uploader', '--username', Settings.username,
                     '--upload-uri', f'sftp://{Settings.warehouse_hostname}:{Settings.warehouse_port}/{self.remote_working_dir}/']
        if self.delete:
            base_args += ["--delete"]

        for file in self.files:
            if file.is_dir():
                continue

            if working_dir_container not in file.parents:
                raise ValueError(f"can't upload file from outside host volume: {file}")

            # replace local path (mounted volume) to target (in uploader mounted volume)
            target_path = re.sub(
                r"^({working_dir})".format(working_dir=working_dir_container),
                str(working_dir_target),
                str(file), 1)
            # add file path to uploader args
            args = base_args + ['--file', target_path]

            logger.debug(args)

            try:
                container_log = docker_client.containers.run(
                    image=self.image_name, remove=True,
                    command=args, volumes=volumes)
            except docker.errors.ContainerError as exc:
                try:
                    logger.error(container_log)
                except Exception:
                    pass
                raise UploadError(code=exc.exit_status,
                                  msg=f'failed to upload {file.name}. uploader exited with `{exc.exit_status}`')
            except (docker.errors.APIError, docker.errors.ImageNotFound) as exc:
                logger.exception(exc)
                raise UploadError(code='docker',
                                  msg=f'Docker error while uploading: {exc}')
            else:
                logger.info(f'successfuly uploaded {file.name}')

    @staticmethod
    def upload_files(remote_working_dir: str, files: list = None, delete: bool = False):
        """upload either a list of files (Path) or all files of a directory (Path)"""

        stats = [{'name': file.name, 'size': file.stat().st_size} for file in files]
        files_desc = ','.join([f'{stat["name"]} - {stat["size"]}' for stat in stats])
        logger.info(f'Uploading files, {files_desc}')

        upload = Upload(remote_working_dir=remote_working_dir, files=files)
        upload.execute()

        return stats

    @staticmethod
    def upload_directory_content(remote_working_dir: str, directory: Path = None, delete: bool = False):
        """upload either a list of files (Path) or all files of a directory (Path)"""

        files = [file for file in directory.iterdir() if not file.is_dir()]

        return Upload.upload_files(remote_working_dir=remote_working_dir, files=files, delete=delete)

    @staticmethod
    def upload_log(container):
        """fetch, compress and upload the container's stdout to the warehouse"""

        # compress log output (using a 1M lines buffer to prevent swap)
        archive = Path(Settings.working_dir_container).joinpath(
            container.name + '.log.xz')
        with lzma.open(archive, 'wb') as f:
            buff, count = (b'', 0)
            for line in container.logs(stdout=True, stderr=True, stream=True):
                buff += line
                count += 1
                if count > MAX_UPLOAD_LOG_LINES:
                    f.write(buff)
                    buff, count = (b'', 0)
            f.write(buff)

        # upload compressed file
        return Upload.upload_files('/logs/', files=[archive], delete=True)[-1]
