#!/usr/bin/env python
'''
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

import pg_bawler.core


LOGGER = logging.getLogger('pg_bawler.listener')


class DefaultHandler:

    def __init__(self):
        self.count = 0

    async def handle_notification(self, notification):
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


def resolve_handler(handler_str):
    module_name, callable_name = handler_str.split(':')
    return getattr(importlib.import_module(module_name), callable_name)


default_handler = DefaultHandler().handle_notification


class NotificationListener(
    pg_bawler.core.BawlerBase,
    pg_bawler.core.ListenerMixin
):
    pass


def main():
    args = get_default_cli_args_parser().parse_args()
    logging.basicConfig(
        format='[%(asctime)s][%(name)s][%(levelname)s]: %(message)s',
        level=logging.DEBUG)
    LOGGER.info('Starting pg_bawler listener for channel: %s', args.channel)
    loop = asyncio.get_event_loop()
    listener = NotificationListener(connection_params={'dsn': args.dsn})
    listener.listen_timeout = 5
    listener.register_handler(resolve_handler(args.handler))
    loop.run_until_complete(listener.register_channel(args.channel))
    loop.run_until_complete(listener.listen())


if __name__ == '__main__':
    sys.exit(main())
