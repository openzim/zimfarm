import json
import signal
import socket
import sys
import threading
import time
import traceback
import urllib.request

import paramiko

from sftp import SFTPHandler


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


class Thread(threading.Thread):
    def __init__(self, client: socket.socket):
        super().__init__()
        self.client = client
        self.host_key = paramiko.RSAKey(filename="/Users/chrisli/.ssh/id_rsa")

    def run(self):
        try:
            transport = paramiko.Transport(self.client)
            transport.add_server_key(self.host_key)
            transport.set_subsystem_handler("sftp", paramiko.SFTPServer, sftp_si=SFTPHandler)
            transport.start_server(server=Server())
            channel: paramiko.Channel = transport.accept()

            while transport.is_active():
                time.sleep(1)

        except Exception as e:
            print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
            traceback.print_exc()


if __name__ == '__main__':
    def signal_handler(number: int, *args):
        for thread in threading.enumerate():
            if isinstance(thread, paramiko.Transport):
                thread.close()
        sys.exit(0)

    def bind_socket(port: int) -> socket.socket:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", port))
            return sock
        except Exception as e:
            print("Socket binding failed: " + str(e))
            sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    # signal.signal(signal.SIGTERM, signal_handler)

    sock = bind_socket(2200)
    sock.listen(10)

    while True:
        try:
            client, address = sock.accept()
            print('Received incoming connection from {}:{}'.format(address[0], address[1]))
            thread = Thread(client)
            thread.start()
        except Exception as e:
            print("*** Listen/accept failed: " + str(e))
            sys.exit(1)
