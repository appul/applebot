import asyncio


def call_co(co, *args, **kwargs):
    """Call a coroutine as a function. Not thread safe!"""
    if asyncio.iscoroutinefunction(co):
        return call_co(co(*args, **kwargs))
    return asyncio.new_event_loop().run_until_complete(co)
