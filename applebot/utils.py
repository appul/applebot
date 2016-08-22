import asyncio
import inspect


def call_co(co, *args, **kwargs):
    """Call a coroutine as a function. Not thread safe!"""
    if asyncio.iscoroutinefunction(co):
        return call_co(co(*args, **kwargs))
    return asyncio.new_event_loop().run_until_complete(co)


def caller_attr(attr, default=None):
    """Get an attribute from the class instance of the caller method"""
    caller = inspect.currentframe().f_back.f_back.f_locals.get('self')
    if caller:
        return caller.__dict__.get(attr, default)
    return default
