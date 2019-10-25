import functools
def exception_log(logger):
    """
    Decorator for logging exceptions as they occur. 
    @param logger: The logging obj
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                err = "Exception from:  "
                err += func.__name__
                logger.exception(err)
                # re-raise the exception
                raise
        return wrapper
    return decorator