import functools
import inspect
import warnings

string_types = (type(b''), type(u''))

# Pulled from SO: https://stackoverflow.com/a/40301488/14578858
# "... This decorator is now part of the Deprecated library"
# See deprecated library license
def deprecated(reason):
    """
    This is a decorator which can be used to mark functions as deprecated. It will result in a warning being emitted
    when the function is used.
    :param reason: Optional reason to give for deprecation
    """

    if isinstance(reason, string_types):

        # The @deprecated is used with a 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated("please, use another function")
        #    def old_function(x, y):
        #      pass

        def decorator(func1):
            @functools.wraps(func1)
            def new_func1(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                warnings.warn(
                    "Call to deprecated %s %s (%s)." % ("class" if inspect.isclass(func1) else "function", func1.__name__, reason),
                    category=DeprecationWarning,
                    stacklevel=2
                )
                warnings.simplefilter('default', DeprecationWarning)
                return func1(*args, **kwargs)
            return new_func1
        return decorator

    elif inspect.isclass(reason) or inspect.isfunction(reason):

        # The @deprecated is used without any 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated
        #    def old_function(x, y):
        #      pass

        func = reason
        @functools.wraps(func)
        def new_func2(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)
            warnings.warn(
                "Call to deprecated %s %s (%s)." % ("class" if inspect.isclass(func) else "function", func.__name__, reason),
                category=DeprecationWarning,
                stacklevel=2
            )
            warnings.simplefilter('default', DeprecationWarning)
            return func(*args, **kwargs)
        return new_func2
    else:
        raise TypeError(repr(type(reason)))