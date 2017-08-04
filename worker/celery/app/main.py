import os, sys, subprocess
from celery import Celery
import tasks


username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
host = os.getenv('HOST')
port = os.getenv('RABBITMQ_PORT')

if username is None or password is None:
    print("USERNAME and PASSWORD need to be provided as environment variables.")
    sys.exit()
if host is None:
    print("HOST needs to be provided as environment variables.")
    sys.exit()
if port is None:
    print("RABBITMQ_PORT needs to be provided as environment variables.")
    sys.exit()

app = Celery(broker='amqp://{username}:{password}@{host}:{port}/zimfarm'
             .format(username=username, password=password, host=host, port=port))
app.register_task(tasks.MWOffliner())

if __name__ == "__main__":
    # add docker socket read / write permission to other
    subprocess.run(['chmod', 'o+rw', '/var/run/docker.sock'])

    # start celery worker
    argv = ['celery', 'worker', '--uid', 'zimfarm_worker', '-l', 'info', '--concurrency', '2']
    app.start(argv=argv)
