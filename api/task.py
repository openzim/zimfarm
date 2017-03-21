from flask import request, Response

def enqueue():
    return Response('{"message": "under construction"}', mimetype='application/json')