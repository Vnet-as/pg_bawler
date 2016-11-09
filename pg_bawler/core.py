'''
==============
pg_bawler.core
==============

Base classes for LISTEN / NOTIFY.  Postgresql documentation for
`LISTEN<https://www.postgresql.org/docs/current/static/sql-listen.html>`_ /
`NOTIFY<https://www.postgresql.org/docs/current/static/sql-notify.html>`_.
'''
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
    '''
    Base ``pg_bawler`` class with convenience methods around ``aiopg``.
    '''

    def __init__(self, *, connection_params, loop=None):
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
        pg_conn = (await self.pg_connection())
        pg_conn.close()
        await (await self.pg_pool()).release(pg_conn)
        # clear cached connection property (cache_async_def)
        delattr(self, self.pg_connection.cache_attr_name)


class SenderMixin:

    NOTIFY_SEND_TPL = 'SELECT pg_notify(\'{channel}\', \'{payload}\')'

    def get_notify_statement(self, *, channel, payload):
        return self.NOTIFY_SEND_TPL.format(channel=channel, payload=payload)

    async def send(self, *, channel, payload):
        async with (await self.pg_connection()).cursor() as pg_cursor:
            await pg_cursor.execute(
                self.get_notify_statement(channel=channel, payload=payload))


class ListenerMixin:

    CHANNEL_REGISTRATION_TPL = 'LISTEN {channel}'
    listen_timeout = None
    stop_on_timeout = False
    _stopped = False

    async def stop(self):
        await self.drop_connection()
        self._stopped = True

    @property
    def is_stopped(self):
        return self._stopped

    @property
    def registered_channels(self):
        prop_name = '_registered_channels'
        if not hasattr(self, prop_name):
            setattr(self, prop_name, {})
        return getattr(self, prop_name)

    def _get_listen_statement(self, channel):
        return self.CHANNEL_REGISTRATION_TPL.format(channel=channel)

    async def register_channel(self, channel):
        '''
        Register ``channel`` by executing the `LISTEN` statement.

        :param channel: Name of the channel
        :returns: None
        '''
        async with (await self.pg_connection()).cursor() as cursor:
            await cursor.execute(self._get_listen_statement(channel))
        self.registered_channels.setdefault(channel, [])

    async def get_notification(self):
        try:
            notification = await asyncio.wait_for(
                (await self.pg_connection()).notifies.get(),
                self.listen_timeout,
                loop=self.loop,
            )
        except asyncio.TimeoutError:
            LOGGER.debug(
                'Timed out. No notification for last %s seconds.',
                self.listen_timeout)
            if self.stop_on_timeout:
                await self.stop()
            else:
                LOGGER.debug(
                    'Checking health of connection.')
                async with (await self.pg_connection()).cursor() as pg_cursor:
                    await pg_cursor.execute('SELECT 1')
                    is_healthy = await pg_cursor.fetchone() == (1, )
                if is_healthy:
                    LOGGER.debug('Connection seems to be OK.')
                else:
                    LOGGER.error('Failed postgres connection!')
                    LOGGER.info(
                        'Dropping this connection and creating new one.')
                    await self.drop_connection()
            return None
        else:
            LOGGER.debug(
                'Received notification from channel %s: %s',
                notification.channel, notification.payload)
            return notification

    def register_handler(self, channel, handler):
        '''
        Registers ``handler`` with given ``channel``

        :param channel: Name of channel
        :param handler: Coroutine that will handle notifications from
            ``channel``
        :returns: None
        '''
        if channel in self.registered_channels:
            self.registered_channels[channel].append(handler)
        else:
            self.registered_channels[channel] = [handler]

    def unregister_handler(self, channel, handler):
        '''
        Unregisters ``handler`` by removing it from handlers list of given
        ``channel``.

        :param channel: Name of channel
        :param handler: Coroutine to unregister from ``channel``
        :returns: None
        '''
        if channel in self.registered_channels:
            try:
                self.registered_channels[channel].remove(handler)
            except ValueError:
                LOGGER.debug('Handler is not registered.')
            else:
                LOGGER.debug('Handler %s unregistered.')
        return None

    async def listen(self):
        while not self.is_stopped:
            notification = await self.get_notification()
            if notification is not None:
                handlers = self.registered_channels[notification.channel]
                for handler in handlers:
                    self.loop.create_task(handler(notification, self))
