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


class NotificationListener(
    pg_bawler.core.BawlerBase,
    pg_bawler.core.ListenerMixin
):
    pass


def main(*argv):
    args = get_default_cli_args_parser().parse_args(argv or sys.argv[1:])
    try:
        logging.basicConfig(
            format='[%(asctime)s][%(name)s][%(levelname)s]: %(message)s',
            level=args.log_level.upper())
    except TypeError:
        sys.exit('Worng log level. --help for more info.')
    LOGGER.info('Starting pg_bawler listener for channel: %s', args.channel)
    loop = asyncio.get_event_loop()
    listener = NotificationListener(connection_params={'dsn': args.dsn})
    listener.listen_timeout = args.timeout
    listener.register_handler(resolve_handler(args.handler))
    loop.run_until_complete(listener.register_channel(args.channel))
    loop.run_until_complete(listener.listen())


if __name__ == '__main__':
    sys.exit(main())
