from sys import argv
from ieddit import app
from utilities.error_decorator import exception_log


# Logging Initialization
import logging
from utilities.log_utils import logger_init
logger = logging.getLogger(__name__)

import config

@exception_log(logger)
def main(port=80):
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    try:
        port = 80
        if len(argv) > 1:
            port = int(argv[1])

        logger.info(f"Attempting to start app on Port: {port}")
        main(port)

    except:
        logger.exception("Unable to start app.")
