from flask import request, Response
from .. import errors


def oauth2():
    if request.is_json:
        grant_type = request.json.get('grant_type')
    elif request.mimetype == 'application/x-www-form-urlencoded':
        grant_type = request.form.get('grant_type')
    else:
        grant_type = request.headers.get('grant_type')

    if grant_type == 'password':
        pass
    elif grant_type == 'token':
        pass
    else:
        raise errors.oauth.UnsupportedGrantType('{} is not a supported grant type'.format(grant_type))

    return Response()


def password_grant(username: str, password: str):
    pass


def token_grant():
    pass