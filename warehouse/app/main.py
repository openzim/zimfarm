import logging
import os
import sys

from warehouse import Warehouse

if __name__ == "__main__":
    # setting up logging
    log_path = os.getenv("LOG_PATH", "/warehouse.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, mode="w")],
    )
    # start zimfarm warehouse
    try:
        warehouse = Warehouse()
        warehouse.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
