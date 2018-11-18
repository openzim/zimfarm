import logging
import os
import sys

from worker import Worker

if __name__ == '__main__':
    # setting up logging
    log_path = os.getenv('LOG_PATH', '/worker.log')
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(log_path, mode='w')])
    logging.getLogger("paramiko").setLevel(logging.WARNING)

    # start zimfarm worker
    try:
        worker = Worker()
        worker.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
