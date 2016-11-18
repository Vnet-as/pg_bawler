'''
==============
pg_bawler.core
==============

Base classes for LISTEN / NOTIFY.


Postgresql documentation for
`LISTEN <https://www.postgresql.org/docs/current/static/sql-listen.html>`_ /
`NOTIFY <https://www.postgresql.org/docs/current/static/sql-notify.html>`_.
'''
import asyncio
import logging

import aiopg

LOGGER = logging.getLogger(name='pg_bawler.core')


class PgBawlerException(Exception):
    '''
    Base class for all ``pg_bawler`` related failures
    '''


def cache_async_def(func):
    cache_attr_name = '_cache_async_def_{func.__name__}'.format(func=func)
    async def _cache_method(self, *args, **kwargs):
        if not hasattr(self, cache_attr_name):
            setattr(self, cache_attr_name, await func(self, *args, **kwargs))
        return getattr(self, cache_attr_name)
    # simulate functools.update_wrapper
    _cache_method.__name__ = func.__name__
    _cache_method.__doc__ = func.__doc__
    _cache_method.__module__ = func.__module__
    # save cache_attr_name on function
    # so delattr(self, func.cache_attr_name) will clear the cache
    _cache_method.cache_attr_name = cache_attr_name
    return _cache_method


class BawlerBase:
    '''
    Base ``pg_bawler`` class with convenience methods around ``aiopg``.
    '''

    def __init__(self, connection_params, *, loop=None):
        self.connection_params = connection_params
        self._connection = None
        self.loop = asyncio.get_event_loop() if loop is None else loop

    @cache_async_def
    async def pg_pool(self):
        return await aiopg.create_pool(
            loop=self.loop, **self.connection_params)

    @cache_async_def
    async def pg_connection(self):
        return await (await self.pg_pool()).acquire()

    async def drop_connection(self):
        '''
        Drops current connection

        Next call to the ``self.pg_connection`` will acquire new connection
        from pool. Use this method to drop dead connections on server restart.
        '''
        if hasattr(self, self.pg_connection.cache_attr_name):
            pg_conn = (await self.pg_connection())
            pg_conn.close()
            await (await self.pg_pool()).release(pg_conn)
            # clear cached connection property (cache_async_def)
            delattr(self, self.pg_connection.cache_attr_name)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.drop_connection()
