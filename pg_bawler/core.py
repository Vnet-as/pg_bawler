"""
==============
pg_bawler.core
==============

Base classes for LISTEN / NOTIFY.  Postgresql documentation for
`LISTEN<https://www.postgresql.org/docs/current/static/sql-listen.html>`_ /
`NOTIFY<https://www.postgresql.org/docs/current/static/sql-notify.html>`_.
"""
import asyncio
import logging

import aiopg

LOGGER = logging.getLogger(name='pg_bawler.core')


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
    """
    Base ``pg_bawler`` class with convenience methods around ``aiopg``.
    """

    def __init__(self, *, connection_params, loop=None):
        self.connection_params = connection_params
        self._connection = None
        self.loop = asyncio.get_event_loop() if loop is None else loop

    @cache_async_def
    async def pg_pool(self):
        return await aiopg.create_pool(**self.connection_params)

    @cache_async_def
    async def pg_connection(self):
        return await (await self.pg_pool()).acquire()


class SenderMixin:

    NOTIFY_SEND_TPL = 'SELECT pg_notify(\'{channel}\', \'{payload}\')'

    def get_send_statement(self, *, channel, payload):
        return self.NOTIFY_SEND_TPL.format(channel=channel, payload=payload)

    async def send(self, *, channel, payload):
        async with (await self.pg_connection()).cursor() as pg_cursor:
            await pg_cursor.execute(
                self.get_send_statement(channel=channel, payload=payload))


class ListenerMixin:

    CHANNEL_REGISTRATION_TPL = 'LISTEN {channel}'
    listen_timeout = None
    reset_connection_on_timeout = False
    _stopped = False
    _reset_connection = False

    def stop(self):
        self._stopped = True

    @property
    def is_stopped(self):
        return self._stopped

    def _get_listen_statement(self, channel):
        return self.CHANNEL_REGISTRATION_TPL.format(channel=channel)

    async def register_channel(self, channel):
        async with (await self.pg_connection()).cursor() as cursor:
            await cursor.execute(self._get_listen_statement(channel))

    async def get_notification(self):
        try:
            notification = await asyncio.wait_for(
                (await self.pg_connection()).notifies.get(),
                self.listen_timeout)
        except asyncio.TimeoutError:
            LOGGER.debug(
                'Timed out. No notification for last %s seconds.',
                self.listen_timeout)
            return None
        else:
            LOGGER.debug(
                'Received notification from channel %s: %s',
                notification.channel, notification.payload)
            return notification

    async def listen(self):
        while not self.is_stopped:
            notification = await self.get_notification()
            # If Queue.get() for notifications timed out,
            # we may want to reset connection or just continue
            if notification:
                self.loop.create_task(self.handler(notification))
            else:
                if self.reset_connection_on_timeout:
                    self.reset_connection()
