import subprocess
from flask import request
from . import flask, celery, get_db
from .response import JSONResponse, MissingURLParameterResponse


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
                'task': task.id,
                'template': template,
            })


@celery.task(bind=True)
def execute(self):
    subprocess.run(["sleep", "10"], stdout=subprocess.PIPE)


@flask.route('/task/status', methods=['POST'])
def status():
    return JSONResponse({
        "message": "under construction"
    })
