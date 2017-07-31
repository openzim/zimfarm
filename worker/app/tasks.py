from celery import Task
from celery.utils.log import get_task_logger
import jwt
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

    def run(self, token: str, params: {}, **kwargs):
        print(kwargs)
        redis_container_name = 'zimfarm-worker-redis'

        def run_redis():
            containers = client.containers.list(filters={'name': redis_container_name})
            if len(containers) == 0:
                client.containers.run('redis', detach=True, name=redis_container_name)

        def assemble_command(params: {}):
            parts: [str] = []
            for key, value in params.items():
                if isinstance(value, bool):
                    parts.append('--{name}'.format(name=key))
                else:
                    parts.append('--{name}={value}'.format(name=key, value=value))
            return 'mwoffliner {}'.format(' '.join(parts))

        try:
            id_prefix = self.request.id.split('-')[0]
            client = docker.from_env()

            # 1/4 run redis
            logger.info('Step {step}/{total} -- start redis'.format(id=id_prefix, step=1, total=4))
            run_redis()

            # 2/4 pull latest image
            logger.info('Step {step}/{total} -- pull openzim/mwoffliner'.format(id=id_prefix, step=2, total=4))
            client.images.pull('openzim/mwoffliner', tag='latest')

            # 3/4 generate zim file
            logger.info('Step {step}/{total} -- generating zim file'.format(id=id_prefix, step=3, total=4))
            params['redis'] = 'redis://redis'
            params['mwUrl'] = 'https://bm.wikipedia.org/'
            params['adminEmail'] = 'chris@kiwix.org'
            params['verbose'] = True
            command = assemble_command(params)
            log = client.containers.run('openzim/mwoffliner', command, name=self.request.id, remove=True,
                                        links={redis_container_name: 'redis'})
            logger.info(command)
            log = log.decode()

            # 4/4 upload zim file
            logger.info('Step {step}/{total} -- uploading zim file'.format(id=id_prefix, step=4, total=4))

        except docker.errors.ContainerError as e:
            logger.error('DOCKER: ContainerError({})'.format(e.stderr))
        except docker.errors.ImageNotFound as e:
            logger.info('DOCKER: ImageNotFound({})'.format(e.explanation))
        except docker.errors.APIError as e:
            logger.info('DOCKER: APIError({})'.format(e.explanation))
