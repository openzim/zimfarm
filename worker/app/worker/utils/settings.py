import logging
import os
import sys
from pathlib import Path


class Settings:
    username: str = os.getenv('USERNAME', None)
    password: str = os.getenv('PASSWORD', None)

    dispatcher_hostname: str = os.getenv('DISPATCHER_HOST', 'farm.openzim.org')
    rabbit_port: int = os.getenv('RABBIT_PORT', 5671)
    warehouse_hostname: str = os.getenv('WAREHOUSE_HOST', 'farm.openzim.org')
    warehouse_port: int = os.getenv('WAREHOUSE_PORT', 1522)

    docker_socket_path: Path = Path('/var/run/docker.sock')
    working_dir: Path = Path(os.getenv('WORKING_DIR', ''))
    redis_name: str = os.getenv('REDIS_NAME', 'zimfarm_redis')
    container_inside_files_dir: Path = Path('/files')

    @classmethod
    def sanity_check(cls):
        def log_error_and_exit(name: str):
            logger = logging.getLogger(__name__)
            logger.error('{name} environmental variable is required.'.format(name=name))
            sys.exit(1)

        if cls.username is None or cls.username == '':
            log_error_and_exit('USERNAME')
        if cls.password is None or cls.password == '':
            log_error_and_exit('PASSWORD')

    @classmethod
    def log(cls):
        logger = logging.getLogger(__name__)
        variables = {
            'USERNAME': cls.username,
            'DISPATCHER_HOST': cls.dispatcher_hostname,
            'RABBIT_PORT': cls.rabbit_port,
            'WAREHOUSE_HOST': cls.warehouse_hostname,
            'WAREHOUSE_PORT': cls.warehouse_port
        }

        for name, value in variables.items():
            logger.info('ENV {name} -- {value}'.format(name=name, value=value))
