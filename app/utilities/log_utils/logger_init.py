import os

# Get Application Config
import config

# Setup For Logging Init
import yaml
import logging
import utilities.log_utils.logger_util

# Pull in Logging Config
path = os.path.join(os.getcwd(), 'app', 'utilities', 'log_utils', 'logger_config.yaml')
with open(path, 'r') as stream:
    try:
      logging_config = yaml.load(stream, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
      print("Error Loading Logger Config")
      pass

# Load Logging configs
logging.config.dictConfig(logging_config)

# Initialize Log Levels
log_level = logging.WARNING

# Check For Debug Flag
if config.DEBUG:
  log_level = logging.DEBUG

# Set the logging level for all loggers in scope 
# This level can be overwritten by the following in a file
#   logger = logging.getlogger(__name__)
#   logger.setLevel(logging.INFO)
loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for log in loggers:
  log.setLevel(log_level)