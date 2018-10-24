import logging
import os
import signal
import socket
import sys
import threading

import paramiko

from thread import Thread


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


if __name__ == '__main__':
    logging.basicConfig(filename='warehouse.log', filemode='w', level=logging.INFO)
    logging.info('Welcome to Zimfarm warehouse')
    #
    #
    # host_key = os.getenv('host_key')
    # if host_key is None:
    #     logger.error('Fatal errorCannot find environment variable host_key.')
    #
    #
    #
    # host_key = "/Users/chrisli/.ssh/id_rsa"
    # host_key = paramiko.RSAKey(filename=host_key)
    #
    # signal.signal(signal.SIGINT, signal_handler)
    # # signal.signal(signal.SIGTERM, signal_handler)
    #
    # sock = bind_socket(2200)
    # sock.listen(10)
    #
    # while True:
    #     try:
    #         client, address = sock.accept()
    #         print('Received incoming connection from {}:{}'.format(address[0], address[1]))
    #         thread = Thread(host_key, client)
    #         thread.start()
    #     except Exception as e:
    #         print("*** Listen/accept failed: " + str(e))
    #         sys.exit(1)
