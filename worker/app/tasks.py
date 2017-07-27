from celery import Task
from celery.utils.log import get_task_logger
import docker
import docker.errors


logger = get_task_logger(__name__)


class Generic(Task):
    name = 'zimfarm.generic'
    logger = get_task_logger(__name__)

    def run(self, image_name: str, script: str):
        try:
            client = docker.from_env()
            logger.info('DOCKER: running {}'.format(image_name))
            logger.info('DOCKER: command {}'.format(script))
            log = client.containers.run(image_name, script, name=self.request.id)
            logger.info(log.decode())
        except docker.errors.ContainerError as e:
            logger.error('DOCKER: ContainerError({})'.format(e.stderr.decode()))
        except docker.errors.ImageNotFound as e:
            logger.error('DOCKER: ImageNotFound({})'.format(e.explanation))
        except docker.errors.APIError as e:
            logger.error('DOCKER: APIError({})'.format(e.explanation))


class MWOffliner(Task):
    name = 'zimfarm.mwoffliner'

    def run(self):
        def run_redis():
            redis_container_name = 'zimfarm-worker-redis'
            containers = client.containers.list(filters={'name': redis_container_name})
            if len(containers) == 0:
                client.containers.run('redis', detach=True, name=redis_container_name)

        try:
            client = docker.from_env()
            run_redis()
        except docker.errors.ContainerError as e:
            logger.error('DOCKER: ContainerError({})'.format(e.stderr))
        except docker.errors.ImageNotFound as e:
            logger.info('DOCKER: ImageNotFound({})'.format(e.explanation))
        except docker.errors.APIError as e:
            logger.info('DOCKER: APIError({})'.format(e.explanation))
