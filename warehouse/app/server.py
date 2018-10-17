import json
import threading
import urllib.request

import paramiko


class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def get_allowed_auths(self, username):
        return "publickey"

    def check_auth_publickey(self, username, key: paramiko.PKey):
        url = 'https://farm.openzim.org/api/auth/validate/ssh_key'
        data = {
            'username': username,
            'key': key.get_base64()
        }
        data = json.dumps(data).encode()
        headers = {'content-type': 'application/json'}
        request = urllib.request.Request(url, data, headers, method='POST')
        with urllib.request.urlopen(request) as response:
            if response.code < 300:
                return paramiko.AUTH_SUCCESSFUL
            else:
                return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED if kind == "session" \
            else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED