import os, sys, pathlib, subprocess
from celery import Celery
import tasks


class FatalError(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


class EnvironmentVariableCheckError(Exception):
    def __init__(self, name=None):
        self.name = name

    def __str__(self):
        return 'Error: {} environment variable must be set.'.format(self.name)


if __name__ == "__main__":
    try:
        # add docker socket read / write permission to other
        docker_socket_path = '/var/run/docker.sock'
        if not pathlib.Path(docker_socket_path).exists():
            raise FatalError("Error: cannot find docker socket at '/var/run/docker.sock', "
                             "perhaps you have forgot to map it when you run the container?")
        subprocess.run(['chmod', 'o+rw', '/var/run/docker.sock'])

        # read env variables
        username = os.getenv('USERNAME')
        password = os.getenv('PASSWORD')
        dispatcher_host = os.getenv('DISPATCHER_HOST')
        warehouse_host = os.getenv('WAREHOUSE_HOST')
        rabbit_port = os.getenv('RABBITMQ_PORT')
        warehouse_command_port = os.getenv('WAREHOUSE_COMMAND_PORT')
        host_working_dir = os.getenv('HOST_WORKING_DIR')
        container_working_dir = os.getenv('CONTAINER_WORKING_DIR')

        # check mandatory env variables is set
        if username is None or len(username) == 0:
            raise EnvironmentVariableCheckError("USERNAME")
        if password is None or len(password) == 0:
            raise EnvironmentVariableCheckError("PASSWORD")
        if dispatcher_host is None:
            raise EnvironmentVariableCheckError("DISPATCHER_HOST")
        if warehouse_host is None:
            raise EnvironmentVariableCheckError("WAREHOUSE_HOST")
        if rabbit_port is None:
            raise EnvironmentVariableCheckError("RABBITMQ_PORT")
        if warehouse_command_port is None:
            raise EnvironmentVariableCheckError("WAREHOUSE_COMMAND_PORT")
        if host_working_dir is None:
            raise EnvironmentVariableCheckError("HOST_WORKING_DIR")
        if container_working_dir is None:
            raise EnvironmentVariableCheckError("CONTAINER_WORKING_DIR")

        # configure celery instance
        app = Celery(main='zimfarm', broker='amqp://{username}:{password}@{host}:{port}/zimfarm'
                     .format(username=username, password=password, host=dispatcher_host, port=rabbit_port))
        app.register_task(tasks.MWOffliner())

        # start celery worker
        app.start(argv=['celery', 'worker',
                        '--task-events',
                        '--uid', 'zimfarm_worker',
                        '-l', 'info',
                        '--concurrency', os.getenv('CONCURRENCY', '2')])
    except FatalError as e:
        sys.exit(e)
    except EnvironmentVariableCheckError as e:
        sys.exit(e)
