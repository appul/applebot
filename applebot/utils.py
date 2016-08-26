import asyncio
import inspect

import aiohttp


def call_co(co, *args, **kwargs):
    """Call a coroutine as a function. Not thread safe!"""
    if asyncio.iscoroutinefunction(co):
        return call_co(co(*args, **kwargs))
    return asyncio.new_event_loop().run_until_complete(co)


def caller_attr(attr, default=None, levels=2):
    """Get an attribute from the class instance of the caller method"""
    caller = inspect.currentframe()
    for l in range(levels):
        caller = caller.f_back
    caller = caller.f_locals.get('self')
    if caller:
        return caller.__dict__.get(attr, default)
    return default


def table_align(lines, alignment=None):
    adjusts = {'r': str.rjust, 'l': str.ljust}
    alignment = iter(alignment)
    cols = transpose_list(lines)

    for i, col in enumerate(cols):
        adjust = adjusts[next(alignment, 'l')]
        width = max(map(len, col))
        cols[i] = [adjust(s, width) for s in col]

    return transpose_list(cols)


def transpose_list(matrix):
    return list(zip(*matrix))


async def get_request(*args, session=None, **kwargs):
    session = session or aiohttp.ClientSession()
    async with session.get(*args, **kwargs) as response:
        response.body = await response.text()
        return response
