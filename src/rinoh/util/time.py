from functools import wraps
import time


def timed(function):
    """Decorator timing the method call and printing the result to `stdout`"""
    @wraps(function)
    def function_wrapper(obj, *args, **kwargs):
        """Wrapper function printing the time taken by the call to `function`"""
        name = obj.__class__.__name__ + '.' + function.__name__
        start = time.time()
        result = function(obj, *args, **kwargs)
        print('{}: {:.4f} seconds'.format(name, time.time() - start))
        return result
    return function_wrapper
