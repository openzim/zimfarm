from celery import Celery
import tasks


app = Celery('worker', broker='amqp://worker01:worker_pass@zimfarm.chrisshwli.com:7285/zimfarm')
app.register_task(tasks.Generic())
app.register_task(tasks.MWOffliner())


if __name__ == "__main__":
    app.start(argv=['celery', 'worker', '-l', 'info', '--uid', 'zimfarm_worker'])
