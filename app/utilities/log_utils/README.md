# Logging Utils

These logging utilities create default loggers for all of the files. The configuration is stored on a static config file logger_config.yaml. 

## How Loggers work

Loggers use objects to send logs places. Each module should have its own logger with a name. Data flows like this in the application;

Logger -> QueueListener -> Other handers (FileHandler, Console) 

Each level works with filtering by the Log Levels below:

Level | Numberic Value
----- | --------------
CRITICAL | 50
ERROR | 40
WARNING | 30
INFO | 20
DEBUG | 10
NOTSET | 0

It works from the bottom up. If the logging level that handler/logger will only catch at that level and above. 

## Updating Logging Yaml

### Objects
```yaml
objects:
  queue:
    class: queue.Queue
    maxsize: 1000
```
 
 Objects represent arbitrary python class objects that are needed. Update maxsize if needed.


### Formatters
```yaml
formatters:
  simple:
    format: '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
```

Formatters specify the format that logs should be in. Formatters are childeren of handlers so if a different fomatter is need a seperate handler may be needed. 


### Handlers
```yaml
handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: simple
    stream: ext://sys.stdout
  file:
    class: logging.FileHandler
    level: WARNING
    filename: 'ieddit.log'
    formatter: simple
  queue_listener:
    class: utilities.log_utils.logger_util.QueueListenerHandler
    handlers:
      - cfg://handlers.console
      - cfg://handlers.file
    queue: cfg://objects.queue
```

Handlers define where the logs should go when log statements are hit. Queue handler here defines that after items hit it they should go into console and then file.

1. Stream handler:
    * Sends output to the console. It is set to allow everything debug and higher in priority. 
2. File handler:
    * Sends output to specified file. It is set to allow everything warning and higher in priority. This is to prevent logs from growing too large. 
3. Queue Listener:
    * This is a very special handler. It lives on a seperate thread from the application so log statements do not block the application flow. All loggers should point here. 

### Loggers
```yaml
loggers:
    blueprints.admin:
    level: WARNING
    handlers: 
      - queue_listener
    propagate: false
```

Logger objects are the individual instances of the logging class. Each file should have its own logger defined by its name. Above is what the logger looks like for admin.py which is in the blueprints module. Its data is directed at the queue-listener which then spits the data out to the 2 other handlers. Propogate means do we want this error bubbling up to other loggers, which we do not want. 

## Using Loggers in files

```python
# Admin.py
# Logging Initialization
import logging 
logger = logging.getLogger(__name__)
```

Here the default log level for production is WARNING and above. If we wanted to do different we could manually set the level in a file like so:

```python
# Admin.py
# Logging Initialization
import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

This will override what is set in the config. If you set this to debug however it will only be caught by the console becuase the FileHandler filters anything out below Warning.