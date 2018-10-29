import logging
import os

from warehouse import Warehouse


# def signal_handler(number: int, stack_frame):
#     """Close paramiko threads when receiving SIGINT
#
#     :param number: the signal number, like signal.SIGINT
#     :param stack_frame:
#     :return:
#     """
#     for thread in threading.enumerate():
#         if isinstance(thread, paramiko.Transport):
#             thread.close()
#     sys.exit(0)


if __name__ == '__main__':
    # setting up logging
    log_path = os.getenv('LOG_PATH', '/warehouse.log')
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(log_path, mode='w')])
    # start zimfarm warehouse
    warehouse = Warehouse()
    warehouse.start()

    # signal.signal(signal.SIGINT, signal_handler)
