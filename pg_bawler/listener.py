#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import aiopg
import asyncio
import logging
import argparse
import importlib


LOGGER = logging.getLogger('pg_bawler.listener')

_cli_description = """\
Listen on given channel for notification.

    $ python -m pg_bawler.listener mychannel

If you installed notification trigger with ``pg_bawler.gen_sql`` then
channel is the same as ``tablename`` argument.
"""
__doc__ = _cli_description


class DefaultHandler:

    def __init__(self):
        self.count = 0

    async def handle_notification(self, notification):
        self.count += 1
        LOGGER.info(
            'Reveived notification #%s pid %s from channel %s: %s',
            self.count, notification.pid,
            notification.channel, notification.payload)


async def listen(connection, channel, handler):
    async with connection.cursor() as cursor:
        await cursor.execute('LISTEN {channel}'.format(channel=channel))
        while True:
            notification = await connection.notifies.get()
            LOGGER.debug(
                'Received notification from channel %s: %s',
                channel, notification.payload)
            await handler(notification)


async def listen_forever(channel, handle_fn, connection_kwargs):
    async with aiopg.create_pool(**connection_kwargs) as pg_pool:
        async with pg_pool.acquire() as connection:
            listener = listen(connection, channel, handle_fn)
            await asyncio.gather(listener)


def get_default_cli_args_parser():
    parser = argparse.ArgumentParser(
        description=_cli_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--dsn',
        metavar='DSN',
        help='Connection string. e.g. `dbname=test user=postgres`')
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


default_handler = DefaultHandler().handle_notification


def main():
    args = get_default_cli_args_parser().parse_args()
    logging.basicConfig(
        format='[%(asctime)s][%(name)s][%(levelname)s]: %(message)s',
        level=logging.DEBUG)
    LOGGER.info('Starting pg_bawler listener for channel: %s', args.channel)
    module_name, callable_name = args.handler.split(':')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        listen_forever(
            args.channel,
            getattr(importlib.import_module(module_name), callable_name),
            {'dsn': args.dsn}))


if __name__ == "__main__":
    sys.exit(main())
