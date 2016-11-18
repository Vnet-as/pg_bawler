#!/usr/bin/env python
'''
==================
pg_bawler.listener
==================

Listen on given channel for notification.

    $ python -m pg_bawler.listener mychannel

If you installed notification trigger with ``pg_bawler.gen_sql`` then
channel is the same as ``tablename`` argument.
'''
import argparse
import asyncio
import importlib
import logging
import sys

import psycopg2

import pg_bawler.core


LOGGER = logging.getLogger('pg_bawler.listener')


class ListenerMixin:

    CHANNEL_REGISTRATION_TPL = 'LISTEN {channel}'
    listen_timeout = None
    stop_on_timeout = False
    try_to_reconnect = True
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

    async def _re_register_all_channels(self):
        for channel in self.registered_channels:
            await self.register_channel(channel)

    async def register_channel(self, channel):
        '''
        Register ``channel`` by executing the `LISTEN` statement.

        :param channel: Name of the channel
        :returns: None
        '''
        async with (await self.pg_connection()).cursor() as cursor:
            await cursor.execute(self._get_listen_statement(channel))
        self.registered_channels.setdefault(channel, [])

    async def timeout_callback(self):
        LOGGER.debug(
            'Timed out. No notification for last %s seconds.',
            self.listen_timeout)
        if self.stop_on_timeout:
            await self.stop()
        else:
            LOGGER.debug(
                'Checking health of connection.')
            try:
                async with (await self.pg_connection()).cursor() as pg_cursor:
                    await pg_cursor.execute('SELECT 1')
                    await pg_cursor.fetchone() == (1, )
            except (
                psycopg2.OperationalError,
                psycopg2.InterfaceError,
            ):
                LOGGER.error('Failed postgres connection!')
                if self.try_to_reconnect:
                    LOGGER.info(
                        'Dropping this connection and creating new one.')
                    await self.drop_connection()
                    await self._re_register_all_channels()
                else:
                    await self.stop()
            else:
                LOGGER.debug('Connection seems to be OK.')

    async def get_notification(self):
        try:
            notification = await asyncio.wait_for(
                (await self.pg_connection()).notifies.get(),
                self.listen_timeout,
                loop=self.loop,
            )
        except asyncio.TimeoutError:
            await self.timeout_callback()
            return None
        except psycopg2.InterfaceError:
            if self.try_to_reconnect:
                await self.drop_connection()
                await self._re_register_all_channels()
            else:
                await self.stop()
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


class DefaultHandler:

    def __init__(self):
        self.count = 0

    async def handle_notification(self, notification, listener):
        self.count += 1
        notification_number = self.count
        LOGGER.info(
            'Received notification #%s pid %s from channel %s: %s',
            notification_number, notification.pid,
            notification.channel, notification.payload)


def get_default_cli_args_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--stop-on-timeout',
        action='store_true',
        default=False,
        help='Stop listener when timeout passes.')
    parser.add_argument(
        '--log-level',
        metavar='LOG_LEVEL',
        default='INFO',
        help='Log level. One of: FATAL, CIRTICAL, ERROR, WARNING, INFO, DEBUG')
    parser.add_argument(
        '--dsn',
        metavar='DSN',
        required=True,
        help='Connection string. e.g. `dbname=test user=postgres`')
    parser.add_argument(
        '--timeout',
        metavar='TIMEOUT', default=5, type=int,
        help=(
            'Timeout for getting notification.'
            ' If this timeout passes pg_bawler checks'
            ' connection if it\'s alive'))
    parser.add_argument(
        '--handler',
        metavar='HANDLER', default='pg_bawler.listener:default_handler',
        help=(
            'Module and name of python callable.'
            ' e.g. `pg_bawler.listener:default_handler`'))
    parser.add_argument(
        'channel',
        metavar='CHANNEL', type=str,
        help='Name of Notify/Listen channel to listen on.')
    return parser


def resolve_handler(handler_str):
    module_name, callable_name = handler_str.split(':')
    return getattr(importlib.import_module(module_name), callable_name)


default_handler = DefaultHandler().handle_notification


class NotificationListener(pg_bawler.core.BawlerBase, ListenerMixin):
    pass


def _main(
    *,
    loop,
    connection_params,
    channel,
    handler=default_handler,
    timeout=5,
    stop_on_timeout=False,
    listener_class=NotificationListener
):
    listener = NotificationListener(
        connection_params=connection_params,
        loop=loop)
    listener.listen_timeout = timeout
    listener.stop_on_timeout = stop_on_timeout
    listener.register_handler(channel, handler)
    loop.run_until_complete(listener.register_channel(channel))
    return listener, loop.create_task(listener.listen())


def main(*argv, loop=None):
    args = get_default_cli_args_parser().parse_args(argv or sys.argv[1:])
    try:
        logging.basicConfig(
            format='[%(asctime)s][%(name)s][%(levelname)s]: %(message)s',
            level=args.log_level.upper())
    except (TypeError, ValueError):
        sys.exit('Worng log level. --help for more info.')
    LOGGER.info('Starting pg_bawler listener for channel: %s', args.channel)
    loop = loop or asyncio.get_event_loop()
    _, listen_task = _main(
        loop=loop,
        connection_params={'dsn': args.dsn},
        channel=args.channel,
        handler=resolve_handler(args.handler),
        stop_on_timeout=args.stop_on_timeout,
        timeout=args.timeout)
    listen_task.add_done_callback(lambda fut: loop.stop())
    try:
        loop.run_forever()
    finally:
        if loop.is_running():
            loop.stop()
        loop.close()


if __name__ == '__main__':
    sys.exit(main())
