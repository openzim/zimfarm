import logging
import os
import sys
from pathlib import Path

from paramiko import RSAKey, SSHException

logger = logging.getLogger(__name__)


class Settings:
    username: str = os.getenv('USERNAME', None)
    password: str = os.getenv('PASSWORD', None)

    node_name: str = os.getenv('NODE_NAME', None)
    queues: str = os.getenv('QUEUES', None)
    concurrency: int = os.getenv('CONCURRENCY', None)

    dispatcher_hostname: str = os.getenv('DISPATCHER_HOST', 'farm.openzim.org')
    rabbit_port: int = os.getenv('RABBIT_PORT', 5671)
    warehouse_hostname: str = os.getenv('WAREHOUSE_HOST', 'farm.openzim.org')
    warehouse_port: int = os.getenv('WAREHOUSE_PORT', 1522)

    working_dir_host: str = os.getenv('WORKING_DIR', None)
    working_dir_container: str = '/zim_files'
    sockets_dir_container: str = '/tmp/sockets'
    private_key: str = '/usr/src/.ssh/id_rsa'

    docker_socket: str = '/var/run/docker.sock'

    @classmethod
    def sanity_check(cls):
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
        if cls.node_name is None or cls.node_name == '' or cls.node_name == 'default_node_name':
            logger.error('{} environmental variable is required.'.format('NODE_NAME'))
            sys.exit(1)
        if cls.queues is None or cls.queues == '':
            logger.error('{} environmental variable is required.'.format('QUEUES'))
            sys.exit(1)

        # check working directory mapping inside container
        working_dir_container = Path(cls.working_dir_container)
        if not working_dir_container.exists():
            logger.error('Working directory mapping not found inside container at {}.'
                         .format(cls.working_dir_container))
            sys.exit(1)
        if not working_dir_container.is_dir():
            logger.error('Working directory mapping inside container at {} is not a directory.'
                         .format(cls.working_dir_container))
            sys.exit(1)

        # check RSA private key mapping inside container
        private_key = Path(cls.private_key)
        if not private_key.exists():
            logger.error('Private key mapping not found inside container at {}.'.format(cls.private_key))
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
            logger.error('Docker socket mapping not found inside container at {}.'.format(cls.docker_socket))
            sys.exit(1)

        # check sockets folder permission (redis is ran as user)
        sockets_dir_from_worker = Path(cls.working_dir_container).joinpath('sockets')
        sockets_dir_host = Path(cls.working_dir_host).joinpath('sockets')
        if not sockets_dir_from_worker.exists() or \
                not oct(sockets_dir_from_worker.stat().st_mode & 0o777) == 0o777:
            logger.info('Sockets directory at {} need to be world writable'
                        .format(sockets_dir_host))
            try:
                sockets_dir_from_worker.mkdir(0o777, parents=True, exist_ok=True)
                sockets_dir_from_worker.chmod(0o777)
            except Exception as e:
                logger.exception(e)
                logger.error('Unable to make sockets directory at {} world writable'
                             .format(sockets_dir_host))
                sys.exit(1)
            else:
                logger.info('Changed sockets directory mode to world writable')

    @classmethod
    def ensure_correct_typing(cls):
        try:
            if cls.concurrency is not None:
                cls.concurrency = int(cls.concurrency)
                if cls.concurrency < 1:
                    logger.error('CONCURRENCY environmental variable cannot be less than one.')
                    sys.exit(1)
        except ValueError:
            logger.error('CONCURRENCY environmental variable is not an integer.')
            sys.exit(1)
        try:
            cls.rabbit_port = int(cls.rabbit_port)
        except ValueError:
            logger.error('RABBIT_PORT environmental variable is not an integer.')
            sys.exit(1)
        try:
            cls.warehouse_port = int(cls.warehouse_port)
        except ValueError:
            logger.error('WAREHOUSE_PORT environmental variable is not an integer.')
            sys.exit(1)

    @classmethod
    def log(cls):
        variables = {
            'USERNAME': cls.username,
            'DISPATCHER_HOST': cls.dispatcher_hostname,
            'RABBIT_PORT': cls.rabbit_port,
            'WAREHOUSE_HOST': cls.warehouse_hostname,
            'WAREHOUSE_PORT': cls.warehouse_port,
            'WORKING_DIR': cls.working_dir_host,
            'NODE_NAME': cls.node_name,
            'QUEUES': cls.queues,
            'CONCURRENCY': cls.concurrency
        }

        for name, value in variables.items():
            logger.info('ENV {name} -- {value}'.format(name=name, value=value))
