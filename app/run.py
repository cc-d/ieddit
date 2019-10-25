from sys import argv
from ieddit import app
from utilities.error_decorator import exception_log


# Logging Initialization
import logging 
from utilities.log_utils import logger_init
logger = logging.getLogger(__name__)

@exception_log(logger)
def main(port=80):
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    try:
        logger.info("Attempting to run on custom port")
        port = int(argv[1])
        main(port)
    except:
        logger.warning("Unable to start on custom port. Using port 80")
        main()


