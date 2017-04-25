import subprocess
from flask import request
from celery import Task
from . import flask, celery, get_db
from .response import JSONResponse, MissingURLParameterResponse


class ShellScriptExecTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery.task(bind=True, base=ShellScriptExecTask, track_started=True)
def execute(self):
    subprocess.run(["sleep", "20"], stdout=subprocess.PIPE)


@flask.route('/task/enqueue', methods=['POST'])
def enqueue():
    template_id = request.args.get('template_id')
    if template_id is None:
        return MissingURLParameterResponse('template_id')
    else:
        db = get_db()
        template = db.get_template(template_id)
        if template is None:
            return JSONResponse({
                'error': 'Task is not enqueued, because template with id {} does not exist.'.format(template_id)
            }, status=400)
        else:
            task = execute.apply_async(args=[])
            return JSONResponse({
                'task': {
                    'id': task.id,
                    'status': task.status
                },
                'template': template,
            })


@flask.route('/task/status', methods=['GET'])
def status():
    task_id = request.args.get('task_id')
    if task_id is None:
        return MissingURLParameterResponse('task_id')
    else:
        task = execute.AsyncResult(task_id)
        return JSONResponse({
            'task': {
                'id': task.id,
                'status': task.status
            }
        })
