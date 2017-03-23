import subprocess
from flask import request
from .database import SQLiteDB
from .response import JSONResponse, MissingURLParameterResponse
from . import app


@app.route('/task/enqueue', methods=['POST'])
def enqueue():
    template_id = request.args.get('template_id')
    if template_id is None:
        return MissingURLParameterResponse('template_id')
    else:
        db = SQLiteDB()
        template = db.get_template(template_id)
        if template is None:
            return JSONResponse({
                'error': 'Task is not enqueued, because template with id {} does not exist.'.format(template_id)
            }, status=400)
        else:
            output = subprocess.run(["sleep", "10"], stdout=subprocess.PIPE)
            return JSONResponse({
                'output': str(output.stdout),
                'template': template,
            })


@app.route('/task/status', methods=['POST'])
def status():
    return JSONResponse({
        "message": "under construction"
    })
