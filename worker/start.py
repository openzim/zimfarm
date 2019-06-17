import sys
from os import getenv

import docker

if __name__ == '__main__':
    client = docker.from_env()

    containers = client.containers.list(all=True, filters={'name': 'zimfarm_worker'})
    print(containers)
    for container in containers:
        container.remove()

    username = getenv('USERNAME', 'automactic')
    password = getenv('PASSWORD', 'macOS10&open')
    host_working_dir = '/Volumes/Data/zimfarm'
    # ssh_pub_key = '/home/automactic/.ssh/id_rsa'
    ssh_pub_key = '/Users/chrisli/.ssh/id_rsa'

    if not username or not password:
        sys.exit(1)

    volumes = {
        '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'},
        ssh_pub_key: {'bind': '/usr/src/.ssh/id_rsa', 'mode': 'ro'},
        host_working_dir: {'bind': '/zim_files', 'mode': 'rw'},
    }

    environment = {
        'USERNAME': username,
        'PASSWORD': password,
        'WORKING_DIR': host_working_dir,
        'NODE_NAME': 'Chris Macbook Pro',
        'QUEUES': 'debug',
        'CONCURRENCY': 2
    }

    # image = client.images.pull('openzim/zimfarm-worker', tag='latest')
    client.containers.run('zimfarm_worker:latest', detach=True, environment=environment, name='zimfarm_worker', volumes=volumes)
