import logging
import os
import sys
from pathlib import Path
from paramiko import RSAKey, SSHException


class Settings:
    username: str = os.getenv('USERNAME', None)
    password: str = os.getenv('PASSWORD', None)

    dispatcher_hostname: str = os.getenv('DISPATCHER_HOST', 'farm.openzim.org')
    rabbit_port: int = os.getenv('RABBIT_PORT', 5671)
    warehouse_hostname: str = os.getenv('WAREHOUSE_HOST', 'farm.openzim.org')
    warehouse_port: int = os.getenv('WAREHOUSE_PORT', 1522)

    working_dir_host: str = os.getenv('WORKING_DIR', None)
    working_dir_container: str = '/zim_files'
    private_key: str = '/usr/src/.ssh/id_rsa'
    redis_name: str = os.getenv('REDIS_NAME', 'zimfarm_redis')

    docker_socket: str = '/var/run/docker.sock'

    @classmethod
    def sanity_check(cls):
        logger = logging.getLogger(__name__)

        # check mandatory env variables exist
        if cls.username is None or cls.username == '':
            logger.error('{} environmental variable is required.'.format('USERNAME'))
            sys.exit(1)
        if cls.password is None or cls.password == '':
            logger.error('{} environmental variable is required.'.format('PASSWORD'))
            sys.exit(1)
        if cls.working_dir_host is None or cls.working_dir_host == '':
            logger.error('{} environmental variable is required.'.format('WORKING_DIR'))
            sys.exit(1)

        # check working directory mapping inside container
        working_dir_container = Path(cls.working_dir_container)
        if not working_dir_container.exists():
            logger.error('Working directory mapping did not found inside container at {}.'
                         .format(cls.working_dir_container))
            sys.exit(1)
        if not working_dir_container.is_dir():
            logger.error('Working directory mapping inside container at {} is not a directory.'
                         .format(cls.working_dir_container))
            sys.exit(1)

        # check RSA private key mapping inside container
        private_key = Path(cls.private_key)
        if not private_key.exists():
            logger.error('Private key mapping did not found inside container at {}.'.format(cls.private_key))
            sys.exit(1)
        if not private_key.is_file():
            logger.error('Private key mapping at {} is not a file.'.format(cls.private_key))
            sys.exit(1)
        try:
            RSAKey.from_private_key_file(cls.private_key)
        except SSHException:
            logger.error('Private key mapping at {} is not a valid RSA key.'.format(cls.private_key))
            sys.exit(1)

        # check docker socket mapping inside container
        docker_socket = Path(cls.docker_socket)
        if not docker_socket.exists():
            logger.error('Docker socket mapping did not found inside container at {}.'.format(cls.private_key))
            sys.exit(1)

    @classmethod
    def ensure_correct_typing(cls):
        logger = logging.getLogger(__name__)
        try:
            cls.rabbit_port = int(cls.rabbit_port)
        except ValueError:
            logger.error('{} environmental variable is not an integer.'.format('RABBIT_PORT'))
            sys.exit(1)
        try:
            cls.warehouse_port = int(cls.warehouse_port)
        except ValueError:
            logger.error('{} environmental variable is not an integer.'.format('WAREHOUSE_PORT'))
            sys.exit(1)

    @classmethod
    def log(cls):
        logger = logging.getLogger(__name__)
        variables = {
            'USERNAME': cls.username,
            'DISPATCHER_HOST': cls.dispatcher_hostname,
            'RABBIT_PORT': cls.rabbit_port,
            'WAREHOUSE_HOST': cls.warehouse_hostname,
            'WAREHOUSE_PORT': cls.warehouse_port,
            'WORKING_DIR': cls.working_dir_host
        }

        for name, value in variables.items():
            logger.info('ENV {name} -- {value}'.format(name=name, value=value))
