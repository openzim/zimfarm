import json
from flask import Response


class JSONResponse(Response):
    default_mimetype = 'application/json'

    def __init__(self, response, **kwargs):
        if isinstance(response, dict) or isinstance(response, list):
            response = json.dumps(response)
        super().__init__(response, **kwargs)


class MissingURLParameterResponse(JSONResponse):
    def __init__(self, param_name: str):
        response = {'error': 'Required parameter {} not provided'.format(param_name)}
        super().__init__(response, status=400)