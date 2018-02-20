from celery.events import EventReceiver
from kombu import Connection

if __name__ == '__main__':
    url = 'amqp://{username}:{password}@{host}:{port}/zimfarm'.format(username='admin', password='admin_passes', host='farm.openzim.org', port=28001)

    def on_event(event):
        print("EVENT HAPPENED: ", event, flush=True)

    with Connection(url) as connection:
        receiver = EventReceiver(connection, handlers={
            'task-failed' : on_event,
            'task-succeeded' : on_event,
            'task-sent' : on_event,
            'task-received' : on_event,
            'task-revoked' : on_event,
            'task-started' : on_event,
        })
        receiver.capture(limit=None, timeout=None)